"""The admin portal API. Every route needs an admin (`require_admin`): anyone
else gets 403. Learners see announcements through `/announcements/active`."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.models.profile import Profile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.admin import (
    ActiveAnnouncement,
    AdminCareer,
    AdminCareerRow,
    AdminMe,
    AdminResource,
    AdminResourceList,
    AdminStats,
    AdminUserList,
    AnnouncementCreate,
    AnnouncementOut,
    AnnouncementUpdate,
    AuditList,
    CareerCreate,
    CareerUpdate,
    ResourceFields,
    RoleRequest,
)
from app.services.admin_service import AdminService, active_announcements, make_admin_if_listed

NOT_ADMIN = "You do not have access to the admin portal."

router = APIRouter(prefix="/admin", tags=["Admin"])
public = APIRouter(tags=["Announcements"])


@dataclass
class Admin:
    profile: Profile
    email: str | None
    service: AdminService


async def require_admin(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Admin:
    """The signed-in admin, or 403. Accounts listed in ADMIN_EMAILS become
    admins here, the first time they ask."""
    profile = await ProfileRepository(db).get_by_auth_user_id(current_user.id)
    email = getattr(current_user, "email", None)

    if profile is None or not await make_admin_if_listed(db, profile, email):
        raise HTTPException(status_code=403, detail=NOT_ADMIN)

    return Admin(profile, email, AdminService(db, profile, email))


@router.get("/me", response_model=AdminMe)
async def me(admin: Admin = Depends(require_admin)):
    return AdminMe(id=admin.profile.id, name=admin.profile.full_name, email=admin.email)


@router.get("/stats", response_model=AdminStats)
async def stats(days: int = Query(default=7, ge=1, le=90), admin: Admin = Depends(require_admin)):
    return await admin.service.stats(days)


@router.get("/users", response_model=AdminUserList)
async def users(
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin: Admin = Depends(require_admin),
):
    return await admin.service.users(search, limit, offset)


@router.patch("/users/{profile_id}/role")
async def set_role(profile_id: UUID, request: RoleRequest, admin: Admin = Depends(require_admin)):
    return await admin.service.set_role(profile_id, request.role)


@router.get("/careers", response_model=list[AdminCareerRow])
async def careers(admin: Admin = Depends(require_admin)):
    return await admin.service.careers()


@router.get("/careers/{career_id}", response_model=AdminCareer)
async def career(career_id: UUID, admin: Admin = Depends(require_admin)):
    return await admin.service.career(career_id)


@router.post("/careers", response_model=AdminCareer, status_code=201)
async def create_career(request: CareerCreate, admin: Admin = Depends(require_admin)):
    return await admin.service.create_career(request)


@router.put("/careers/{career_id}", response_model=AdminCareer)
async def update_career(career_id: UUID, request: CareerUpdate, admin: Admin = Depends(require_admin)):
    return await admin.service.update_career(career_id, request)


@router.get("/resources", response_model=AdminResourceList)
async def resources(
    search: str | None = Query(default=None, max_length=100),
    active: bool | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin: Admin = Depends(require_admin),
):
    return await admin.service.resources(search, active, limit, offset)


@router.post("/resources", response_model=AdminResource, status_code=201)
async def create_resource(request: ResourceFields, admin: Admin = Depends(require_admin)):
    return await admin.service.create_resource(request)


@router.put("/resources/{resource_id}", response_model=AdminResource)
async def update_resource(resource_id: UUID, request: ResourceFields, admin: Admin = Depends(require_admin)):
    return await admin.service.update_resource(resource_id, request)


@router.get("/announcements", response_model=list[AnnouncementOut])
async def announcements(admin: Admin = Depends(require_admin)):
    return await admin.service.announcements()


@router.post("/announcements", response_model=AnnouncementOut, status_code=201)
async def publish(request: AnnouncementCreate, admin: Admin = Depends(require_admin)):
    return await admin.service.publish(request)


@router.patch("/announcements/{announcement_id}", response_model=AnnouncementOut)
async def update_announcement(
    announcement_id: UUID, request: AnnouncementUpdate, admin: Admin = Depends(require_admin)
):
    return await admin.service.update_announcement(announcement_id, request)


@router.get("/audit", response_model=AuditList)
async def audit(
    limit: int = Query(default=50, ge=1, le=100),
    before: datetime | None = None,
    action: str | None = Query(default=None, max_length=40),
    admin: Admin = Depends(require_admin),
):
    return await admin.service.audit(limit, before, action)


@public.get("/announcements/active", response_model=list[ActiveAnnouncement])
async def active(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """The banners learners see: switched on, started and not ended."""
    return await active_announcements(db)
