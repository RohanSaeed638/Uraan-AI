from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Query

from app.db.base import get_db
from app.services.mentor_service import MentorService
from app.schemas.mentor import (
    MentorConversationCreateRequest,
    MentorConversationResponse,
    MentorConversationDetailResponse,
    MentorConversationListResponse,
    MentorMessageCreateRequest,
    MentorMessageCreateResponse,
    MentorSuggestionsResponse,
    MotivationResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.services.motivation_service import MotivationService
from app.services.review_service import ReviewService
from app.api.dependencies import get_current_user
from uuid import UUID

router = APIRouter(
    prefix="/mentor",
    tags=["AI Mentor"],
)

@router.get(
    "/suggestions",
    response_model=MentorSuggestionsResponse,
)
async def mentor_suggestions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    chips = await MentorService(db).suggestions(current_user.id)

    return {"chips": [vars(chip) for chip in chips]}


@router.get(
    "/motivation",
    response_model=MotivationResponse,
)
async def daily_motivation(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await MotivationService(db).today(current_user.id)


@router.post(
    "/review",
    response_model=ReviewResponse,
)
async def review_work(
    payload: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ReviewService(db).review(current_user.id, payload.model_dump())


@router.post(
    "/conversations",
    response_model=MentorConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mentor_conversation(
    payload: MentorConversationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MentorService(db)

    return await service.create_conversation(
        payload=payload,
        auth_user_id=current_user.id,
    )

@router.get(
    "/conversations",
    response_model=MentorConversationListResponse,
)
async def list_mentor_conversations(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MentorService(db)

    return await service.list_conversations(
        auth_user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

@router.get(
    "/conversations/{conversation_id}",
    response_model=MentorConversationDetailResponse,
)
async def get_mentor_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MentorService(db)

    return await service.get_conversation_detail(
        conversation_id=conversation_id,
        auth_user_id=current_user.id,
    )    

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MentorMessageCreateResponse,
    status_code=201,
)
async def send_mentor_message(
    conversation_id: UUID,
    payload: MentorMessageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MentorService(db)

    return await service.send_message(
        conversation_id=conversation_id,
        payload=payload,
        auth_user_id=current_user.id,
    )

@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_mentor_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MentorService(db)

    await service.delete_conversation(
        conversation_id=conversation_id,
        auth_user_id=current_user.id,
    )