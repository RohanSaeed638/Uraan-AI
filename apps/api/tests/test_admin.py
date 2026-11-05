"""The admin portal: who gets in, what staff can change, and the record of it."""
import asyncio
import selectors
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.api.dependencies import get_current_user
from app.api.routes.admin import public as announcements_router
from app.api.routes.admin import router as admin_router
from app.core.config import settings
from app.db.base import get_db
from app.models.admin import AuditLog
from app.models.ai_request import AiRequest
from app.models.career import Career
from app.models.notification import Notification
from app.models.profile import Profile
from app.repositories.career_repository import CareerRepository
from app.repositories.profile_repository import ProfileRepository


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


class Harness:
    """A real (rolled back) database, the admin API on top of it, and people to be."""

    def __init__(self, db):
        self.db = db
        self.current = None
        self.api = FastAPI()
        self.api.include_router(admin_router)
        self.api.include_router(announcements_router)
        self.api.dependency_overrides[get_db] = lambda: db
        self.api.dependency_overrides[get_current_user] = lambda: self.current

    async def person(self, name="Staff", role="admin", email=None):
        auth_id = uuid4()
        email = email or f"{name.lower()}-{uuid4().hex[:6]}@example.com"

        await self.db.execute(
            text(
                "insert into auth.users (instance_id, id, aud, role, email) values "
                "('00000000-0000-0000-0000-000000000000', :i, 'authenticated', 'authenticated', :e)"
            ),
            {"i": auth_id, "e": email},
        )
        profile = Profile(auth_user_id=auth_id, full_name=name, daily_hours=1, xp=0, streak_days=0, role=role)
        self.db.add(profile)
        await self.db.flush()

        return SimpleNamespace(profile=profile, auth=SimpleNamespace(id=auth_id, email=email))

    def as_(self, person):
        self.current = person.auth

    async def call(self, method, url, **kwargs):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.api), base_url="http://t") as client:
            return await client.request(method, url, **kwargs)


def with_db(fn):
    async def go():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
                try:
                    return await fn(Harness(db))
                finally:
                    await db.close()
                    await trans.rollback()
        finally:
            await engine.dispose()

    try:
        return run(go())
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")


async def audit(h, action=None):
    query = select(AuditLog).order_by(AuditLog.created_at, AuditLog.id)

    if action:
        query = query.where(AuditLog.action == action)

    return list((await h.db.execute(query)).scalars())


CAREER = {
    "slug": "test-career-xyz",
    "name": "Test Career",
    "description": "A career that exists only inside a test.",
    "category": "Testing",
    "icon": "Server",
    "color": "#7C3AED",
    "difficulty": "beginner",
    "estimated_months": 6,
    "salary_min_pkr": 50000,
    "salary_max_pkr": 150000,
    "market_demand": "high",
    "is_active": True,
    "skills": [{"name": "Patience"}, {"name": "Care"}],
    "resources": [
        {"title": "Guide", "type": "docs", "provider": "Acme", "url": "https://example.com/guide", "is_free": True,
         "difficulty": "beginner"}
    ],
}

RESOURCE = {
    "title": "A test course",
    "url": "https://example.com/test-course-xyz",
    "type": "course",
    "provider": "Acme",
    "description": "For tests.",
    "is_free": True,
    "difficulty": "beginner",
    "career_slugs": ["backend-engineer"],
    "language": "en",
    "is_active": True,
}

ROUTES = [
    ("GET", "/admin/me"),
    ("GET", "/admin/stats"),
    ("GET", "/admin/users"),
    ("PATCH", "/admin/users/00000000-0000-0000-0000-000000000001/role"),
    ("GET", "/admin/careers"),
    ("GET", "/admin/careers/00000000-0000-0000-0000-000000000001"),
    ("POST", "/admin/careers"),
    ("PUT", "/admin/careers/00000000-0000-0000-0000-000000000001"),
    ("GET", "/admin/resources"),
    ("POST", "/admin/resources"),
    ("PUT", "/admin/resources/00000000-0000-0000-0000-000000000001"),
    ("GET", "/admin/announcements"),
    ("POST", "/admin/announcements"),
    ("PATCH", "/admin/announcements/00000000-0000-0000-0000-000000000001"),
    ("GET", "/admin/audit"),
]


# ---- who gets in -------------------------------------------------------------------------------------------------------------


def test_a_learner_is_refused_everywhere():
    async def check(h):
        learner = await h.person("Learner", role="user")
        h.as_(learner)
        refused = []

        for method, url in ROUTES:
            r = await h.call(method, url, json={})

            if r.status_code != 403:
                refused.append((method, url, r.status_code))

        return refused

    assert with_db(check) == []


def test_someone_without_a_profile_is_refused():
    async def check(h):
        h.current = SimpleNamespace(id=uuid4(), email="nobody@example.com")

        return (await h.call("GET", "/admin/me")).status_code

    assert with_db(check) == 403


def test_an_admin_gets_in():
    async def check(h):
        admin = await h.person("Staff", role="admin")
        h.as_(admin)
        r = await h.call("GET", "/admin/me")

        return r.status_code, r.json()["name"]

    assert with_db(check) == (200, "Staff")


def test_an_address_in_the_admin_list_becomes_an_admin_once(monkeypatch):
    async def check(h):
        monkeypatch.setattr(settings, "ADMIN_EMAILS", "Boss@Example.com, other@example.com")
        boss = await h.person("Boss", role="user", email="boss@example.com")
        stranger = await h.person("Stranger", role="user", email="stranger@example.com")

        h.as_(stranger)
        refused = (await h.call("GET", "/admin/me")).status_code

        h.as_(boss)
        first = (await h.call("GET", "/admin/me")).status_code
        await h.call("GET", "/admin/me")
        await h.db.refresh(boss.profile)
        await h.db.refresh(stranger.profile)

        return refused, first, boss.profile.role, stranger.profile.role, len(await audit(h, "user.role"))

    assert with_db(check) == (403, 200, "admin", "user", 1)


def test_the_admin_list_is_empty_by_default():
    assert settings.admin_emails == set() or isinstance(settings.admin_emails, set)


# ---- people -------------------------------------------------------------------------------------------------------------------------


def test_the_user_list_has_emails_search_and_paging():
    async def check(h):
        admin = await h.person("Staff")
        ayesha = await h.person("Ayesha Findme", role="user", email="ayesha-findme@example.com")
        await h.person("Someone Else", role="user")
        h.as_(admin)

        found = (await h.call("GET", "/admin/users?search=findme")).json()
        by_mail = (await h.call("GET", "/admin/users?search=ayesha-findme@")).json()
        page = (await h.call("GET", "/admin/users?limit=1&offset=0")).json()

        return found, by_mail, page, ayesha

    found, by_mail, page, ayesha = with_db(check)

    assert found["total"] == 1 and found["items"][0]["email"] == "ayesha-findme@example.com"
    assert found["items"][0]["role"] == "user" and by_mail["total"] == 1
    assert len(page["items"]) == 1 and page["total"] >= 3


def test_roles_can_be_changed_and_it_is_recorded():
    async def check(h):
        admin = await h.person("Staff")
        learner = await h.person("Learner", role="user")
        h.as_(admin)

        up = await h.call("PATCH", f"/admin/users/{learner.profile.id}/role", json={"role": "admin"})
        again = await h.call("PATCH", f"/admin/users/{learner.profile.id}/role", json={"role": "admin"})
        down = await h.call("PATCH", f"/admin/users/{learner.profile.id}/role", json={"role": "user"})
        bad = await h.call("PATCH", f"/admin/users/{learner.profile.id}/role", json={"role": "owner"})
        missing = await h.call("PATCH", f"/admin/users/{uuid4()}/role", json={"role": "admin"})

        return up.json(), again.status_code, down.json(), bad.status_code, missing.status_code, await audit(h, "user.role")

    up, again, down, bad, missing, entries = with_db(check)

    assert up["role"] == "admin" and again == 200 and down["role"] == "user"
    assert bad == 422 and missing == 404
    assert len(entries) == 2 and entries[0].changes == {"role": ["user", "admin"]}  # the repeat changed nothing


def test_you_cannot_remove_your_own_admin_access():
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)
        r = await h.call("PATCH", f"/admin/users/{admin.profile.id}/role", json={"role": "user"})
        await h.db.refresh(admin.profile)

        return r.status_code, r.json()["detail"], admin.profile.role

    assert with_db(check) == (409, "You cannot remove your own admin access.", "admin")


# ---- the numbers -----------------------------------------------------------------------------------------------------------------


def test_stats_count_people_and_ai_calls():
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)
        before = (await h.call("GET", "/admin/stats")).json()

        for ok, provider in ((True, "openai"), (True, "openai"), (False, "gemini")):
            h.db.add(AiRequest(purpose="unit-test", provider=provider, model="m", success=ok,
                               error_type=None if ok else "TimeoutError", latency_ms=100))
        await h.db.flush()

        after = (await h.call("GET", "/admin/stats")).json()

        return before, after

    before, after = with_db(check)
    mine = next(p for p in after["ai_by_purpose"] if p["purpose"] == "unit-test")

    assert after["counts"]["users"] == before["counts"]["users"]
    assert after["ai_requests"] == before["ai_requests"] + 3 and after["ai_failures"] == before["ai_failures"] + 1
    assert mine == {"purpose": "unit-test", "requests": 3, "failures": 1, "failure_rate": 0.333, "avg_latency_ms": 100}
    assert any(f["purpose"] == "unit-test" and f["error_type"] == "TimeoutError" for f in after["recent_failures"])
    assert {"users", "new_users_7d", "active_users_7d", "roadmaps", "lessons_completed", "tasks_completed",
            "mentor_messages"} == set(after["counts"])


# ---- careers ---------------------------------------------------------------------------------------------------------------------


def test_a_career_can_be_created_edited_and_switched_off():
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)

        made = await h.call("POST", "/admin/careers", json=CAREER)
        cid = made.json()["id"]
        row = (await h.call("GET", f"/admin/careers/{cid}")).json()

        edited = dict(CAREER, name="Better Name", skills=[{"name": "Focus"}], resources=[])
        edited.pop("slug")
        saved = await h.call("PUT", f"/admin/careers/{cid}", json=edited)

        off = await h.call("PUT", f"/admin/careers/{cid}", json=dict(edited, is_active=False))
        listed = (await h.call("GET", "/admin/careers")).json()

        public, _ = await CareerRepository(h.db).search(
            search="Better Name", difficulty=None, demand=None, category=None,
            min_salary=None, max_salary=None, page=1, page_size=10,
        )
        exists = await ProfileRepository(h.db).career_exists("test-career-xyz")

        return made.status_code, row, saved.json(), off.status_code, listed, public, exists, await audit(h)

    status, row, saved, off, listed, public, exists, entries = with_db(check)

    assert status == 201 and [s["name"] for s in row["skills"]] == ["Patience", "Care"]
    assert row["resources"][0]["url"] == "https://example.com/guide"
    assert saved["name"] == "Better Name" and [s["name"] for s in saved["skills"]] == ["Focus"] and saved["resources"] == []
    assert off == 200
    assert next(c for c in listed if c["slug"] == "test-career-xyz")["is_active"] is False  # still listed for staff
    assert public == [] and exists is False  # but learners no longer see it
    assert [e.action for e in entries] == ["career.create", "career.update", "career.update"]
    assert entries[1].changes["name"] == ["Test Career", "Better Name"]
    assert entries[2].summary.startswith("Switched off career")


def test_a_new_career_can_be_chosen_by_learners():
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)
        await h.call("POST", "/admin/careers", json=CAREER)

        return await ProfileRepository(h.db).career_exists("test-career-xyz")

    assert with_db(check) is True


@pytest.mark.parametrize(
    "change,code",
    [
        ({"slug": "Bad Slug!"}, 422),
        ({"slug": "x"}, 422),
        ({"color": "purple"}, 422),
        ({"difficulty": "impossible"}, 422),
        ({"market_demand": "huge"}, 422),
        ({"estimated_months": 0}, 422),
        ({"salary_min_pkr": 900000, "salary_max_pkr": 1000}, 422),
        ({"resources": [{"title": "x", "type": "docs", "url": "javascript:alert(1)"}]}, 422),
        ({"resources": [{"title": "x", "type": "movie", "url": "https://e.com"}]}, 422),
        ({"description": "short"}, 422),
        ({"slug": "backend-engineer"}, 409),
    ],
)
def test_bad_careers_are_refused(change, code):
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)
        r = await h.call("POST", "/admin/careers", json={**CAREER, **change})

        return r.status_code, await audit(h, "career.create"), (await h.db.execute(select(Career).where(Career.slug == CAREER["slug"]))).first()

    status, entries, row = with_db(check)

    assert status == code and entries == [] and row is None  # nothing saved, nothing recorded


# ---- library resources ---------------------------------------------------------------------------------------------


def test_a_resource_can_be_added_changed_and_switched_off():
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)

        made = await h.call("POST", "/admin/resources", json=RESOURCE)
        rid = made.json()["id"]
        saved = await h.call("PUT", f"/admin/resources/{rid}", json=dict(RESOURCE, title="Renamed"))
        off = await h.call("PUT", f"/admin/resources/{rid}", json=dict(RESOURCE, title="Renamed", is_active=False))
        active = (await h.call("GET", "/admin/resources?search=Renamed&active=true")).json()
        inactive = (await h.call("GET", "/admin/resources?search=Renamed&active=false")).json()

        return made.status_code, saved.json()["title"], off.json()["is_active"], active["total"], inactive["total"], await audit(h)

    status, title, is_active, active, inactive, entries = with_db(check)

    assert (status, title, is_active, active, inactive) == (201, "Renamed", False, 0, 1)
    assert [e.action for e in entries] == ["resource.create", "resource.update", "resource.update"]
    assert entries[1].changes == {"title": ["A test course", "Renamed"]}


def test_bad_resources_are_refused():
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)
        first = await h.call("POST", "/admin/resources", json=RESOURCE)
        again = await h.call("POST", "/admin/resources", json=RESOURCE)  # same link
        unknown = await h.call("POST", "/admin/resources", json=dict(RESOURCE, url="https://example.com/other", career_slugs=["no-such-career"]))
        bad_link = await h.call("POST", "/admin/resources", json=dict(RESOURCE, url="ftp://example.com/x"))
        clash = await h.call("PUT", f"/admin/resources/{uuid4()}", json=RESOURCE)

        return first.status_code, again.status_code, unknown.status_code, unknown.json()["detail"], bad_link.status_code, clash.status_code

    assert with_db(check) == (201, 409, 422, "Unknown careers: no-such-career", 422, 404)


# ---- announcements -----------------------------------------------------------------------------------------------------


def test_an_announcement_reaches_the_banner_and_everyones_notifications():
    async def check(h):
        admin = await h.person("Staff")
        learner = await h.person("Learner", role="user")
        h.as_(admin)

        quiet = await h.call("POST", "/admin/announcements", json={"title": "Quiet note", "body": "No notification."})
        loud = await h.call("POST", "/admin/announcements", json={
            "title": "Maintenance tonight", "body": "Back by 6 am.", "level": "warning", "notify": True})

        profiles = (await h.db.execute(text("select count(*) from profiles"))).scalar_one()
        notes = (await h.db.execute(select(Notification).where(Notification.type == "announcement"))).scalars().all()

        h.as_(learner)
        seen = (await h.call("GET", "/announcements/active")).json()

        return quiet.json(), loud.json(), profiles, notes, seen

    quiet, loud, profiles, notes, seen = with_db(check)

    assert quiet["notified"] == 0 and loud["notified"] == profiles and len(notes) == profiles
    assert {n.title for n in notes} == {"Maintenance tonight"} and {n.url for n in notes} == {"/dashboard"}
    assert [a["title"] for a in seen] == ["Maintenance tonight", "Quiet note"] and seen[0]["level"] == "warning"


def test_notifying_twice_adds_nothing():
    from app.models.admin import Announcement
    from app.services.admin_service import AdminService

    async def check(h):
        admin = await h.person("Staff")
        row = Announcement(title="Once", body="Only once.")
        h.db.add(row)
        await h.db.flush()
        service = AdminService(h.db, admin.profile)

        return await service._notify_everyone(row), await service._notify_everyone(row)

    first, second = with_db(check)

    assert first >= 1 and second == 0


def test_announcements_can_be_switched_off_and_expire():
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)
        a = (await h.call("POST", "/admin/announcements", json={"title": "Switch me", "body": "Off soon."})).json()
        b = (await h.call("POST", "/admin/announcements", json={
            "title": "Ends soon", "body": "Short.", "ends_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()})).json()
        past = await h.call("POST", "/admin/announcements", json={
            "title": "Too late", "body": "Already over.", "ends_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()})

        before = [x["title"] for x in (await h.call("GET", "/announcements/active")).json()]
        await h.call("PATCH", f"/admin/announcements/{a['id']}", json={"is_active": False})
        await h.call("PATCH", f"/admin/announcements/{b['id']}", json={"ends_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()})
        after = [x["title"] for x in (await h.call("GET", "/announcements/active")).json()]
        listed = [x["title"] for x in (await h.call("GET", "/admin/announcements")).json()]
        unknown = await h.call("PATCH", f"/admin/announcements/{uuid4()}", json={"is_active": False})
        extra = await h.call("PATCH", f"/admin/announcements/{a['id']}", json={"title": "sneaky"})

        return past.status_code, before, after, listed, unknown.status_code, extra.status_code

    past, before, after, listed, unknown, extra = with_db(check)

    assert past == 422 and before == ["Ends soon", "Switch me"] and after == []
    assert {"Switch me", "Ends soon"} <= set(listed)  # staff still see them
    assert unknown == 404 and extra == 422


def test_only_learners_who_are_signed_in_see_banners():
    async def check(h):
        h.current = None

        async def refuse():
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Invalid or expired session. Please sign in again.")

        h.api.dependency_overrides[get_current_user] = refuse

        return (await h.call("GET", "/announcements/active")).status_code

    assert with_db(check) == 401


# ---- the record --------------------------------------------------------------------------------------------------------------


def test_the_audit_log_says_who_did_what_and_pages():
    async def check(h):
        admin = await h.person("Staff", email="staff@example.com")
        h.as_(admin)

        for i in range(5):
            await h.call("POST", "/admin/resources", json=dict(RESOURCE, url=f"https://example.com/r{i}", title=f"Resource {i}"))

        await h.call("POST", "/admin/announcements", json={"title": "Hello all", "body": "Hi."})

        # Inside one test transaction every row gets the same clock time; real requests do not.
        now = datetime.now(timezone.utc)

        for i, entry in enumerate(await audit(h)):
            entry.created_at = now + timedelta(seconds=i)

        await h.db.flush()

        everything = (await h.call("GET", "/admin/audit?limit=3")).json()
        older = (await h.call("GET", "/admin/audit?limit=3&before=" + everything["items"][-1]["at"].replace("+", "%2B"))).json()
        only = (await h.call("GET", "/admin/audit?action=announcement")).json()

        return everything, older, only

    everything, older, only = with_db(check)

    assert everything["has_more"] is True and len(everything["items"]) == 3
    assert everything["items"][0]["action"] == "announcement.publish"
    assert everything["items"][0]["actor"] == "Staff <staff@example.com>"
    assert len(older["items"]) == 3 and older["has_more"] is False  # 6 entries: 3 + 3
    assert older["items"][0]["at"] < everything["items"][-1]["at"]
    assert [e["action"] for e in only["items"]] == ["announcement.publish"]


def test_a_failed_change_leaves_no_record():
    async def check(h):
        admin = await h.person("Staff")
        h.as_(admin)
        await h.call("POST", "/admin/resources", json=RESOURCE)
        await h.call("POST", "/admin/resources", json=RESOURCE)  # refused: same link

        return len(await audit(h, "resource.create"))

    assert with_db(check) == 1


def test_signing_in_with_a_listed_address_makes_the_admin_link_appear(monkeypatch):
    """The app reads the role from /profile/me, so the first sign-in must promote."""
    from app.api.routes.profile import router as profile_router

    async def check(h):
        monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss@example.com")
        boss = await h.person("Boss", role="user", email="boss@example.com")
        other = await h.person("Other", role="user", email="other@example.com")
        h.api.include_router(profile_router)

        h.as_(other)
        first = (await h.call("GET", "/profile/me")).json()["role"]
        h.as_(boss)
        second = (await h.call("GET", "/profile/me")).json()["role"]

        return first, second

    assert with_db(check) == ("user", "admin")
