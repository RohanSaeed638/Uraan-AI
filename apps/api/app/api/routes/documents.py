from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    GenerateDocumentRequest,
    UpdateDocumentRequest,
)
from app.services.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/generate",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_document(
    payload: GenerateDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await DocumentService(db).generate(payload, current_user.id)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await DocumentService(db).list(current_user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await DocumentService(db).get(document_id, current_user.id)


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    payload: UpdateDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await DocumentService(db).update(
        document_id, payload, current_user.id
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await DocumentService(db).delete(document_id, current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
