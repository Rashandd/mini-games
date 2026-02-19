"""SocketIO event handlers for real-time game and chat."""
import uuid
from datetime import datetime
from flask import session
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user

from db import db
from models import GameSession, Game, ChatRoom, ChatMessage, ChatRoomMember, ChatMute, ChatReport
from games import get_engine
from leaderboard import update_ratings

# Track online users
online_users = {}  # user_id -> {username, sid}


def register_events(socketio):
    """Register all SocketIO event handlers."""

    # --- Connection ---

    @socketio.on('connect')
    def on_connect():
        if current_user.is_authenticated:
            online_users[current_user.id] = {
                'username': current_user.username,
                'sid': session.get('sid', '')
            }
            emit('online_count', {'count': len(online_users)}, broadcast=True)

    @socketio.on('disconnect')
    def on_disconnect():
        if current_user.is_authenticated:
            online_users.pop(current_user.id, None)
            emit('online_count', {'count': len(online_users)}, broadcast=True)

    # --- Game Events ---

    @socketio.on('create_game')
    def on_create_game(data):
        if not current_user.is_authenticated:
            return emit('error', {'message': 'Not authenticated'})

        game_slug = data.get('game_slug')
        game = Game.query.filter_by(slug=game_slug).first()
        if not game:
            return emit('error', {'message': 'Unknown game'})

        engine = get_engine(game_slug)
        room_code = uuid.uuid4().hex[:8]

        is_private = data.get('is_private', False)
        password = data.get('password', '')

        gs = GameSession(
            game_id=game.id,
            player1_id=current_user.id,
            status='waiting',
            room_code=room_code,
            state_json=engine.init_state(),
            is_private=bool(is_private),
            last_activity=datetime.utcnow(),
        )
        if is_private and password:
            gs.set_password(password)

        db.session.add(gs)
        db.session.commit()

        join_room(room_code)
        emit('game_created', {
            'room_code': room_code,
            'game_slug': game_slug,
            'game_name': game.name,
            'player1': current_user.username,
            'is_private': gs.is_private,
        })

    @socketio.on('join_game')
    def on_join_game(data):
        if not current_user.is_authenticated:
            return emit('error', {'message': 'Not authenticated'})

        room_code = data.get('room_code')
        gs = GameSession.query.filter_by(room_code=room_code).first()
        if not gs:
            return emit('error', {'message': 'Game not found'})

        # Password check for private games
        if gs.is_private and gs.password_hash:
            password = data.get('password', '')
            if not gs.check_password(password):
                return emit('error', {'message': 'Wrong password'})

        if gs.status == 'waiting' and gs.player2_id is None and gs.player1_id != current_user.id:
            gs.player2_id = current_user.id
            gs.status = 'playing'
            gs.last_activity = datetime.utcnow()
            db.session.commit()

        join_room(room_code)

        game = Game.query.get(gs.game_id)
        p1 = gs.player1.username if gs.player1 else '?'
        p2 = gs.player2.username if gs.player2 else None

        emit('game_joined', {
            'room_code': room_code,
            'game_slug': game.slug,
            'game_name': game.name,
            'status': gs.status,
            'state': gs.state_json,
            'player1': p1,
            'player2': p2,
            'your_player': 1 if gs.player1_id == current_user.id else 2,
        }, room=room_code)

    @socketio.on('make_move')
    def on_make_move(data):
        if not current_user.is_authenticated:
            return emit('error', {'message': 'Not authenticated'})

        room_code = data.get('room_code')
        move = data.get('move', {})

        gs = GameSession.query.filter_by(room_code=room_code).first()
        if not gs or gs.status != 'playing':
            return emit('error', {'message': 'Game not active'})

        if current_user.id == gs.player1_id:
            player = 1
        elif current_user.id == gs.player2_id:
            player = 2
        else:
            return emit('error', {'message': 'You are not in this game'})

        game = Game.query.get(gs.game_id)
        engine = get_engine(game.slug)
        new_state, err = engine.make_move(gs.state_json, move, player)

        if err:
            return emit('move_error', {'message': err})

        gs.state_json = new_state
        gs.last_activity = datetime.utcnow()
        db.session.commit()

        result = {
            'room_code': room_code,
            'state': new_state,
            'move': move,
            'player': player,
        }

        if engine.is_game_over(new_state):
            winner = engine.get_winner(new_state)
            gs.status = 'finished'
            gs.ended_at = datetime.utcnow()

            if winner and winner != 0:
                gs.winner_id = gs.player1_id if winner == 1 else gs.player2_id
                loser_id = gs.player2_id if winner == 1 else gs.player1_id
                update_ratings(gs.winner_id, loser_id, gs.game_id)
            elif winner == 0:
                update_ratings(gs.player1_id, gs.player2_id, gs.game_id, draw=True)

            db.session.commit()
            result['game_over'] = True
            result['winner'] = winner
            p1_name = gs.player1.username if gs.player1 else '?'
            p2_name = gs.player2.username if gs.player2 else '?'
            if winner == 1:
                result['winner_name'] = p1_name
            elif winner == 2:
                result['winner_name'] = p2_name
            else:
                result['winner_name'] = 'Draw'

        emit('game_update', result, room=room_code)

    @socketio.on('resign')
    def on_resign(data):
        if not current_user.is_authenticated:
            return
        room_code = data.get('room_code')
        gs = GameSession.query.filter_by(room_code=room_code).first()
        if not gs or gs.status != 'playing':
            return

        if current_user.id == gs.player1_id:
            winner_id = gs.player2_id
            winner_num = 2
        elif current_user.id == gs.player2_id:
            winner_id = gs.player1_id
            winner_num = 1
        else:
            return

        gs.status = 'finished'
        gs.winner_id = winner_id
        gs.ended_at = datetime.utcnow()
        update_ratings(winner_id, current_user.id, gs.game_id)
        db.session.commit()

        emit('game_update', {
            'room_code': room_code,
            'state': gs.state_json,
            'game_over': True,
            'winner': winner_num,
            'winner_name': gs.winner.username if gs.winner else '?',
            'resigned': current_user.username,
        }, room=room_code)

    # --- Legacy Chat Events (game_room.html) ---

    @socketio.on('chat_join')
    def on_chat_join(data):
        if not current_user.is_authenticated:
            return
        room_id = data.get('room_id')
        room = ChatRoom.query.get(room_id)
        if not room:
            return emit('error', {'message': 'Chat room not found'})

        join_room(f'chat_{room_id}')

        existing = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
        if not existing:
            db.session.add(ChatRoomMember(room_id=room_id, user_id=current_user.id))
            db.session.commit()

        messages = ChatMessage.query.filter_by(room_id=room_id) \
            .order_by(ChatMessage.created_at.desc()).limit(50).all()
        messages.reverse()

        emit('chat_history', {
            'room_id': room_id,
            'messages': [m.to_dict() for m in messages],
        })

    @socketio.on('chat_send')
    def on_chat_send(data):
        if not current_user.is_authenticated:
            return
        room_id = data.get('room_id')
        content = data.get('content', '').strip()
        if not content or len(content) > 1000:
            return

        msg = ChatMessage(room_id=room_id, user_id=current_user.id, content=content)
        db.session.add(msg)
        db.session.commit()

        emit('chat_message', msg.to_dict(), room=f'chat_{room_id}')

    # --- Sidebar Chat Events ---

    @socketio.on('list_rooms')
    def on_list_rooms():
        if not current_user.is_authenticated:
            return
        memberships = ChatRoomMember.query.filter_by(user_id=current_user.id).all()
        room_ids = [m.room_id for m in memberships]
        rooms = ChatRoom.query.filter(ChatRoom.id.in_(room_ids)).all() if room_ids else []

        # Also show public groups the user isn't in yet
        public_groups = ChatRoom.query.filter_by(room_type='group').all()
        all_room_ids = set(room_ids)
        for pg in public_groups:
            if pg.id not in all_room_ids:
                rooms.append(pg)

        room_list = []
        for r in rooms:
            name = r.name or 'Chat'
            if r.room_type == 'dm':
                other = ChatRoomMember.query.filter(
                    ChatRoomMember.room_id == r.id,
                    ChatRoomMember.user_id != current_user.id
                ).first()
                if other and other.user:
                    name = other.user.username

            room_list.append({
                'id': r.id,
                'name': name,
                'type': r.room_type,
            })

        emit('room_list', {'rooms': room_list})

    @socketio.on('create_dm')
    def on_create_dm(data):
        if not current_user.is_authenticated:
            return
        target_id = data.get('target_user_id')
        if not target_id or target_id == current_user.id:
            return emit('error', {'message': 'Invalid user'})

        from auth import User
        target = User.query.get(target_id)
        if not target:
            return emit('error', {'message': 'User not found'})

        # Check if DM already exists
        my_rooms = db.session.query(ChatRoomMember.room_id).filter_by(user_id=current_user.id)
        their_rooms = db.session.query(ChatRoomMember.room_id).filter_by(user_id=target_id)
        dm_room = ChatRoom.query.filter(
            ChatRoom.room_type == 'dm',
            ChatRoom.id.in_(my_rooms),
            ChatRoom.id.in_(their_rooms)
        ).first()

        if dm_room:
            emit('dm_created', {'room_id': dm_room.id})
            return

        room = ChatRoom(
            name=f'{current_user.username} & {target.username}',
            room_type='dm',
            created_by=current_user.id
        )
        db.session.add(room)
        db.session.flush()
        db.session.add(ChatRoomMember(room_id=room.id, user_id=current_user.id, role='owner'))
        db.session.add(ChatRoomMember(room_id=room.id, user_id=target_id, role='member'))
        db.session.commit()

        emit('dm_created', {'room_id': room.id})

    @socketio.on('create_group')
    def on_create_group(data):
        if not current_user.is_authenticated:
            return
        name = data.get('name', '').strip()
        if not name:
            return emit('error', {'message': 'Group name required'})

        room = ChatRoom(name=name, room_type='group', created_by=current_user.id)
        db.session.add(room)
        db.session.flush()
        db.session.add(ChatRoomMember(room_id=room.id, user_id=current_user.id, role='owner'))
        db.session.commit()

        emit('group_created', {'room_id': room.id})

    @socketio.on('join_chat')
    def on_join_chat(data):
        if not current_user.is_authenticated:
            return
        room_id = data.get('room_id')
        room = ChatRoom.query.get(room_id)
        if not room:
            return

        join_room(f'chat_{room_id}')

        existing = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
        if not existing:
            db.session.add(ChatRoomMember(room_id=room_id, user_id=current_user.id))
            db.session.commit()

    @socketio.on('leave_chat')
    def on_leave_chat(data):
        room_id = data.get('room_id')
        leave_room(f'chat_{room_id}')

    @socketio.on('load_messages')
    def on_load_messages(data):
        if not current_user.is_authenticated:
            return
        room_id = data.get('room_id')
        messages = ChatMessage.query.filter_by(room_id=room_id) \
            .order_by(ChatMessage.created_at.desc()).limit(50).all()
        messages.reverse()

        emit('message_history', {
            'room_id': room_id,
            'messages': [m.to_dict() for m in messages],
        })

    @socketio.on('send_message')
    def on_send_message(data):
        if not current_user.is_authenticated:
            return
        room_id = data.get('room_id')
        content = data.get('content', '').strip()
        if not content or len(content) > 1000:
            return

        msg = ChatMessage(room_id=room_id, user_id=current_user.id, content=content)
        db.session.add(msg)
        db.session.commit()

        emit('new_message', msg.to_dict(), room=f'chat_{room_id}')

    @socketio.on('chat_leave')
    def on_chat_leave_room(data):
        if not current_user.is_authenticated:
            return
        room_id = data.get('room_id')
        membership = ChatRoomMember.query.filter_by(
            room_id=room_id, user_id=current_user.id
        ).first()
        if membership:
            db.session.delete(membership)
            db.session.commit()
        leave_room(f'chat_{room_id}')
        emit('left_room', {'room_id': room_id})

    @socketio.on('chat_mute')
    def on_chat_mute(data):
        if not current_user.is_authenticated:
            return
        muted_user_id = data.get('muted_user_id')
        room_id = data.get('room_id')
        if not muted_user_id:
            return

        existing = ChatMute.query.filter_by(
            user_id=current_user.id, muted_user_id=muted_user_id, room_id=room_id
        ).first()
        if not existing:
            mute = ChatMute(user_id=current_user.id, muted_user_id=muted_user_id, room_id=room_id)
            db.session.add(mute)
            db.session.commit()

        emit('mute_confirmed', {'muted_user_id': muted_user_id})

    @socketio.on('chat_report')
    def on_chat_report(data):
        if not current_user.is_authenticated:
            return
        reported_user_id = data.get('reported_user_id')
        room_id = data.get('room_id')
        reason = data.get('reason', '')
        if not reported_user_id:
            return

        report = ChatReport(
            reporter_id=current_user.id,
            reported_user_id=reported_user_id,
            room_id=room_id,
            reason=reason
        )
        db.session.add(report)
        db.session.commit()

        emit('report_confirmed', {'reported_user_id': reported_user_id})

    # --- Matchmaking ---

    @socketio.on('find_match')
    def on_find_match(data):
        """Quick match: find an open game or create one."""
        if not current_user.is_authenticated:
            return emit('error', {'message': 'Not authenticated'})

        game_slug = data.get('game_slug')
        game = Game.query.filter_by(slug=game_slug).first()
        if not game:
            return emit('error', {'message': 'Unknown game'})

        # Find waiting PUBLIC game
        waiting = GameSession.query.filter_by(
            game_id=game.id, status='waiting', is_private=False
        ).filter(GameSession.player1_id != current_user.id).first()

        if waiting:
            on_join_game({'room_code': waiting.room_code})
        else:
            on_create_game({'game_slug': game_slug})
