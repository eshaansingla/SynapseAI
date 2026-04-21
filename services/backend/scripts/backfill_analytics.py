from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import select, update

from db.base import SessionLocal, engine, init_db
from db.models import Assignment, Task, VolunteerProfile

logger = logging.getLogger(__name__)


def _profile_completeness(profile: VolunteerProfile) -> float:
    scalar_fields = [
        profile.full_name,
        profile.phone,
        profile.city,
        profile.bio,
        profile.date_of_birth,
        profile.emergency_contact_name,
        profile.emergency_contact_phone,
        profile.education_level,
        profile.motivation_statement,
        profile.availability_notes,
    ]
    list_fields = [profile.skills, profile.preferred_roles, profile.certifications, profile.languages, profile.causes_supported]
    filled = sum(1 for value in scalar_fields if value) + sum(1 for value in list_fields if value)
    total = len(scalar_fields) + len(list_fields)
    return round((filled / max(total, 1)) * 100, 1)


def _urgency_score(task: Task) -> float:
    base = {"low": 10.0, "medium": 50.0, "high": 90.0}.get(task.priority, 50.0)
    if task.deadline:
        days = (task.deadline - datetime.utcnow()).days
        if days <= 1:
            base += 10
        elif days <= 3:
            base += 7
        elif days <= 7:
            base += 4
    if task.status == "open":
        base += 5
    return round(min(base, 100.0), 1)


async def _batch_update_profiles(dry_run: bool) -> int:
    async with SessionLocal() as session:
        profiles = (await session.execute(select(VolunteerProfile))).scalars().all()
        for profile in profiles:
            score = _profile_completeness(profile)
            if not dry_run:
                await session.execute(
                    update(VolunteerProfile).where(VolunteerProfile.id == profile.id).values(profile_completeness_score=score)
                )
        if not dry_run:
            await session.commit()
        return len(profiles)


async def _batch_update_tasks(dry_run: bool) -> int:
    async with SessionLocal() as session:
        tasks = (await session.execute(select(Task))).scalars().all()
        for task in tasks:
            score = _urgency_score(task)
            if not dry_run:
                await session.execute(update(Task).where(Task.id == task.id).values(urgency_score=score))
        if not dry_run:
            await session.commit()
        return len(tasks)


async def _batch_update_assignments(dry_run: bool) -> int:
    async with SessionLocal() as session:
        assignments = (await session.execute(select(Assignment))).scalars().all()
        grouped: dict[str, dict[str, int]] = {}
        for assignment in assignments:
            bucket = grouped.setdefault(assignment.volunteer_id, {"assigned": 0, "accepted": 0, "completed": 0})
            bucket["assigned"] += 1
            if assignment.status in {"accepted", "completed"}:
                bucket["accepted"] += 1
            if assignment.status == "completed":
                bucket["completed"] += 1

        profile_rows = (await session.execute(select(VolunteerProfile))).scalars().all()
        for profile in profile_rows:
            stats = grouped.get(profile.user_id, {"assigned": 0, "accepted": 0, "completed": 0})
            assigned = stats["assigned"]
            accepted_rate = round(stats["accepted"] / max(assigned, 1), 4)
            completed_score = round(min(100.0, (stats["completed"] / max(assigned, 1)) * 100), 1)
            if not dry_run:
                await session.execute(
                    update(VolunteerProfile)
                    .where(VolunteerProfile.id == profile.id)
                    .values(
                        total_assigned=assigned,
                        completed_tasks=stats["completed"],
                        acceptance_rate=accepted_rate,
                        performance_score=completed_score,
                    )
                )
        if not dry_run:
            await session.commit()
        return len(assignments)


async def main(dry_run: bool) -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger.info("Starting analytics backfill (%s)", "dry-run" if dry_run else "apply")
    await init_db()
    try:
        profile_count = await _batch_update_profiles(dry_run)
        task_count = await _batch_update_tasks(dry_run)
        assignment_count = await _batch_update_assignments(dry_run)
        logger.info("Backfill complete: profiles=%s tasks=%s assignments=%s", profile_count, task_count, assignment_count)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Compute values without writing them")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run))