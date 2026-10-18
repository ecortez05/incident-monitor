from app.config import ERROR_THRESHOLD


def make_incident(client, **overrides):
    body = {"title": "DB is down", "severity": "high"}
    body.update(overrides)
    return client.post("/incidents", json=body)


def test_create_and_get(client):
    created = make_incident(client).json()
    assert created["status"] == "open"
    assert client.get(f"/incidents/{created['id']}").json()["title"] == "DB is down"


def test_missing_incident_is_404(client):
    assert client.get("/incidents/999").status_code == 404
    assert client.patch("/incidents/999", json={"status": "resolved"}).status_code == 404


def test_resolving_sets_timestamp_and_reopening_clears_it(client):
    incident = make_incident(client).json()
    resolved = client.patch(f"/incidents/{incident['id']}", json={"status": "resolved"}).json()
    assert resolved["resolved_at"] is not None

    reopened = client.patch(f"/incidents/{incident['id']}", json={"status": "open"}).json()
    assert reopened["resolved_at"] is None


def test_filter_incidents(client):
    make_incident(client, title="a", severity="low")
    b = make_incident(client, title="b", severity="high").json()
    client.patch(f"/incidents/{b['id']}", json={"status": "acknowledged"})

    assert len(client.get("/incidents", params={"severity": "high"}).json()) == 1
    assert len(client.get("/incidents", params={"status": "open"}).json()) == 1
    assert len(client.get("/incidents", params={"status": "open,acknowledged"}).json()) == 2


def test_error_spike_opens_one_incident(client):
    for _ in range(ERROR_THRESHOLD + 3):
        client.post("/events", json={"source": "payments", "level": "error", "message": "boom"})

    incidents = client.get("/incidents", params={"source": "payments"}).json()
    assert len(incidents) == 1
    assert incidents[0]["auto_created"] is True


def test_errors_below_threshold_do_nothing(client):
    for _ in range(ERROR_THRESHOLD - 1):
        client.post("/events", json={"source": "search", "level": "error", "message": "boom"})
    assert client.get("/incidents").json() == []


def test_info_events_never_count_toward_a_spike(client):
    for _ in range(ERROR_THRESHOLD * 2):
        client.post("/events", json={"source": "api", "level": "warning", "message": "slow"})
    assert client.get("/incidents").json() == []
