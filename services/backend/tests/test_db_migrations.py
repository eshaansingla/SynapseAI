from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from db import base as db_base
from db.base import Base, init_db
from db.models import Assignment, ConsentEvent, NGO, Task, User, VolunteerProfile


@dataclass
class _AsyncConnWrapper:
    sync_conn: object

    async def run_sync(self, fn):
        return fn(self.sync_conn)

    async def execute(self, statement):
        return self.sync_conn.execute(statement)


class _AsyncBeginWrapper:
    def __init__(self, sync_engine):
        self._sync_engine = sync_engine
        self._ctx = None
        self._conn = None

    async def __aenter__(self):
        self._ctx = self._sync_engine.begin()
        self._conn = self._ctx.__enter__()
        return _AsyncConnWrapper(self._conn)

    async def __aexit__(self, exc_type, exc, tb):
        return self._ctx.__exit__(exc_type, exc, tb)


class _AsyncEngineShim:
    def __init__(self, sync_engine):
        self._sync_engine = sync_engine

    def begin(self):
        return _AsyncBeginWrapper(self._sync_engine)

    async def dispose(self):
        self._sync_engine.dispose()


@pytest.fixture
def sqlite_engine(tmp_path):
    sync_engine = create_engine(f"sqlite:///{tmp_path / 'migrations.db'}", future=True)
    yield sync_engine
    sync_engine.dispose()


async def _patch_engine(monkeypatch, sync_engine) -> None:
    monkeypatch.setattr(db_base, "engine", _AsyncEngineShim(sync_engine))
    monkeypatch.setattr(db_base, "SessionLocal", sessionmaker(sync_engine, expire_on_commit=False))


async def _table_columns(sync_engine, table_name: str) -> dict[str, dict]:
    return {column["name"]: column for column in inspect(sync_engine).get_columns(table_name)}


@pytest.mark.asyncio
async def test_fresh_database_init(sqlite_engine, monkeypatch):
    await _patch_engine(monkeypatch, sqlite_engine)
    await init_db()

    users = await _table_columns(sqlite_engine, "users")
    ngos = await _table_columns(sqlite_engine, "ngos")
    profiles = await _table_columns(sqlite_engine, "volunteer_profiles")
    tasks = await _table_columns(sqlite_engine, "tasks")
    assignments = await _table_columns(sqlite_engine, "assignments")
    consents = await _table_columns(sqlite_engine, "consent_events")

    assert {"id", "email", "password_hash", "preferred_language", "consent_ai_training", "email_verified"}.issubset(users)
    assert {"id", "name", "invite_code", "created_by"}.issubset(ngos)
    assert {"id", "user_id", "profile_completeness_score", "share_location"}.issubset(profiles)
    assert {"id", "ngo_id", "urgency_score", "impact_tags"}.issubset(tasks)
    assert {"id", "task_id", "volunteer_id", "match_score"}.issubset(assignments)
    assert {"id", "user_id", "scope", "granted", "source"}.issubset(consents)


@pytest.mark.asyncio
async def test_idempotent_init(sqlite_engine, monkeypatch):
    await _patch_engine(monkeypatch, sqlite_engine)
    await init_db()
    await init_db()

    users = await _table_columns(sqlite_engine, "users")
    assert users["preferred_language"]["default"] in {"'en'", '"en"', "en"}


@pytest.mark.asyncio
async def test_nullable_defaults(sqlite_engine, monkeypatch):
    await _patch_engine(monkeypatch, sqlite_engine)
    await init_db()

    SessionLocal = sessionmaker(sqlite_engine, expire_on_commit=False)
    with SessionLocal() as session:
        user = User(email="defaults@test.com", password_hash="hash", role="volunteer")
        session.add(user)
        session.flush()
        session.refresh(user)

        assert user.preferred_language == "en"
        assert user.consent_analytics is True
        assert user.consent_personalization is True
        assert user.consent_ai_training is False
        assert user.email_verified is False


@pytest.mark.asyncio
async def test_existing_data_preservation(sqlite_engine, monkeypatch):
    await _patch_engine(monkeypatch, sqlite_engine)
    await init_db()

    SessionLocal = sessionmaker(sqlite_engine, expire_on_commit=False)
    with SessionLocal() as session:
        ngo = NGO(name="Test NGO", description="Demo", invite_code="INV12345", created_by="admin-1")
        session.add(ngo)
        session.flush()

        user = User(email="vol@test.com", password_hash="hash", role="volunteer", ngo_id=ngo.id)
        session.add(user)
        session.flush()

        profile = VolunteerProfile(user_id=user.id, ngo_id=ngo.id, skills=["Teaching"], availability={"mon": True})
        task = Task(ngo_id=ngo.id, title="Community Cleanup", description="Demo", required_skills=["Teaching"])
        session.add_all([profile, task])
        session.flush()

        assignment = Assignment(task_id=task.id, volunteer_id=user.id, ngo_id=ngo.id)
        consent = ConsentEvent(user_id=user.id, scope="ai_training", granted=True, source="signup")
        session.add_all([assignment, consent])
        session.commit()

    await init_db()

    with SessionLocal() as session:
        assert session.execute(select(NGO).where(NGO.id == ngo.id)).scalar_one().name == "Test NGO"
        assert session.execute(select(User).where(User.id == user.id)).scalar_one().email == "vol@test.com"
        assert session.execute(select(Task).where(Task.id == task.id)).scalar_one().title == "Community Cleanup"
        assert session.execute(select(Assignment).where(Assignment.id == assignment.id)).scalar_one().task_id == task.id
        assert session.execute(select(ConsentEvent).where(ConsentEvent.id == consent.id)).scalar_one().scope == "ai_training"