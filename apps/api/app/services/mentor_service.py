from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.mentor import MentorConversationListResponse

from app.repositories.profile_repository import (
    ProfileRepository,
)
from app.repositories.mentor_repository import (
    MentorRepository,
)
from app.schemas.mentor import (
    MentorConversationCreateRequest,
    MentorConversationResponse,
    MentorConversationDetailResponse,
    MentorMessageResponse,
    MentorMessageCreateRequest,
    MentorMessageCreateResponse,
)
import logging

from datetime import datetime, timezone

from openai import OpenAIError

from app.repositories.settings_repository import SettingsRepository
from app.services.mentor_ai_service import MentorAIService


logger = logging.getLogger(__name__)

class MentorService:

    def __init__(self, db: AsyncSession):
        self.db = db

        self.profile_repository = ProfileRepository(db)
        self.mentor_repository = MentorRepository(db)
        self.mentor_ai_service = MentorAIService()
        self.settings_repository = SettingsRepository(db)

    async def _require_mentor_enabled(self, profile_id: UUID) -> None:
        """403 when the user switched the AI mentor off in Settings.
        No saved settings means the default, which is on."""
        settings = await self.settings_repository.get_by_profile_id(
            profile_id
        )

        if settings is not None and not settings.ai_mentor_enabled:
            raise HTTPException(
                status_code=403,
                detail="AI Mentor is turned off in Settings.",
            )

    async def create_conversation(
        self,
        payload: MentorConversationCreateRequest,
        auth_user_id: UUID,
    ) -> MentorConversationResponse:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        await self._require_mentor_enabled(profile.id)

        try:
            conversation = await (
                self.mentor_repository
                .create_conversation(
                    profile_id=profile.id,
                    title=payload.title.strip(),
                )
            )

            await self.db.commit()
            await self.db.refresh(conversation)

        except Exception:
            await self.db.rollback()
            raise

        return MentorConversationResponse.model_validate(
            conversation
        )

    async def list_conversations(
        self,
        auth_user_id: UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> MentorConversationListResponse:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        offset = (page - 1) * page_size

        conversations = await (
            self.mentor_repository
            .list_conversations(
                profile_id=profile.id,
                limit=page_size,
                offset=offset,
            )
        )

        total = await (
            self.mentor_repository
            .count_conversations(
                profile_id=profile.id,
            )
        )

        total_pages = (
            (total + page_size - 1) // page_size
        )

        return MentorConversationListResponse(
            conversations=[
                MentorConversationResponse.model_validate(
                    conversation
                )
                for conversation in conversations
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
        )

    async def get_conversation_detail(
        self,
        conversation_id: UUID,
        auth_user_id: UUID,
    ) -> MentorConversationDetailResponse:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        conversation = await (
            self.mentor_repository
            .get_conversation_by_id(
                conversation_id=conversation_id,
                profile_id=profile.id,
            )
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        messages = await (
            self.mentor_repository
            .get_conversation_messages(
                conversation_id=conversation.id,
            )
        )

        return MentorConversationDetailResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[
                MentorMessageResponse.model_validate(message)
                for message in messages
            ],
        )

    async def send_message(
        self,
        conversation_id: UUID,
        payload: MentorMessageCreateRequest,
        auth_user_id: UUID,
    ) -> MentorMessageCreateResponse:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        conversation = await (
            self.mentor_repository
            .get_conversation_by_id(
                conversation_id=conversation_id,
                profile_id=profile.id,
            )
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        await self._require_mentor_enabled(profile.id)

        content = payload.content.strip()

        if not content:
            raise HTTPException(
                status_code=422,
                detail="Message cannot be empty",
            )

        history = await (
            self.mentor_repository
            .get_recent_messages(
                conversation_id=conversation.id,
                limit=20,
            )
        )

        llm_messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in history
        ]

        llm_messages.append({
            "role": "user",
            "content": content,
        })

        # Generate before writing messages.
        # A failed LLM request won't leave an
        # unanswered user message in the database.
        try:
            assistant_content = await (
                self.mentor_ai_service.generate_response(
                    messages=llm_messages,
                )
            )

        except (OpenAIError, RuntimeError):
            logger.exception(
                "AI Mentor generation failed for conversation %s",
                conversation_id,
            )

            raise HTTPException(
                status_code=503,
                detail=(
                    "AI Mentor is temporarily unavailable. "
                "Please try again."
                ),
            )

        try:
            user_message = await (
                self.mentor_repository.create_message(
                    conversation_id=conversation.id,
                    role="user",
                    content=content,
                )
            )

            assistant_message = await (
                self.mentor_repository.create_message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=assistant_content,
                )
            )

            await self.mentor_repository.touch_conversation(
                conversation
            )

            await self.db.commit()

            await self.db.refresh(user_message)
            await self.db.refresh(assistant_message)

        except Exception:
            await self.db.rollback()
            raise

        return MentorMessageCreateResponse(
            conversation_id=conversation.id,
            user_message=MentorMessageResponse.model_validate(
                user_message
            ),
            assistant_message=MentorMessageResponse.model_validate(
                assistant_message
            ),
        )

    async def delete_conversation(
        self,
        conversation_id: UUID,
        auth_user_id: UUID,
    ) -> None:

        profile = await (
            self.profile_repository
            .get_by_auth_user_id(auth_user_id)
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        conversation = await (
            self.mentor_repository
            .get_conversation_by_id(
                conversation_id=conversation_id,
                profile_id=profile.id,
            )
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        try:
            await self.mentor_repository.delete_conversation(
                conversation
            )

            await self.db.commit()
 
        except Exception:
            await self.db.rollback()
            raise