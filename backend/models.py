"""Database models for the mini-games platform — vanilla SQLAlchemy."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, JSON,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


# ─── User ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    village_ids = Column(JSON, default=list)

    def __repr__(self):
        return f"<User {self.username}>"


# ─── Game ───────────────────────────────────────────────────────────────────

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(10), default="🎮")
    min_players = Column(Integer, default=2)
    max_players = Column(Integer, default=2)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("GameSession", back_populates="game")
    leaderboard = relationship("LeaderboardEntry", back_populates="game")

    def __repr__(self):
        return f"<Game {self.name}>"


# ─── GameSession ────────────────────────────────────────────────────────────

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    state_json = Column(JSON, default=dict)
    status = Column(String(20), default="waiting")
    room_code = Column(String(20), unique=True, nullable=False, index=True)
    is_private = Column(Boolean, default=False)
    password_hash = Column(String(256), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game = relationship("Game", back_populates="sessions")
    player1 = relationship("User", foreign_keys=[player1_id])
    player2 = relationship("User", foreign_keys=[player2_id])
    winner = relationship("User", foreign_keys=[winner_id])

    def __repr__(self):
        return f"<GameSession {self.room_code} ({self.status})>"


# ─── Leaderboard ────────────────────────────────────────────────────────────

class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"
    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_user_game"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    score = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    rating = Column(Integer, default=1200)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    game = relationship("Game", back_populates="leaderboard")

    @property
    def total_games(self):
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self):
        if self.total_games == 0:
            return 0.0
        return round(self.wins / self.total_games * 100, 1)


# ─── Chat ───────────────────────────────────────────────────────────────────

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=True)
    room_type = Column(String(20), default="group")
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="room", order_by="ChatMessage.created_at")
    members = relationship("ChatRoomMember", back_populates="room")
    creator = relationship("User", foreign_keys=[created_by])


class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_room_user"),)

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default="member")
    joined_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("ChatRoom", back_populates="members")
    user = relationship("User")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    room = relationship("ChatRoom", back_populates="messages")
    author = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "username": self.author.username if self.author else "Unknown",
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChatMute(Base):
    __tablename__ = "chat_mutes"
    __table_args__ = (UniqueConstraint("user_id", "muted_user_id", "room_id", name="uq_mute"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    muted_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatReport(Base):
    __tablename__ = "chat_reports"

    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
