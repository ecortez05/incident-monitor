def post_event(client, **overrides):
    body = {"source": "api", "level": "info", "message": "hello"}
    body.update(overrides)
    return client.post("/events", json=body)


def test_ingest_and_list(client):
    assert post_event(client).status_code == 201
    post_event(client, message="second")
    events = client.get("/events").json()
    assert [e["message"] for e in events] == ["second", "hello"]


def test_bad_level_rejected(client):
    assert post_event(client, level="loud").status_code == 422


def test_filter_by_level_and_source(client):
    post_event(client, level="error", source="auth")
    post_event(client, level="info", source="auth")
    post_event(client, level="error", source="api")

    assert len(client.get("/events", params={"level": "error"}).json()) == 2
    assert len(client.get("/events", params={"level": "error,info", "source": "auth"}).json()) == 2
    assert len(client.get("/events", params={"source": "api"}).json()) == 1


def test_search_message(client):
    post_event(client, message="Connection refused")
    post_event(client, message="all good")
    found = client.get("/events", params={"q": "refused"}).json()
    assert len(found) == 1


def test_pagination_with_before_id(client):
    for i in range(5):
        post_event(client, message=f"m{i}")
    first = client.get("/events", params={"limit": 2}).json()
    older = client.get("/events", params={"limit": 2, "before_id": first[-1]["id"]}).json()
    assert [e["message"] for e in first] == ["m4", "m3"]
    assert [e["message"] for e in older] == ["m2", "m1"]
