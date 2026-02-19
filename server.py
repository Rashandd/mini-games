import os
from flask import Flask, render_template, send_from_directory, request, redirect, session, flash, jsonify, Response
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO
from bundle import ASSETS_DIR, STUB_DIR

# App setup
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'minigames-secret-key-change-me')

# Database & Auth
from db import init_db
from auth import login_manager, register_user, authenticate_user

init_db(app)
login_manager.init_app(app)

# SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

from socket_events import register_events
register_events(socketio)

# Import models (after db init)
from models import Game, GameSession, ChatRoom, ChatRoomMember

# Social Empires backend modules
from sessions import load_saved_villages, all_saves_info, save_info as se_save_info, new_village as se_new_village
from sessions import session as se_session, fb_friends_str
from get_player_info import get_player_info as se_get_player_info, get_neighbor_info as se_get_neighbor_info
from command import command as se_command
from get_game_config import get_game_config
from quests import get_quest_map
from version import version_name as SE_VERSION
from engine import timestamp_now

# Initialize SE villages on startup
print(" [+] Loading Social Empires villages...")
load_saved_villages()

host = '127.0.0.1'
port = 5050


##########
# ROUTES #
##########

# --- Auth ---

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect("/home")
    return redirect("/login")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect("/home")

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user, error = authenticate_user(username, password)
        if error:
            flash(error, 'error')
            return redirect("/login")
        login_user(user)
        return redirect("/home")

    return render_template("login.html", version="Mini Games")


@app.route("/register", methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    password2 = request.form.get('password2', '')

    if password != password2:
        flash("Passwords do not match.", 'error')
        return redirect("/login?register")

    user, error = register_user(username, password)
    if error:
        flash(error, 'error')
        return redirect("/login?register")

    flash("Account created! You can now sign in.", 'success')
    return redirect("/login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Signed out.", 'info')
    return redirect("/login")


# --- Home (Game Select) ---

@app.route("/home")
@login_required
def home():
    games = Game.query.filter_by(is_active=True).all()
    return render_template("home.html", games=games)


# --- Social Empires Backend (real PHP emulation) ---

@app.route("/get_player_info.php")
def se_player_info_route():
    USERID = request.args.get('user_id') or request.args.get('fb_sig_user', '')
    if not USERID or not se_session(USERID):
        return jsonify({"result": "error", "message": "No village found"}), 404
    return jsonify(se_get_player_info(USERID))


@app.route("/get_neighbor_info.php")
def se_neighbor_info_route():
    USERID = request.args.get('user_id', '')
    map_number = int(request.args.get('map', '0'))
    try:
        return jsonify(se_get_neighbor_info(USERID, map_number))
    except Exception:
        return jsonify({"result": "error"}), 404


@app.route("/command.php", methods=['POST'])
def se_command_route():
    USERID = request.form.get('user_id') or request.args.get('user_id', '')
    if not USERID or not se_session(USERID):
        return jsonify({"result": "error"}), 404
    data = request.get_data(as_text=True)
    result = se_command(USERID, data)
    return jsonify(result) if result else jsonify({"result": "ok"})


@app.route("/get_game_config.php")
def se_game_config_route():
    return jsonify(get_game_config())


@app.route("/get_quest_map.php")
def se_quest_map_route():
    questid = request.args.get('questid', '')
    data, code = get_quest_map(questid)
    if code != 200:
        return Response("", status=404)
    return jsonify(data)


@app.route("/crossdomain.xml")
def crossdomain():
    return send_from_directory(STUB_DIR, 'crossdomain.xml')


# SE Flash asset routes (mimic the original CDN structure)
@app.route("/default01.static.socialpointgames.com/static/socialempires/<path:path>")
def se_static_assets(path):
    return send_from_directory(ASSETS_DIR, path)


@app.route("/dynamic.flash1.dev.socialpoint.es/<path:path>")
def se_dynamic_stub(path):
    """Dynamic URL stub — redirect API calls to local endpoints."""
    return jsonify({"result": "ok"})


# SE pages
@app.route("/select", methods=['GET'])
@login_required
def se_select_village():
    saves = all_saves_info()
    return render_template("select_village.html",
        saves_info=saves,
        version=SE_VERSION,
        current_user=current_user)


@app.route("/select_village", methods=['POST'])
@login_required
def se_select_village_post():
    USERID = request.form.get('USERID', '')
    GAMEVERSION = request.form.get('GAMEVERSION', 'SocialEmpires0926bsec.swf')
    if not USERID or not se_session(USERID):
        flash("Invalid village.", 'error')
        return redirect("/select")
    return redirect(f"/play/{USERID}?version={GAMEVERSION}")


@app.route("/new.html")
@login_required
def se_new_village_page():
    se_new_village()
    flash("New empire created!", 'success')
    return redirect("/select")


@app.route("/play/<USERID>")
@login_required
def se_play(USERID):
    if not se_session(USERID):
        flash("Village not found.", 'error')
        return redirect("/select")
    info = se_save_info(USERID)
    friends = fb_friends_str(USERID)
    server_time = timestamp_now()
    GAMEVERSION = request.args.get('version', 'SocialEmpires0926bsec.swf')
    return render_template("play.html",
        save_info=info,
        friendsInfo=friends,
        serverTime=server_time,
        GAMEVERSION=GAMEVERSION,
        version=SE_VERSION)


# --- Game Routes ---

@app.route("/game/<slug>")
@login_required
def game_lobby(slug):
    game = Game.query.filter_by(slug=slug).first_or_404()

    # Social Empires: redirect to village selection
    if slug == 'social-empires':
        return redirect("/select")

    waiting = GameSession.query.filter_by(game_id=game.id, status='waiting').all()
    return render_template("game_room.html", game=game, room_code=None, waiting_games=waiting, chat_room_id=None)


@app.route("/game/<slug>/<room_code>")
@login_required
def game_room(slug, room_code):
    game = Game.query.filter_by(slug=slug).first_or_404()
    gs = GameSession.query.filter_by(room_code=room_code).first_or_404()

    # Create or get chat room for this game session
    from db import db
    chat_room = ChatRoom.query.filter_by(game_session_id=gs.id).first()
    if not chat_room:
        chat_room = ChatRoom(
            name=f"{game.name} — {room_code}",
            room_type='lobby',
            game_session_id=gs.id,
            created_by=current_user.id
        )
        db.session.add(chat_room)
        db.session.commit()

    return render_template("game_room.html", game=game, room_code=room_code, chat_room_id=chat_room.id)


# --- Leaderboard ---

@app.route("/leaderboard")
@login_required
def leaderboard_global():
    from leaderboard import get_global_leaderboard
    all_games = Game.query.filter_by(is_active=True).all()
    entries = get_global_leaderboard()
    return render_template("leaderboard.html", game=None, all_games=all_games, entries=entries)


@app.route("/leaderboard/<slug>")
@login_required
def leaderboard_game(slug):
    from leaderboard import get_leaderboard
    game = Game.query.filter_by(slug=slug).first_or_404()
    all_games = Game.query.filter_by(is_active=True).all()
    entries = get_leaderboard(slug)
    return render_template("leaderboard.html", game=game, all_games=all_games, entries=entries)


# --- Chat ---

@app.route("/chat")
@login_required
def chat_page():
    # Get rooms user is a member of, plus public rooms
    user_memberships = ChatRoomMember.query.filter_by(user_id=current_user.id).all()
    room_ids = [m.room_id for m in user_memberships]
    rooms = ChatRoom.query.filter(
        (ChatRoom.id.in_(room_ids)) | (ChatRoom.room_type == 'group')
    ).all()

    # Create a "General" room if none exist
    from db import db
    if not ChatRoom.query.filter_by(name='General').first():
        general = ChatRoom(name='General', room_type='group', created_by=current_user.id)
        db.session.add(general)
        db.session.commit()
        rooms = [general] + rooms

    active_room = rooms[0] if rooms else None
    return render_template("chat.html", rooms=rooms, active_room=active_room)


@app.route("/chat/create", methods=['POST'])
@login_required
def chat_create():
    from db import db
    name = request.form.get('room_name', '').strip()
    if not name:
        flash("Room name required.", 'error')
        return redirect("/chat")

    room = ChatRoom(name=name, room_type='group', created_by=current_user.id)
    db.session.add(room)
    db.session.flush()
    db.session.add(ChatRoomMember(room_id=room.id, user_id=current_user.id))
    db.session.commit()
    return redirect("/chat")


# --- Static files ---

@app.route("/js/<path:path>")
def js_files(path):
    return send_from_directory(os.path.join(TEMPLATES_DIR, "js"), path)


@app.route("/css/<path:path>")
def css_files(path):
    return send_from_directory(os.path.join(TEMPLATES_DIR, "css"), path)


@app.route("/img/<path:path>")
def img_files(path):
    return send_from_directory(os.path.join(TEMPLATES_DIR, "img"), path)


@app.route("/assets/<path:path>")
def asset_files(path):
    return send_from_directory(ASSETS_DIR, path)


# --- API (for future use) ---

@app.route("/api/games")
@login_required
def api_games():
    games = Game.query.filter_by(is_active=True).all()
    return jsonify([{
        'slug': g.slug, 'name': g.name, 'description': g.description,
        'icon': g.icon, 'min_players': g.min_players, 'max_players': g.max_players,
    } for g in games])


@app.route("/api/users/search")
@login_required
def api_user_search():
    from auth import User
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    users = User.query.filter(
        User.username.ilike(f'%{q}%'),
        User.id != current_user.id
    ).limit(10).all()
    return jsonify([{'id': u.id, 'username': u.username} for u in users])


@app.route("/api/lobbies/<slug>")
@login_required
def api_lobbies(slug):
    from datetime import datetime
    game = Game.query.filter_by(slug=slug).first()
    if not game:
        return jsonify([])
    waiting = GameSession.query.filter_by(
        game_id=game.id, status='waiting'
    ).order_by(GameSession.started_at.desc()).all()
    now = datetime.utcnow()
    result = []
    for gs in waiting:
        delta = (now - gs.started_at).total_seconds()
        if delta < 60:
            age = f'{int(delta)}s ago'
        elif delta < 3600:
            age = f'{int(delta/60)}m ago'
        else:
            age = f'{int(delta/3600)}h ago'
        result.append({
            'room_code': gs.room_code,
            'host': gs.player1.username if gs.player1 else '?',
            'is_private': gs.is_private,
            'age': age,
        })
    return jsonify(result)


########
# MAIN #
########

if __name__ == '__main__':
    from cleanup import start_cleanup_task
    start_cleanup_task(socketio)
    print(f" [+] Mini Games Platform running on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=False)
