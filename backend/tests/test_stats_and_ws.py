def test_stats_counts(client):
    client.post("/events", json={"source": "a", "level": "info", "message": "x"})
    client.post("/events", json={"source": "a", "level": "error", "message": "y"})
    client.post("/incidents", json={"title": "t", "severity": "high"})

    stats = client.get("/stats").json()
    assert stats["events_last_hour"] == 2
    assert stats["events_by_level"] == {"info": 1, "error": 1}
    assert stats["open_incidents"] == 1
    assert stats["open_by_severity"] == {"high": 1}


def test_stats_are_cached_then_cleared_by_writes(client):
    client.post("/events", json={"source": "a", "level": "info", "message": "x"})
    assert client.get("/stats").json()["events_last_hour"] == 1

    # a new event invalidates the cache, so the next read sees it
    client.post("/events", json={"source": "a", "level": "info", "message": "y"})
    assert client.get("/stats").json()["events_last_hour"] == 2


def test_websocket_receives_new_events(client):
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json() == {"type": "ready"}
        client.post("/events", json={"source": "api", "level": "warning", "message": "slow"})
        msg = ws.receive_json()

    assert msg["type"] == "event"
    assert msg["data"]["message"] == "slow"
