from __future__ import annotations

import argparse
import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta

from dotenv import load_dotenv

from db.base import SessionLocal, engine, init_db
from db.models import Assignment, ConsentEvent, NGO, Task, User, VolunteerProfile
from utils.auth_utils import hash_password

logger = logging.getLogger(__name__)


SECTORS = ["Healthcare", "Education", "Environment", "Community Development"]
SKILLS = ["Teaching", "Coding", "Project Management", "Outreach", "Design"]
LANGUAGES = ["English", "Hindi", "Tamil", "Telugu"]
CAUSES = ["Child Welfare", "Climate Action", "Health", "Literacy", "Disaster Relief"]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"]
ROLES = ["Research", "Outreach", "Administration", "Field Work"]
TASK_STATUSES = ["open", "in_progress", "completed"]
ASSIGNMENT_STATUSES = ["assigned", "accepted", "rejected", "completed"]


def _gen_id() -> str:
    return str(uuid.uuid4())


def _gen_code(length: int = 8) -> str:
    return "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))


async def seed_ngos(session, count: int) -> list[str]:
    admin = User(email="admin@synapse.test", password_hash=hash_password("admin123456"), role="ngo_admin")
    session.add(admin)
    await session.flush()

    ngo_ids: list[str] = []
    for idx in range(count):
        ngo = NGO(
            id=_gen_id(),
            name=f"NGO {idx + 1}",
            description=f"Synthetic organization {idx + 1}",
            sector=random.choice(SECTORS),
            website=f"https://ngo{idx + 1}.example.org",
            headquarters_city=random.choice(CITIES),
            primary_contact_name=f"Contact {idx + 1}",
            primary_contact_phone=f"+91-{random.randint(9000000000, 9999999999)}",
            operating_regions=random.sample(CITIES, k=2),
            mission_focus=random.sample(CAUSES, k=2),
            invite_code=_gen_code(),
            created_by=admin.id,
        )
        session.add(ngo)
        ngo_ids.append(ngo.id)
    await session.flush()
    return ngo_ids


async def seed_users(session, ngo_ids: list[str], count: int) -> tuple[list[str], list[str]]:
    volunteer_ids: list[str] = []
    admin_ids: list[str] = []
    admin_count = max(1, count // 4)
    volunteer_count = max(1, count - admin_count)

    for idx in range(admin_count):
        session.add(
            User(
                id=_gen_id(),
                email=f"admin{idx + 1}@test.org",
                password_hash=hash_password("admin123456"),
                role="ngo_admin",
                ngo_id=random.choice(ngo_ids),
                full_name=f"Admin {idx + 1}",
                phone=f"+91-{random.randint(9000000000, 9999999999)}",
                preferred_language=random.choice(["en", "hi"]),
                consent_analytics=True,
                consent_personalization=True,
                consent_ai_training=True,
            )
        )
        admin_ids.append(admin.id)

    for idx in range(volunteer_count):
        user = User(
            id=_gen_id(),
            email=f"volunteer{idx + 1}@test.org",
            password_hash=hash_password("vol123456"),
            role="volunteer",
            ngo_id=random.choice(ngo_ids),
            full_name=f"Volunteer {idx + 1}",
            phone=f"+91-{random.randint(9000000000, 9999999999)}",
            preferred_language=random.choice(["en", "hi", "ta"]),
            consent_analytics=random.choice([True, True, False]),
            consent_personalization=random.choice([True, True, False]),
            consent_ai_training=random.choice([True, False]),
        )
        session.add(user)
        volunteer_ids.append(user.id)
        user_ids.append(user.id)

    await session.flush()
    return admin_ids, volunteer_ids


async def seed_profiles(session, ngo_ids: list[str], volunteer_ids: list[str]) -> None:
    for user_id in volunteer_ids:
        session.add(
            VolunteerProfile(
                id=_gen_id(),
                user_id=user_id,
                ngo_id=random.choice(ngo_ids),
                skills=random.sample(SKILLS, k=2),
                availability={day: random.choice([True, False]) for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]},
                full_name=f"Profile {user_id[:8]}",
                city=random.choice(CITIES),
                bio="Synthetic volunteer profile",
                education_level=random.choice(["High School", "Bachelor's", "Master's"]),
                years_experience=random.randint(0, 12),
                preferred_roles=random.sample(ROLES, k=2),
                certifications=["First Aid"],
                languages=random.sample(LANGUAGES, k=2),
                causes_supported=random.sample(CAUSES, k=2),
                motivation_statement="Synthetic motivation statement",
                availability_notes="Synthetic availability notes",
                profile_completeness_score=random.uniform(40, 95),
            )
        )
    await session.flush()


async def seed_tasks(session, ngo_ids: list[str], count: int) -> list[str]:
    task_ids: list[str] = []
    for idx in range(count):
        task = Task(
            id=_gen_id(),
            ngo_id=random.choice(ngo_ids),
            title=f"Task {idx + 1}",
            description=f"Synthetic task {idx + 1}",
            required_skills=random.sample(SKILLS, k=2),
            priority=random.choice(["low", "medium", "high"]),
            status=random.choice(TASK_STATUSES),
            deadline=datetime.utcnow() + timedelta(days=random.randint(1, 60)),
            lat=round(random.uniform(-33.0, 28.0), 6),
            lng=round(random.uniform(68.0, 88.0), 6),
            task_category=random.choice(["Field Work", "Administration", "Research"]),
            estimated_hours=random.randint(2, 40),
            urgency_score=random.uniform(20, 95),
            impact_tags=random.sample(["community", "education", "health", "environment"], k=2),
        )
        session.add(task)
        task_ids.append(task.id)
    await session.flush()
    return task_ids


async def seed_assignments(session, ngo_ids: list[str], volunteer_ids: list[str], task_ids: list[str], count: int) -> None:
    for idx in range(count):
        session.add(
            Assignment(
                id=_gen_id(),
                task_id=random.choice(task_ids),
                volunteer_id=random.choice(volunteer_ids),
                ngo_id=random.choice(ngo_ids),
                status=random.choice(ASSIGNMENT_STATUSES),
                assigned_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                accepted_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)) if random.choice([True, False]) else None,
                completed_at=datetime.utcnow() - timedelta(days=random.randint(0, 10)) if random.choice([True, False]) else None,
                hours_spent=random.randint(1, 24),
                completion_rating=random.randint(1, 5) if random.choice([True, False]) else None,
                ngo_feedback="Synthetic feedback" if random.choice([True, False]) else None,
                match_score=random.uniform(30, 98),
            )
        )
    await session.flush()


async def seed_consent_events(session, user_ids: list[str]) -> None:
    scopes = ["analytics", "personalization", "ai_training"]
    for user_id in user_ids:
        for scope in scopes:
            session.add(
                ConsentEvent(
                    id=_gen_id(),
                    user_id=user_id,
                    scope=scope,
                    granted=random.choice([True, True, False]),
                    source="seed",
                )
            )
    await session.flush()


async def main(scale: int, clear: bool) -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    await init_db()
    async with SessionLocal() as session:
        ngo_ids = await seed_ngos(session, max(1, scale))
        admin_ids, volunteer_ids = await seed_users(session, ngo_ids, max(4, scale * 4))
        await seed_profiles(session, ngo_ids, volunteer_ids)
        task_ids = await seed_tasks(session, ngo_ids, max(10, scale * 10))
        await seed_assignments(session, ngo_ids, volunteer_ids, task_ids, max(20, scale * 20))

        await seed_consent_events(session, admin_ids + volunteer_ids)

        await session.commit()

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5, help="Scale factor for generated data")
    parser.add_argument("--clear", action="store_true", help="Reserved for future cleanup flow")
    args = parser.parse_args()
    asyncio.run(main(args.count, args.clear))