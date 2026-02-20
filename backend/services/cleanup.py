"""Lobby cleanup background task (asyncio)."""
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select
from database import async_session
from models import GameSession


async def cleanup_loop():
    """Remove stale game sessions every 30 seconds."""
    while True:
        await asyncio.sleep(30)
        try:
            async with async_session() as db:
                cutoff = datetime.utcnow() - timedelta(seconds=120)
                result = await db.execute(
                    select(GameSession).where(
                        GameSession.status == "waiting",
                        GameSession.last_activity < cutoff,
                    )
                )
                stale = result.scalars().all()
                for gs in stale:
                    await db.delete(gs)
                await db.commit()
                if stale:
                    print(f" [Cleanup] Removed {len(stale)} stale lobby(s)")
        except Exception as e:
            print(f" [Cleanup] Error: {e}")
