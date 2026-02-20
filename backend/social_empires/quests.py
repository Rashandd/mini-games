"""Async quest map loader."""
import json
import os
import asyncio
import aiofiles

from config import settings

QUESTS_DIR = settings.QUESTS_DIR


async def get_quest_map(questid):
    file = os.path.join(QUESTS_DIR, str(questid) + ".json")
    exists = await asyncio.to_thread(os.path.exists, file)
    if not exists:
        return None
    async with aiofiles.open(file, "r") as f:
        return json.loads(await f.read())
