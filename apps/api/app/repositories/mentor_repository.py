from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.mentor_conversation import (
    MentorConversation,
)

from app.models.mentor_message import MentorMessage

class MentorRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self,
        profile_id: UUID,
        title: str,
    ) -> MentorConversation:

        conversation = MentorConversation(
            profile_id=profile_id,
            title=title,
        )

        self.db.add(conversation)

        await self.db.flush()

        return conversation

    async def list_conversations(
        self,
        profile_id: UUID,
        limit: int,
        offset: int,
    ) -> list[MentorConversation]:

        stmt = (
            select(MentorConversation)
            .where(
                MentorConversation.profile_id == profile_id
            )
            .order_by(
                MentorConversation.updated_at.desc(),
                MentorConversation.created_at.desc(),
                MentorConversation.id.desc(),
            )
            .limit(limit)
            .offset(offset)
       )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())


    async def count_conversations(
        self,
        profile_id: UUID,
    ) -> int:

        stmt = (
            select(func.count(MentorConversation.id))
            .where(
                MentorConversation.profile_id == profile_id
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one()

    async def get_conversation_by_id(
        self,
        conversation_id: UUID,
        profile_id: UUID,
    ) -> MentorConversation | None:

        stmt = (
            select(MentorConversation)
            .where(
                MentorConversation.id == conversation_id,
                MentorConversation.profile_id == profile_id,
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()


    async def get_conversation_messages(
        self,
        conversation_id: UUID,
    ) -> list[MentorMessage]:

        stmt = (
            select(MentorMessage)
            .where(
                MentorMessage.conversation_id == conversation_id
            )
            .order_by(
                MentorMessage.created_at.asc(),
                MentorMessage.id.asc(),
            )
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_recent_messages(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ) -> list[MentorMessage]:

        stmt = (
            select(MentorMessage)
            .where(
                MentorMessage.conversation_id == conversation_id
            )
            .order_by(
                MentorMessage.created_at.desc(),
                MentorMessage.id.desc(),
            )
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        messages = list(result.scalars().all())

        return list(reversed(messages))


    async def create_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> MentorMessage:

        message = MentorMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(message)

        await self.db.flush()

        return message


    async def touch_conversation(
        self,
        conversation: MentorConversation,
    ):
        conversation.updated_at = datetime.now(timezone.utc)

        await self.db.flush()    