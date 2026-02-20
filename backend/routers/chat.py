"""Chat router."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import get_current_user
from database import get_db
from models import ChatRoom, ChatRoomMember, User
from schemas import RoomOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/rooms", response_model=list[RoomOut])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatRoom)
        .join(ChatRoomMember)
        .where(ChatRoomMember.user_id == user.id)
        .order_by(ChatRoom.created_at.desc())
    )
    return result.scalars().all()
