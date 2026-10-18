import json

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.services.account_service import AccountService

router = APIRouter(
    prefix="/account",
    tags=["Account"],
)


@router.get("/export")
async def export_my_data(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Everything stored about the signed-in user, as a JSON download."""
    data = await AccountService(db).export(current_user.id)

    return Response(
        content=json.dumps(data, indent=2, ensure_ascii=False, default=str),
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="uraan-ai-data.json"',
            "Cache-Control": "no-store",
        },
    )
