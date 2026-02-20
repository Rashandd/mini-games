"""Async game config — loads at startup, sync lookups after."""
import json
import os
import asyncio
import aiofiles
import jsonpatch

from config import settings

CONFIG_DIR = settings.CONFIG_DIR
CONFIG_PATCH_DIR = settings.CONFIG_PATCH_DIR
MODS_DIR = settings.MODS_DIR

__game_config: dict | None = None
items_dict_id_to_items_index: dict = {}
items_dict_subcat_functional_to_items_index: dict = {}
missions_dict_id_to_missions_index: dict = {}


async def load_game_config():
    """Load and patch the game config at startup (async I/O)."""
    global __game_config, items_dict_id_to_items_index
    global items_dict_subcat_functional_to_items_index, missions_dict_id_to_missions_index

    config_path = os.path.join(CONFIG_DIR, "game_config_20120826.json")
    async with aiofiles.open(config_path, "r", encoding="utf-8") as f:
        __game_config = json.loads(await f.read())

    print(" [+] Applying config patches and mods...")

    # Apply patches
    patch_files = await asyncio.to_thread(os.listdir, CONFIG_PATCH_DIR)
    for patch_file in sorted(patch_files):
        if not patch_file.endswith(".json"):
            continue
        fpath = os.path.join(CONFIG_PATCH_DIR, patch_file)
        async with aiofiles.open(fpath, "r") as f:
            patch = json.loads(await f.read())
        jsonpatch.apply_patch(__game_config, patch, in_place=True)
        print(f" * Patch applied: {patch_file.replace('.json', '')}")

    # Apply mods
    mods_txt = os.path.join(MODS_DIR, "mods.txt")
    if os.path.exists(mods_txt):
        async with aiofiles.open(mods_txt, "r") as f:
            lines = (await f.read()).splitlines()
        for line in lines:
            mod = line.strip()
            if mod.startswith("#") or not mod:
                continue
            mod_path = os.path.join(MODS_DIR, f"{mod.replace('.json', '')}.json")
            if os.path.exists(mod_path):
                async with aiofiles.open(mod_path, "r") as f:
                    patch = json.loads(await f.read())
                jsonpatch.apply_patch(__game_config, patch, in_place=True)
                print(f" * Mod applied: {mod}")

    _remove_duplicate_items()
    _build_indexes()


def _remove_duplicate_items():
    indexes = {}
    items = __game_config["items"]
    num_dup = 0
    while True:
        dup = False
        for idx, item in enumerate(items):
            if item["id"] in indexes:
                del items[indexes[item["id"]]]
                indexes.clear()
                dup = True
                num_dup += 1
                break
            indexes[item["id"]] = idx
        if not dup:
            break
    if num_dup:
        print(f" * Removed {num_dup} duplicate items from config patches")


def _build_indexes():
    global items_dict_id_to_items_index, items_dict_subcat_functional_to_items_index
    global missions_dict_id_to_missions_index
    items_dict_id_to_items_index = {
        int(item["id"]): i for i, item in enumerate(__game_config["items"])
    }
    items_dict_subcat_functional_to_items_index = {
        int(item["subcat_functional"]): i for i, item in enumerate(__game_config["items"])
    }
    missions_dict_id_to_missions_index = {
        int(m["id"]): i for i, m in enumerate(__game_config["missions"])
    }


# ─── Sync lookups (in-memory after startup) ────────────────────────────────

def get_game_config() -> dict:
    return __game_config

def game_config() -> dict:
    return __game_config

def get_xp_from_level(level: int) -> int:
    return __game_config["levels"][int(level)]["exp_required"]

def get_level_from_xp(xp: int) -> int:
    for i, lvl in enumerate(__game_config["levels"]):
        if lvl["exp_required"] > int(xp):
            return i
    return 0

def get_item_from_id(id: int) -> dict | None:
    idx = items_dict_id_to_items_index.get(int(id))
    return __game_config["items"][idx] if idx is not None else None

def get_attribute_from_item_id(id: int, attribute_name: str) -> str | None:
    item = get_item_from_id(id)
    return item.get(attribute_name) if item else None

def get_name_from_item_id(id: int) -> str | None:
    return get_attribute_from_item_id(id, "name")

def get_item_from_subcat_functional(subcat_functional: int) -> dict | None:
    idx = items_dict_subcat_functional_to_items_index.get(int(subcat_functional))
    return __game_config["items"][idx] if idx is not None else None

def get_mission_from_id(id: int) -> dict | None:
    idx = missions_dict_id_to_missions_index.get(int(id))
    return __game_config["missions"][idx] if idx is not None else None

def get_attribute_from_mission_id(id: int, attribute_name: str) -> str | None:
    mission = get_mission_from_id(id)
    return mission.get(attribute_name) if mission else None
