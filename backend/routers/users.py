"""Users router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import User
from schemas import UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search", response_model=list[UserOut])
async def search_users(
    q: str = Query("", min_length=2),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User)
        .where(User.username.ilike(f"%{q}%"), User.id != user.id)
        .limit(10)
    )
    return result.scalars().all()
