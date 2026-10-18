import asyncio
import json
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import cache
from .config import CHANNEL, ERROR_THRESHOLD, ERROR_WINDOW, STATS_KEY, STATS_TTL
from .db import get_db, utcnow
from .models import Event, Incident
from .schemas import EventIn, EventOut, IncidentIn, IncidentOut, IncidentUpdate
from .stream import clear_stats_cache, publish

router = APIRouter()


def event_json(e: Event) -> dict:
    return EventOut.model_validate(e).model_dump(mode="json")


def incident_json(i: Incident) -> dict:
    return IncidentOut.model_validate(i).model_dump(mode="json")


def maybe_open_incident(db: Session, event: Event) -> Incident | None:
    """Count recent errors per source in Redis and open an incident when it spikes."""
    r = cache.get_redis()
    key = f"errors:{event.source}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, ERROR_WINDOW)
    if count < ERROR_THRESHOLD:
        return None

    already_open = db.scalar(
        select(Incident).where(
            Incident.source == event.source,
            Incident.auto_created == 1,
            Incident.status != "resolved",
        )
    )
    if already_open:
        return None

    incident = Incident(
        title=f"Error spike in {event.source}",
        source=event.source,
        severity="critical" if event.level == "critical" else "high",
        auto_created=1,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.post("/events", response_model=EventOut, status_code=201)
def ingest_event(body: EventIn, db: Session = Depends(get_db)):
    event = Event(**body.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)

    publish("event", event_json(event))

    if event.level in ("error", "critical"):
        incident = maybe_open_incident(db, event)
        if incident:
            publish("incident", incident_json(incident))

    clear_stats_cache()
    return event


@router.get("/events", response_model=list[EventOut])
def list_events(
    level: str | None = None,
    source: str | None = None,
    q: str | None = Query(default=None, description="search in message text"),
    before_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(Event).order_by(Event.id.desc()).limit(limit)
    if level:
        query = query.where(Event.level.in_(level.split(",")))
    if source:
        query = query.where(Event.source == source)
    if q:
        query = query.where(Event.message.ilike(f"%{q}%"))
    if before_id:
        query = query.where(Event.id < before_id)
    return db.scalars(query).all()


@router.post("/incidents", response_model=IncidentOut, status_code=201)
def create_incident(body: IncidentIn, db: Session = Depends(get_db)):
    incident = Incident(**body.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    publish("incident", incident_json(incident))
    clear_stats_cache()
    return incident


@router.get("/incidents", response_model=list[IncidentOut])
def list_incidents(
    status: str | None = None,
    severity: str | None = None,
    source: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(Incident).order_by(Incident.id.desc()).limit(limit)
    if status:
        query = query.where(Incident.status.in_(status.split(",")))
    if severity:
        query = query.where(Incident.severity.in_(severity.split(",")))
    if source:
        query = query.where(Incident.source == source)
    return db.scalars(query).all()


@router.get("/incidents/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return incident


@router.patch("/incidents/{incident_id}", response_model=IncidentOut)
def update_incident(incident_id: int, body: IncidentUpdate, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(incident, field, value)

    if changes.get("status") == "resolved":
        incident.resolved_at = utcnow()
    elif "status" in changes:
        incident.resolved_at = None

    db.commit()
    db.refresh(incident)
    publish("incident", incident_json(incident))
    clear_stats_cache()
    return incident


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """Dashboard numbers. Cached in Redis for a few seconds since the UI polls this."""
    r = cache.get_redis()
    cached = r.get(STATS_KEY)
    if cached:
        return json.loads(cached)

    since = utcnow() - timedelta(hours=1)
    by_level = dict(
        db.execute(
            select(Event.level, func.count()).where(Event.created_at >= since).group_by(Event.level)
        ).all()
    )
    by_severity = dict(
        db.execute(
            select(Incident.severity, func.count())
            .where(Incident.status != "resolved")
            .group_by(Incident.severity)
        ).all()
    )
    result = {
        "events_last_hour": sum(by_level.values()),
        "events_by_level": by_level,
        "open_incidents": sum(by_severity.values()),
        "open_by_severity": by_severity,
    }
    r.setex(STATS_KEY, STATS_TTL, json.dumps(result))
    return result


@router.websocket("/ws")
async def live_stream(ws: WebSocket):
    await ws.accept()
    r = cache.get_async_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    # lets the client (and tests) know the subscription is live
    await ws.send_json({"type": "ready"})

    async def forward():
        async for message in pubsub.listen():
            if message["type"] == "message":
                await ws.send_text(message["data"])

    async def watch_client():
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass

    tasks = [asyncio.create_task(forward()), asyncio.create_task(watch_client())]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for t in tasks:
            t.cancel()
        await pubsub.unsubscribe(CHANNEL)
        await pubsub.aclose()
        await r.aclose()
