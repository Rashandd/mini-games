"""Leaderboard router."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import get_current_user
from database import get_db
from models import Game, LeaderboardEntry, User
from schemas import LeaderboardEntryOut, GlobalLeaderboardEntryOut

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[GlobalLeaderboardEntryOut])
async def global_leaderboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(
            LeaderboardEntry.user_id,
            func.sum(LeaderboardEntry.score).label("total_score"),
            func.sum(LeaderboardEntry.wins).label("total_wins"),
            func.sum(LeaderboardEntry.losses).label("total_losses"),
            func.sum(LeaderboardEntry.draws).label("total_draws"),
            func.avg(LeaderboardEntry.rating).label("avg_rating"),
        )
        .group_by(LeaderboardEntry.user_id)
        .order_by(func.sum(LeaderboardEntry.score).desc())
        .limit(50)
    )
    rows = result.all()
    out = []
    for i, r in enumerate(rows):
        u = (await db.execute(select(User).where(User.id == r.user_id))).scalar_one_or_none()
        out.append(GlobalLeaderboardEntryOut(
            rank=i + 1,
            username=u.username if u else "Unknown",
            user_id=r.user_id,
            total_score=int(r.total_score or 0),
            total_wins=int(r.total_wins or 0),
            total_losses=int(r.total_losses or 0),
            total_draws=int(r.total_draws or 0),
            avg_rating=int(r.avg_rating or 1200),
        ))
    return out


@router.get("/{slug}", response_model=list[LeaderboardEntryOut])
async def game_leaderboard(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    game = (await db.execute(select(Game).where(Game.slug == slug))).scalar_one_or_none()
    if not game:
        return []
    result = await db.execute(
        select(LeaderboardEntry)
        .options(selectinload(LeaderboardEntry.user))
        .where(LeaderboardEntry.game_id == game.id)
        .order_by(LeaderboardEntry.rating.desc())
        .limit(50)
    )
    entries = result.scalars().all()
    return [
        LeaderboardEntryOut(
            rank=i + 1,
            username=e.user.username,
            user_id=e.user_id,
            rating=e.rating,
            wins=e.wins,
            losses=e.losses,
            draws=e.draws,
            total=e.total_games,
            win_rate=e.win_rate,
        )
        for i, e in enumerate(entries)
    ]
