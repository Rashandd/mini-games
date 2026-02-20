"""SE player info — pure dict assembly, no I/O."""
from social_empires.sessions import session, neighbor_session, neighbors
from social_empires.engine import timestamp_now


def get_player_info(USERID):
    ts_now = timestamp_now()
    session(USERID)["playerInfo"]["last_logged_in"] = ts_now
    return {
        "result": "ok",
        "processed_errors": 0,
        "timestamp": ts_now,
        "playerInfo": session(USERID)["playerInfo"],
        "map": session(USERID)["maps"][0],
        "privateState": session(USERID)["privateState"],
        "neighbors": neighbors(USERID),
    }


def get_neighbor_info(userid, map_number):
    return {
        "result": "ok",
        "processed_errors": 0,
        "timestamp": timestamp_now(),
        "playerInfo": neighbor_session(userid)["playerInfo"],
        "map": neighbor_session(userid)["maps"][map_number],
        "privateState": neighbor_session(userid)["privateState"],
        "neighbors": neighbors(userid),
    }
