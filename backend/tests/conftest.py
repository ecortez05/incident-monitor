import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import cache
from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def redis_server():
    return fakeredis.FakeServer()


@pytest.fixture()
def client(redis_server, monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    sync_redis = fakeredis.FakeRedis(server=redis_server, decode_responses=True)
    monkeypatch.setattr(cache, "get_redis", lambda: sync_redis)
    monkeypatch.setattr(
        cache,
        "get_async_redis",
        lambda: fakeredis.FakeAsyncRedis(server=redis_server, decode_responses=True),
    )

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()
