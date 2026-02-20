"""ELO leaderboard service."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import LeaderboardEntry


K_FACTOR = 32


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


async def update_elo(
    db: AsyncSession,
    game_id: int,
    winner_id: int,
    loser_id: int,
    is_draw: bool = False,
):
    """Update ELO ratings for two players after a game."""
    w_entry = await _get_or_create_entry(db, winner_id, game_id)
    l_entry = await _get_or_create_entry(db, loser_id, game_id)

    expected_w = expected_score(w_entry.rating, l_entry.rating)
    expected_l = expected_score(l_entry.rating, w_entry.rating)

    if is_draw:
        w_entry.rating = round(w_entry.rating + K_FACTOR * (0.5 - expected_w))
        l_entry.rating = round(l_entry.rating + K_FACTOR * (0.5 - expected_l))
        w_entry.draws += 1
        l_entry.draws += 1
    else:
        w_entry.rating = round(w_entry.rating + K_FACTOR * (1 - expected_w))
        l_entry.rating = round(l_entry.rating + K_FACTOR * (0 - expected_l))
        w_entry.wins += 1
        l_entry.losses += 1

    await db.flush()


async def _get_or_create_entry(
    db: AsyncSession, user_id: int, game_id: int
) -> LeaderboardEntry:
    result = await db.execute(
        select(LeaderboardEntry).where(
            LeaderboardEntry.user_id == user_id,
            LeaderboardEntry.game_id == game_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        entry = LeaderboardEntry(user_id=user_id, game_id=game_id)
        db.add(entry)
        await db.flush()
    return entry
