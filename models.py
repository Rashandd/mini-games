"""Database models for the mini-games platform."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from db import db


class Game(db.Model):
    """A game type (chess, backgammon, etc.)."""
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    icon = db.Column(db.String(10), default='🎮')
    min_players = db.Column(db.Integer, default=2)
    max_players = db.Column(db.Integer, default=2)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship('GameSession', backref='game', lazy='dynamic')
    leaderboard = db.relationship('LeaderboardEntry', backref='game', lazy='dynamic')

    def __repr__(self):
        return f'<Game {self.name}>'


class GameSession(db.Model):
    """An individual game match between players."""
    __tablename__ = 'game_sessions'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    state_json = db.Column(db.JSON, default=dict)
    status = db.Column(db.String(20), default='waiting')  # waiting, playing, finished, abandoned
    room_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    is_private = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(256), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    player1 = db.relationship('User', foreign_keys=[player1_id], backref='games_as_p1')
    player2 = db.relationship('User', foreign_keys=[player2_id], backref='games_as_p2')
    winner = db.relationship('User', foreign_keys=[winner_id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return True
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<GameSession {self.room_code} ({self.status})>'


class LeaderboardEntry(db.Model):
    """Per-game stats for a user."""
    __tablename__ = 'leaderboard_entries'
    __table_args__ = (db.UniqueConstraint('user_id', 'game_id', name='uq_user_game'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    score = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    rating = db.Column(db.Integer, default=1200)  # ELO
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='leaderboard_entries')

    @property
    def total_games(self):
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self):
        if self.total_games == 0:
            return 0.0
        return round(self.wins / self.total_games * 100, 1)

    def __repr__(self):
        return f'<LeaderboardEntry user={self.user_id} game={self.game_id} rating={self.rating}>'


class ChatRoom(db.Model):
    """A chat room (DM, group, or game lobby)."""
    __tablename__ = 'chat_rooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    room_type = db.Column(db.String(20), default='group')  # dm, group, lobby
    game_session_id = db.Column(db.Integer, db.ForeignKey('game_sessions.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('ChatMessage', backref='room', lazy='dynamic', order_by='ChatMessage.created_at')
    members = db.relationship('ChatRoomMember', backref='room', lazy='dynamic')
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<ChatRoom {self.name} ({self.room_type})>'


class ChatRoomMember(db.Model):
    """Membership of a user in a chat room."""
    __tablename__ = 'chat_room_members'
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='uq_room_user'),)

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.String(20), default='member')  # owner, admin, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='chat_memberships')


class ChatMessage(db.Model):
    """A single chat message."""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    author = db.relationship('User', backref='chat_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'username': self.author.username if self.author else 'Unknown',
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<ChatMessage {self.id} in room {self.room_id}>'


class ChatMute(db.Model):
    """A user muting another user in a chat room."""
    __tablename__ = 'chat_mutes'
    __table_args__ = (db.UniqueConstraint('user_id', 'muted_user_id', 'room_id', name='uq_mute'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    muted_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=True)  # null = global mute
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    muted_user = db.relationship('User', foreign_keys=[muted_user_id])


class ChatReport(db.Model):
    """A report filed against a user in chat."""
    __tablename__ = 'chat_reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reporter = db.relationship('User', foreign_keys=[reporter_id])
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])
