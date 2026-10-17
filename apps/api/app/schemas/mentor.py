from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

class MentorConversationCreateRequest(BaseModel):
    title: str = Field(
        default="New Conversation",
        min_length=1,
        max_length=200,
    )

class MentorConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

class MentorConversationListResponse(BaseModel):
    conversations: list[MentorConversationResponse] = Field(
        default_factory=list
    )

    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool    

class MentorMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }

class MentorConversationDetailResponse(
    MentorConversationResponse
):
    messages: list[MentorMessageResponse] = Field(
        default_factory=list
    )    

class MentorMessageCreateRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=8000,
    )

class MentorMessageCreateResponse(BaseModel):
    conversation_id: UUID
    user_message: MentorMessageResponse
    assistant_message: MentorMessageResponse    