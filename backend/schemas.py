"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ─── Auth ───────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


# ─── Games ──────────────────────────────────────────────────────────────────

class GameOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    icon: str
    min_players: int
    max_players: int

    class Config:
        from_attributes = True

class LobbyOut(BaseModel):
    room_code: str
    host: str
    is_private: bool
    age: str

class ActiveGameOut(BaseModel):
    room_code: str
    player1: str
    player2: str
    age: str


# ─── Leaderboard ────────────────────────────────────────────────────────────

class LeaderboardEntryOut(BaseModel):
    rank: int
    username: str
    user_id: int
    rating: int
    wins: int
    losses: int
    draws: int
    total: int
    win_rate: float

class GlobalLeaderboardEntryOut(BaseModel):
    rank: int
    username: str
    user_id: int
    total_score: int
    total_wins: int
    total_losses: int
    total_draws: int
    avg_rating: int


# ─── Chat ───────────────────────────────────────────────────────────────────

class RoomOut(BaseModel):
    id: int
    name: Optional[str] = None
    room_type: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    username: str
    content: str
    created_at: Optional[datetime] = None
