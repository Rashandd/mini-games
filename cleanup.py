"""Background task: clean up stale lobby sessions after 120 seconds of inactivity."""
from datetime import datetime, timedelta
from db import db
from models import GameSession


def start_cleanup_task(socketio):
    """Start a background task that cleans up empty lobbies every 30 seconds."""

    def cleanup_loop():
        import eventlet
        while True:
            eventlet.sleep(30)
            try:
                with socketio.server.eio.get_session('') if False else db.session.begin():
                    pass
            except Exception:
                pass

            try:
                cutoff = datetime.utcnow() - timedelta(seconds=120)
                stale = GameSession.query.filter(
                    GameSession.status == 'waiting',
                    GameSession.last_activity < cutoff
                ).all()

                for gs in stale:
                    room_code = gs.room_code
                    db.session.delete(gs)
                    socketio.emit('lobby_removed', {'room_code': room_code})

                if stale:
                    db.session.commit()
                    print(f' [Cleanup] Removed {len(stale)} stale lobby(s)')
            except Exception as e:
                print(f' [Cleanup] Error: {e}')
                db.session.rollback()

    socketio.start_background_task(cleanup_loop)
