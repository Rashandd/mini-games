"""Games and lobbies router."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import get_current_user
from database import get_db
from models import Game, GameSession, User
from schemas import GameOut, LobbyOut

router = APIRouter(prefix="/api", tags=["games"])


@router.get("/games", response_model=list[GameOut])
async def list_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.is_active == True))
    return result.scalars().all()


@router.get("/lobbies/{slug}", response_model=list[LobbyOut])
async def list_lobbies(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    game = (await db.execute(select(Game).where(Game.slug == slug))).scalar_one_or_none()
    if not game:
        return []

    result = await db.execute(
        select(GameSession)
        .options(selectinload(GameSession.player1))
        .where(GameSession.game_id == game.id, GameSession.status == "waiting")
        .order_by(GameSession.started_at.desc())
    )
    sessions = result.scalars().all()
    now = datetime.utcnow()
    out = []
    for gs in sessions:
        delta = (now - gs.started_at).total_seconds()
        if delta < 60:
            age = f"{int(delta)}s ago"
        elif delta < 3600:
            age = f"{int(delta / 60)}m ago"
        else:
            age = f"{int(delta / 3600)}h ago"
        out.append(LobbyOut(
            room_code=gs.room_code,
            host=gs.player1.username if gs.player1 else "?",
            is_private=gs.is_private,
            age=age,
        ))
    return out
