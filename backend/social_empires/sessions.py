"""Async SE sessions — village load/save with aiofiles."""
import json
import os
import copy
import uuid
import random
import asyncio
import aiofiles

from social_empires.version import version_code, migrate_loaded_save
from social_empires.engine import timestamp_now
from social_empires.constants import Constant
from config import settings

VILLAGES_DIR = settings.VILLAGES_DIR
SAVES_DIR = settings.SAVES_DIR

__villages: dict = {}
__saves: dict = {}
__initial_village: dict = {}


async def load_saved_villages():
    """Load all villages and saves at startup (async I/O)."""
    global __villages, __saves, __initial_village

    __villages = {}
    __saves = {}

    # Load initial template
    async with aiofiles.open(os.path.join(VILLAGES_DIR, "initial.json"), "r") as f:
        __initial_village = json.loads(await f.read())

    # Saves dir check
    if not os.path.exists(SAVES_DIR):
        os.makedirs(SAVES_DIR, exist_ok=True)

    # Static neighbors in /villages
    village_files = await asyncio.to_thread(os.listdir, VILLAGES_DIR)
    for file in village_files:
        if file == "initial.json" or not file.endswith(".json"):
            continue
        print(f" * Loading static neighbour {file}... ", end="")
        async with aiofiles.open(os.path.join(VILLAGES_DIR, file), "r") as f:
            village = json.loads(await f.read())
        if not is_valid_village(village):
            print("Invalid neighbour")
            continue
        USERID = village["playerInfo"]["pid"]
        if str(USERID) in __villages:
            print(f"Ignored: duplicated PID '{USERID}'.")
        else:
            __villages[str(USERID)] = village
            print("Ok.")

    # Saves in /saves
    save_files = await asyncio.to_thread(os.listdir, SAVES_DIR)
    for file in save_files:
        if not file.endswith(".save.json"):
            continue
        print(f" * Loading save at {file}... ", end="")
        try:
            async with aiofiles.open(os.path.join(SAVES_DIR, file), "r") as f:
                save = json.loads(await f.read())
        except json.JSONDecodeError:
            print("Corrupted JSON.")
            continue
        if not is_valid_village(save):
            print("Invalid Save.")
            continue
        USERID = save["playerInfo"]["pid"]
        try:
            map_name = save["playerInfo"]["map_names"][save["playerInfo"]["default_map"]]
        except Exception:
            map_name = "?"
        print(f"({map_name}) Ok.")
        __saves[str(USERID)] = save
        modified = migrate_loaded_save(save)
        if modified:
            await save_session(USERID)


async def new_village() -> str:
    """Create a new village (async save)."""
    USERID = str(uuid.uuid4())
    assert USERID not in all_userid()
    village = copy.deepcopy(__initial_village)
    village["version"] = version_code
    village["playerInfo"]["pid"] = USERID
    village["maps"][0]["timestamp"] = timestamp_now()
    village["privateState"]["dartsRandomSeed"] = abs(int((2**16 - 1) * random.random()))
    __saves[USERID] = village
    await save_session(USERID)
    print("Done.")
    return USERID


# ─── Sync access functions (in-memory reads) ───────────────────────────────

def all_saves_userid() -> list:
    return list(__saves.keys())

def all_userid() -> list:
    return list(__villages.keys()) + list(__saves.keys())

def save_info(USERID: str) -> dict:
    save = __saves[USERID]
    default_map = save["playerInfo"]["default_map"]
    empire_name = str(save["playerInfo"]["map_names"][default_map])
    xp = save["maps"][default_map]["xp"]
    level = save["maps"][default_map]["level"]
    return {"userid": USERID, "name": empire_name, "xp": xp, "level": level}

def all_saves_info() -> list:
    return [save_info(uid) for uid in __saves]

def session(USERID: str) -> dict | None:
    return __saves.get(USERID)

def neighbor_session(USERID: str) -> dict | None:
    if USERID in __saves:
        return __saves[USERID]
    return __villages.get(USERID)

def fb_friends_str(USERID: str) -> list:
    friends = []
    for key in __villages:
        vill = __villages[key]
        if vill["playerInfo"]["pid"] in (
            Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1,
            Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2,
            Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3,
        ):
            continue
        frie = {"uid": vill["playerInfo"]["pid"]}
        frie["pic_square"] = vill["playerInfo"].get("pic") or "/img/profile/1025.png"
        friends.append(frie)
    for key in __saves:
        vill = __saves[key]
        if vill["playerInfo"]["pid"] == USERID:
            continue
        frie = {"uid": vill["playerInfo"]["pid"]}
        frie["pic_square"] = vill["playerInfo"].get("pic") or "/img/profile/1025.png"
        friends.append(frie)
    return friends

def neighbors(USERID: str) -> list:
    result = []
    for key in __villages:
        vill = __villages[key]
        if vill["playerInfo"]["pid"] in (
            Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1,
            Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2,
            Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3,
        ):
            continue
        neigh = dict(vill["playerInfo"])
        neigh["coins"] = vill["maps"][0]["coins"]
        neigh["xp"] = vill["maps"][0]["xp"]
        neigh["level"] = vill["maps"][0]["level"]
        neigh["stone"] = vill["maps"][0]["stone"]
        neigh["wood"] = vill["maps"][0]["wood"]
        neigh["food"] = vill["maps"][0]["food"]
        result.append(neigh)
    for key in __saves:
        vill = __saves[key]
        if vill["playerInfo"]["pid"] == USERID:
            continue
        neigh = dict(vill["playerInfo"])
        neigh["coins"] = vill["maps"][0]["coins"]
        neigh["xp"] = vill["maps"][0]["xp"]
        neigh["level"] = vill["maps"][0]["level"]
        neigh["stone"] = vill["maps"][0]["stone"]
        neigh["wood"] = vill["maps"][0]["wood"]
        neigh["food"] = vill["maps"][0]["food"]
        result.append(neigh)
    return result

def is_valid_village(save: dict) -> bool:
    if "playerInfo" not in save or "maps" not in save or "privateState" not in save:
        return False
    for m in save["maps"]:
        if "oil" in m or "steel" in m:
            return False
        if "stone" not in m or "food" not in m:
            return False
        if "items" not in m or not isinstance(m["items"], list):
            return False
    return True


# ─── Async persistence ─────────────────────────────────────────────────────

async def save_session(USERID: str):
    file = f"{USERID}.save.json"
    print(f" * Saving village at {file}... ", end="")
    village = session(USERID)
    async with aiofiles.open(os.path.join(SAVES_DIR, file), "w") as f:
        await f.write(json.dumps(village, indent=4))
    print("Done.")

async def backup_session(USERID: str):
    pass  # TODO
