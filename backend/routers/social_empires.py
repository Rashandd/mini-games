"""Social Empires routing — PHP-emulation endpoints."""
import json
import os

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, FileResponse

from config import settings
from social_empires.sessions import (
    session, all_saves_userid, all_saves_info,
    fb_friends_str, new_village, save_session,
)
from social_empires.get_player_info import get_player_info, get_neighbor_info
from social_empires.get_game_config import get_game_config
from social_empires.quests import get_quest_map
from social_empires.command import command

router = APIRouter(tags=["social_empires"])


@router.get("/get_player_info.php")
async def se_player_info(USERID: str):
    data = session(USERID)
    if not data:
        return JSONResponse({"error": "Village not found"}, status_code=404)
    return get_player_info(USERID)


@router.get("/get_neighbor_info.php")
async def se_neighbor_info(USERID: str, map: int = 0):
    return get_neighbor_info(USERID, map)


@router.get("/get_game_config.php")
async def se_game_config():
    return get_game_config()


@router.get("/get_quest_map.php")
async def se_quest_map(questid: int):
    result = await get_quest_map(questid)
    if result is None:
        return JSONResponse({"error": "Quest not found"}, status_code=404)
    return result


@router.post("/command.php")
async def se_command(request: Request, USERID: str):
    body = await request.body()
    data = json.loads(body)
    await command(USERID, data)
    return {"result": "ok"}


@router.get("/crossdomain.xml")
async def crossdomain():
    xml = '<?xml version="1.0"?>\n<cross-domain-policy>\n<allow-access-from domain="*"/>\n</cross-domain-policy>'
    return Response(content=xml, media_type="application/xml")


# ─── SE village management endpoints ───────────────────────────────────────

@router.get("/api/se/villages")
async def list_villages():
    return all_saves_info()


@router.post("/api/se/villages/new")
async def create_village():
    userid = await new_village()
    return {"userid": userid}


@router.get("/api/se/fb_friends")
async def se_fb_friends(USERID: str):
    return fb_friends_str(USERID)


@router.get("/api/se/server_time")
async def se_server_time():
    from social_empires.engine import timestamp_now
    return {"serverTime": timestamp_now()}


# ─── CDN-mimic routes (Flash SWF expects these paths) ─────────────────────

@router.get("/default01.static.socialpointgames.com/static/socialempires/{path:path}")
async def se_static_assets(path: str):
    """Serve Flash assets mimicking the original CDN URL structure."""
    full_path = os.path.join(settings.ASSETS_DIR, path)
    if not os.path.isfile(full_path):
        return JSONResponse({"error": "Not found"}, status_code=404)
    return FileResponse(full_path)


@router.api_route("/dynamic.flash1.dev.socialpoint.es/{path:path}", methods=["GET", "POST"])
async def se_dynamic_stub(path: str, request: Request):
    """Dynamic URL stub — route known PHP endpoints to real handlers, stub the rest."""
    # Extract query params
    params = dict(request.query_params)
    userid = params.get("USERID", "")

    if path.endswith("get_game_config.php"):
        return get_game_config()
    elif path.endswith("get_player_info.php") and userid:
        return get_player_info(userid)
    elif path.endswith("get_neighbor_info.php") and userid:
        map_id = int(params.get("map", 0))
        return get_neighbor_info(userid, map_id)
    elif path.endswith("command.php") and userid:
        body = await request.body()
        import json as _json
        data = _json.loads(body) if body else {}
        await command(userid, data)
        return {"result": "ok"}
    elif path.endswith("get_quest_map.php"):
        questid = int(params.get("questid", 0))
        result = await get_quest_map(questid)
        return result if result else {"result": "ok"}

    # Default stub for tracking and other non-critical calls
    return {"result": "ok"}
