from uuid import UUID
from app.services.achievement_service import AchievementService
from app.ai.llm import use_profile
from app.ai.versions import prompt_version

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.document_generator import DocumentGenerator
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    GenerateDocumentRequest,
    UpdateDocumentRequest,
)

MAX_DOCUMENTS = 20

KIND_TITLES = {
    "resume": "Resume",
    "cover_letter": "Cover letter",
    "linkedin_summary": "LinkedIn summary",
}


def default_title(kind: str, target_role: str) -> str:
    return f"{KIND_TITLES[kind]} - {target_role}"[:200]


class DocumentService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repository = ProfileRepository(db)
        self.repository = DocumentRepository(db)
        self.generator = DocumentGenerator()

    async def _profile(self, auth_user_id: UUID):
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    async def _owned(self, document_id: UUID, profile_id: UUID) -> Document:
        document = await self.repository.get_owned(document_id, profile_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document

    async def generate(
        self,
        payload: GenerateDocumentRequest,
        auth_user_id: UUID,
    ) -> DocumentResponse:
        profile = await self._profile(auth_user_id)
        use_profile(profile.id, profile.language)

        if await self.repository.count(profile.id) >= MAX_DOCUMENTS:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"You can keep up to {MAX_DOCUMENTS} documents. "
                    "Delete one to create another."
                ),
            )

        tasks = await self.repository.completed_task_titles(profile.id)
        projects = await self.repository.completed_project_titles(profile.id)

        try:
            content = await self.generator.generate(
                kind=payload.kind,
                profile=profile,
                target_role=payload.target_role,
                completed_tasks=tasks,
                projects=projects,
                details=payload.details,
                job_description=payload.job_description,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Could not write the document right now. Try again.",
            ) from exc

        document = Document(
            profile_id=profile.id,
            kind=payload.kind,
            title=default_title(payload.kind, payload.target_role),
            target_role=payload.target_role,
            content=content,
            prompt_version=prompt_version("document"),
        )

        try:
            await self.repository.create(document)
            await AchievementService(self.db).safe_evaluate(profile)
            await self.db.commit()
            await self.db.refresh(document)
        except Exception:
            await self.db.rollback()
            raise

        return DocumentResponse.model_validate(document)

    async def list(self, auth_user_id: UUID) -> DocumentListResponse:
        profile = await self._profile(auth_user_id)
        rows = await self.repository.list_for_profile(profile.id)

        return DocumentListResponse(
            documents=[DocumentResponse.model_validate(r) for r in rows]
        )

    async def get(
        self,
        document_id: UUID,
        auth_user_id: UUID,
    ) -> DocumentResponse:
        profile = await self._profile(auth_user_id)

        return DocumentResponse.model_validate(
            await self._owned(document_id, profile.id)
        )

    async def update(
        self,
        document_id: UUID,
        payload: UpdateDocumentRequest,
        auth_user_id: UUID,
    ) -> DocumentResponse:
        profile = await self._profile(auth_user_id)
        document = await self._owned(document_id, profile.id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"{field} cannot be empty",
                )
            setattr(document, field, value)

        try:
            await self.db.commit()
            await self.db.refresh(document)
        except Exception:
            await self.db.rollback()
            raise

        return DocumentResponse.model_validate(document)

    async def delete(self, document_id: UUID, auth_user_id: UUID) -> None:
        profile = await self._profile(auth_user_id)
        document = await self._owned(document_id, profile.id)

        try:
            await self.repository.delete(document)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
