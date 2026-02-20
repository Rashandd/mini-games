"""Socket.IO event handlers for real-time game and chat (python-socketio ASGI)."""
import uuid
from datetime import datetime

import socketio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import async_session
from models import (
    User, Game, GameSession, ChatRoom, ChatMessage,
    ChatRoomMember, ChatMute, ChatReport,
)
from services.leaderboard import update_elo
from services.games import get_engine
from auth import decode_token

# Create ASGI socket.io server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Track online users: sid -> {user_id, username}
online_users: dict[str, dict] = {}


def _get_user_from_sid(sid: str) -> dict | None:
    return online_users.get(sid)


# ─── Connection ─────────────────────────────────────────────────────────────

@sio.event
async def connect(sid, environ, auth):
    """Authenticate via JWT token in auth dict."""
    if not auth or "token" not in auth:
        raise socketio.exceptions.ConnectionRefusedError("No token")
    try:
        payload = decode_token(auth["token"])
        user_id = int(payload["sub"])
        username = payload["username"]
        online_users[sid] = {"user_id": user_id, "username": username}
        await sio.emit("online_count", {"count": len(online_users)})
    except Exception:
        raise socketio.exceptions.ConnectionRefusedError("Invalid token")


@sio.event
async def disconnect(sid):
    online_users.pop(sid, None)
    await sio.emit("online_count", {"count": len(online_users)})


# ─── Game Events ────────────────────────────────────────────────────────────

@sio.event
async def create_game(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return await sio.emit("error", {"message": "Not authenticated"}, to=sid)

    async with async_session() as db:
        game_slug = data.get("game_slug")
        game = (await db.execute(select(Game).where(Game.slug == game_slug))).scalar_one_or_none()
        if not game:
            return await sio.emit("error", {"message": "Unknown game"}, to=sid)

        engine = get_engine(game_slug)
        room_code = uuid.uuid4().hex[:8]

        is_private = data.get("is_private", False)
        password = data.get("password", "")

        gs = GameSession(
            game_id=game.id,
            player1_id=user["user_id"],
            status="waiting",
            room_code=room_code,
            state_json=engine.init_state(),
            is_private=bool(is_private),
            last_activity=datetime.utcnow(),
        )
        if is_private and password:
            from werkzeug.security import generate_password_hash
            gs.password_hash = generate_password_hash(password)

        db.add(gs)
        await db.commit()

    sio.enter_room(sid, room_code)
    await sio.emit("game_created", {
        "room_code": room_code,
        "game_slug": game_slug,
        "game_name": game.name,
        "player1": user["username"],
        "is_private": bool(is_private),
    }, to=sid)


@sio.event
async def delete_game(sid, data):
    """Let the host delete their waiting room."""
    user = _get_user_from_sid(sid)
    if not user:
        return await sio.emit("error", {"message": "Not authenticated"}, to=sid)

    async with async_session() as db:
        room_code = data.get("room_code")
        result = await db.execute(
            select(GameSession).where(GameSession.room_code == room_code)
        )
        gs = result.scalar_one_or_none()
        if not gs:
            return await sio.emit("error", {"message": "Room not found"}, to=sid)
        if gs.player1_id != user["user_id"]:
            return await sio.emit("error", {"message": "Only the host can delete"}, to=sid)
        if gs.status != "waiting":
            return await sio.emit("error", {"message": "Can only delete waiting rooms"}, to=sid)

        await db.delete(gs)
        await db.commit()

    await sio.emit("room_deleted", {"room_code": room_code}, to=sid)
    sio.leave_room(sid, room_code)


@sio.event
async def join_game(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return await sio.emit("error", {"message": "Not authenticated"}, to=sid)

    async with async_session() as db:
        room_code = data.get("room_code")
        result = await db.execute(
            select(GameSession)
            .options(selectinload(GameSession.player1), selectinload(GameSession.player2))
            .where(GameSession.room_code == room_code)
        )
        gs = result.scalar_one_or_none()
        if not gs:
            return await sio.emit("error", {"message": "Game not found"}, to=sid)

        # Password check
        if gs.is_private and gs.password_hash:
            password = data.get("password", "")
            from werkzeug.security import check_password_hash
            if not check_password_hash(gs.password_hash, password):
                return await sio.emit("error", {"message": "Wrong password"}, to=sid)

        # Validate join conditions
        if gs.player1_id == user["user_id"]:
            return await sio.emit("error", {"message": "You cannot join your own game"}, to=sid)
        if gs.status != "waiting":
            return await sio.emit("error", {"message": "Game is already in progress"}, to=sid)
        if gs.player2_id is not None:
            return await sio.emit("error", {"message": "Game is full"}, to=sid)

        # Assign player 2 and start the game
        gs.player2_id = user["user_id"]
        gs.status = "playing"
        gs.last_activity = datetime.utcnow()
        await db.commit()
        await db.refresh(gs, ["player1", "player2"])

        game = (await db.execute(select(Game).where(Game.id == gs.game_id))).scalar_one()
        p1 = gs.player1.username if gs.player1 else "?"
        p2 = gs.player2.username if gs.player2 else "?"

        # Join the socket room
        sio.enter_room(sid, room_code)

        # Emit to player 2 (the joiner) — full state so they can render
        await sio.emit("game_joined", {
            "room_code": room_code,
            "game_slug": game.slug,
            "game_name": game.name,
            "status": "playing",
            "state": gs.state_json,
            "player1": p1,
            "player2": p2,
            "your_player": 2,
        }, to=sid)

        # Emit to player 1 (the host) — only the fields that changed
        # This prevents overwriting yourPlayer which was set in game_created
        await sio.emit("game_started", {
            "room_code": room_code,
            "status": "playing",
            "state": gs.state_json,
            "player2": p2,
        }, room=room_code, skip_sid=sid)


@sio.event
async def make_move(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return await sio.emit("error", {"message": "Not authenticated"}, to=sid)

    async with async_session() as db:
        room_code = data.get("room_code")
        move = data.get("move", {})

        result = await db.execute(
            select(GameSession)
            .options(selectinload(GameSession.player1), selectinload(GameSession.player2), selectinload(GameSession.winner))
            .where(GameSession.room_code == room_code)
        )
        gs = result.scalar_one_or_none()
        if not gs or gs.status != "playing":
            return await sio.emit("error", {"message": "Game not active"}, to=sid)

        if user["user_id"] == gs.player1_id:
            player = 1
        elif user["user_id"] == gs.player2_id:
            player = 2
        else:
            return await sio.emit("error", {"message": "You are not in this game"}, to=sid)

        game = (await db.execute(select(Game).where(Game.id == gs.game_id))).scalar_one()
        engine = get_engine(game.slug)
        new_state, err = engine.make_move(gs.state_json, move, player)

        if err:
            return await sio.emit("move_error", {"message": err}, to=sid)

        gs.state_json = new_state
        gs.last_activity = datetime.utcnow()

        result_data = {
            "room_code": room_code,
            "state": new_state,
            "move": move,
            "player": player,
        }

        if engine.is_game_over(new_state):
            winner = engine.get_winner(new_state)
            gs.status = "finished"
            gs.ended_at = datetime.utcnow()

            if winner and winner != 0:
                gs.winner_id = gs.player1_id if winner == 1 else gs.player2_id
                loser_id = gs.player2_id if winner == 1 else gs.player1_id
                await update_elo(db, gs.game_id, gs.winner_id, loser_id)
            elif winner == 0:
                await update_elo(db, gs.game_id, gs.player1_id, gs.player2_id, is_draw=True)

            result_data["game_over"] = True
            result_data["winner"] = winner
            p1_name = gs.player1.username if gs.player1 else "?"
            p2_name = gs.player2.username if gs.player2 else "?"
            if winner == 1:
                result_data["winner_name"] = p1_name
            elif winner == 2:
                result_data["winner_name"] = p2_name
            else:
                result_data["winner_name"] = "Draw"

        await db.commit()
        await sio.emit("game_update", result_data, room=room_code)


@sio.event
async def resign(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return

    async with async_session() as db:
        room_code = data.get("room_code")
        result = await db.execute(
            select(GameSession)
            .options(selectinload(GameSession.winner))
            .where(GameSession.room_code == room_code)
        )
        gs = result.scalar_one_or_none()
        if not gs or gs.status != "playing":
            return

        if user["user_id"] == gs.player1_id:
            winner_id = gs.player2_id
            winner_num = 2
        elif user["user_id"] == gs.player2_id:
            winner_id = gs.player1_id
            winner_num = 1
        else:
            return

        gs.status = "finished"
        gs.winner_id = winner_id
        gs.ended_at = datetime.utcnow()
        await update_elo(db, gs.game_id, winner_id, user["user_id"])
        await db.commit()

        winner_user = (await db.execute(select(User).where(User.id == winner_id))).scalar_one_or_none()
        await sio.emit("game_update", {
            "room_code": room_code,
            "state": gs.state_json,
            "game_over": True,
            "winner": winner_num,
            "winner_name": winner_user.username if winner_user else "?",
            "resigned": user["username"],
        }, room=room_code)


# ─── Chat Events ────────────────────────────────────────────────────────────

@sio.event
async def list_rooms(sid):
    user = _get_user_from_sid(sid)
    if not user:
        return

    async with async_session() as db:
        result = await db.execute(
            select(ChatRoomMember.room_id).where(ChatRoomMember.user_id == user["user_id"])
        )
        room_ids = [r[0] for r in result.all()]
        rooms = []
        if room_ids:
            result = await db.execute(select(ChatRoom).where(ChatRoom.id.in_(room_ids)))
            rooms = list(result.scalars().all())

        # Public groups user isn't in
        result = await db.execute(select(ChatRoom).where(ChatRoom.room_type == "group"))
        for pg in result.scalars().all():
            if pg.id not in set(room_ids):
                rooms.append(pg)

        room_list = []
        for r in rooms:
            name = r.name or "Chat"
            if r.room_type == "dm":
                result = await db.execute(
                    select(ChatRoomMember)
                    .options(selectinload(ChatRoomMember.user))
                    .where(ChatRoomMember.room_id == r.id, ChatRoomMember.user_id != user["user_id"])
                )
                other = result.scalar_one_or_none()
                if other and other.user:
                    name = other.user.username

            room_list.append({"id": r.id, "name": name, "type": r.room_type})

        await sio.emit("room_list", {"rooms": room_list}, to=sid)


@sio.event
async def create_dm(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return

    target_id = data.get("target_user_id")
    if not target_id or target_id == user["user_id"]:
        return await sio.emit("error", {"message": "Invalid user"}, to=sid)

    async with async_session() as db:
        target = (await db.execute(select(User).where(User.id == target_id))).scalar_one_or_none()
        if not target:
            return await sio.emit("error", {"message": "User not found"}, to=sid)

        # Check existing DM
        my_rooms = select(ChatRoomMember.room_id).where(ChatRoomMember.user_id == user["user_id"])
        their_rooms = select(ChatRoomMember.room_id).where(ChatRoomMember.user_id == target_id)
        result = await db.execute(
            select(ChatRoom).where(
                ChatRoom.room_type == "dm",
                ChatRoom.id.in_(my_rooms),
                ChatRoom.id.in_(their_rooms),
            )
        )
        dm_room = result.scalar_one_or_none()
        if dm_room:
            return await sio.emit("dm_created", {"room_id": dm_room.id}, to=sid)

        room = ChatRoom(
            name=f'{user["username"]} & {target.username}',
            room_type="dm",
            created_by=user["user_id"],
        )
        db.add(room)
        await db.flush()
        db.add(ChatRoomMember(room_id=room.id, user_id=user["user_id"], role="owner"))
        db.add(ChatRoomMember(room_id=room.id, user_id=target_id, role="member"))
        await db.commit()
        await sio.emit("dm_created", {"room_id": room.id}, to=sid)


@sio.event
async def create_group(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return

    name = data.get("name", "").strip()
    if not name:
        return await sio.emit("error", {"message": "Group name required"}, to=sid)

    async with async_session() as db:
        room = ChatRoom(name=name, room_type="group", created_by=user["user_id"])
        db.add(room)
        await db.flush()
        db.add(ChatRoomMember(room_id=room.id, user_id=user["user_id"], role="owner"))
        await db.commit()
        await sio.emit("group_created", {"room_id": room.id}, to=sid)


@sio.event
async def join_chat(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return

    room_id = data.get("room_id")
    sio.enter_room(sid, f"chat_{room_id}")

    async with async_session() as db:
        existing = (await db.execute(
            select(ChatRoomMember).where(
                ChatRoomMember.room_id == room_id,
                ChatRoomMember.user_id == user["user_id"],
            )
        )).scalar_one_or_none()
        if not existing:
            db.add(ChatRoomMember(room_id=room_id, user_id=user["user_id"]))
            await db.commit()


@sio.event
async def leave_chat(sid, data):
    room_id = data.get("room_id")
    sio.leave_room(sid, f"chat_{room_id}")


@sio.event
async def load_messages(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return

    room_id = data.get("room_id")
    async with async_session() as db:
        result = await db.execute(
            select(ChatMessage)
            .options(selectinload(ChatMessage.author))
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(50)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        await sio.emit("message_history", {
            "room_id": room_id,
            "messages": [m.to_dict() for m in messages],
        }, to=sid)


@sio.event
async def send_message(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return

    room_id = data.get("room_id")
    content = data.get("content", "").strip()
    if not content or len(content) > 1000:
        return

    async with async_session() as db:
        msg = ChatMessage(room_id=room_id, user_id=user["user_id"], content=content)
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        await sio.emit("new_message", {
            "id": msg.id,
            "room_id": room_id,
            "user_id": user["user_id"],
            "username": user["username"],
            "content": content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }, room=f"chat_{room_id}")


@sio.event
async def chat_mute(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return

    muted_user_id = data.get("muted_user_id")
    room_id = data.get("room_id")
    if not muted_user_id:
        return

    async with async_session() as db:
        existing = (await db.execute(
            select(ChatMute).where(
                ChatMute.user_id == user["user_id"],
                ChatMute.muted_user_id == muted_user_id,
                ChatMute.room_id == room_id,
            )
        )).scalar_one_or_none()
        if not existing:
            db.add(ChatMute(user_id=user["user_id"], muted_user_id=muted_user_id, room_id=room_id))
            await db.commit()
        await sio.emit("mute_confirmed", {"muted_user_id": muted_user_id}, to=sid)


@sio.event
async def chat_report(sid, data):
    user = _get_user_from_sid(sid)
    if not user:
        return

    reported_user_id = data.get("reported_user_id")
    room_id = data.get("room_id")
    reason = data.get("reason", "")
    if not reported_user_id:
        return

    async with async_session() as db:
        db.add(ChatReport(
            reporter_id=user["user_id"],
            reported_user_id=reported_user_id,
            room_id=room_id,
            reason=reason,
        ))
        await db.commit()
        await sio.emit("report_confirmed", {"reported_user_id": reported_user_id}, to=sid)


@sio.event
async def find_match(sid, data):
    """Quick match: find open game or create one."""
    user = _get_user_from_sid(sid)
    if not user:
        return await sio.emit("error", {"message": "Not authenticated"}, to=sid)

    async with async_session() as db:
        game_slug = data.get("game_slug")
        game = (await db.execute(select(Game).where(Game.slug == game_slug))).scalar_one_or_none()
        if not game:
            return await sio.emit("error", {"message": "Unknown game"}, to=sid)

        waiting = (await db.execute(
            select(GameSession)
            .options(selectinload(GameSession.player1))
            .where(
                GameSession.game_id == game.id,
                GameSession.status == "waiting",
                GameSession.is_private == False,  # noqa: E712
                GameSession.player1_id != user["user_id"],
            )
        )).scalar_one_or_none()

    if waiting:
        # Inline join logic so socket room is handled properly
        async with async_session() as db:
            result = await db.execute(
                select(GameSession)
                .options(selectinload(GameSession.player1), selectinload(GameSession.player2))
                .where(GameSession.room_code == waiting.room_code)
            )
            gs = result.scalar_one_or_none()
            if not gs or gs.status != "waiting" or gs.player2_id is not None:
                # Race condition — game was taken, create a new one
                await create_game(sid, {"game_slug": game_slug})
                return

            gs.player2_id = user["user_id"]
            gs.status = "playing"
            gs.last_activity = datetime.utcnow()
            await db.commit()
            await db.refresh(gs, ["player1", "player2"])

            p1 = gs.player1.username if gs.player1 else "?"
            p2 = gs.player2.username if gs.player2 else "?"

            sio.enter_room(sid, waiting.room_code)

            await sio.emit("game_joined", {
                "room_code": waiting.room_code,
                "game_slug": game_slug,
                "game_name": game.name,
                "status": "playing",
                "state": gs.state_json,
                "player1": p1,
                "player2": p2,
                "your_player": 2,
            }, to=sid)

            await sio.emit("game_started", {
                "room_code": waiting.room_code,
                "status": "playing",
                "state": gs.state_json,
                "player2": p2,
            }, room=waiting.room_code, skip_sid=sid)
    else:
        await create_game(sid, {"game_slug": game_slug})
