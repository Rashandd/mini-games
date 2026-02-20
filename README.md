# ⚔️ Mini Games Platform

A multiplayer gaming platform featuring classic board games with real-time matchmaking, chat, leaderboards, and a fully playable **Social Empires** Flash preservation — all wrapped in a modern dark-themed UI.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Discord](https://img.shields.io/discord/984545703558783016?logo=discord&label=Discord&color=blue)](https://discord.gg/zW5gSbQJBw)

---

## 🎮 Games

| Game | Type | Description |
|------|------|-------------|
| ♟️ **Chess** | 1v1 | Full chess with legal move validation via `python-chess` |
| 🏁 **Checkers** | 1v1 | Classic checkers with king promotion |
| 🎲 **Backgammon** | 1v1 | Dice-based backgammon with bar and bearing off |
| ❌ **Tic-Tac-Toe** | 1v1 | Simple 3×3 grid game |
| ⚔️ **Social Empires** | Solo | Flash game preserved with [Ruffle](https://ruffle.rs/) emulator |
| 🏴‍☠️ **Wave Drifter** | Solo | Isometric pirate ship game — dodge and destroy the royal navy! |

## ✨ Features

- **Real-time multiplayer** — Socket.IO for instant game state sync
- **Matchmaking** — Create public/private rooms or quick-match
- **ELO leaderboards** — Per-game rankings with ELO rating system
- **Chat system** — DMs, group chats, mute, and report
- **JWT authentication** — Secure login/register with token-based auth
- **Social Empires** — Full Flash game preserved via Ruffle, with save management and village system
- **Modern UI** — Dark glassmorphism theme with micro-animations

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Zustand, Socket.IO Client, Axios |
| **Backend** | FastAPI, SQLAlchemy (async), python-socketio |
| **Database** | PostgreSQL (asyncpg) |
| **Flash** | Ruffle WebAssembly emulator (CDN) |
| **Auth** | JWT (python-jose), passlib |

## 📁 Project Structure

```
mini-games/
├── backend/                    # FastAPI server
│   ├── main.py                 # App entry point + lifespan
│   ├── config.py               # Pydantic settings
│   ├── database.py             # Async SQLAlchemy engine
│   ├── models.py               # DB models (User, Game, GameSession, Chat...)
│   ├── auth.py                 # JWT + password hashing
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── socket_events.py        # Socket.IO event handlers
│   ├── routers/                # FastAPI route modules
│   │   ├── auth.py             # Login / register
│   │   ├── games.py            # Game CRUD + room listing
│   │   ├── leaderboard.py      # ELO rankings
│   │   ├── chat.py             # Chat REST endpoints
│   │   ├── users.py            # User search
│   │   └── social_empires.py   # SE PHP-emulation + CDN routes
│   ├── services/
│   │   ├── games/              # Game engine implementations
│   │   │   ├── base_game.py    # Abstract base class
│   │   │   ├── chess_game.py
│   │   │   ├── checkers_game.py
│   │   │   ├── backgammon_game.py
│   │   │   ├── tic_tac_toe_game.py
│   │   │   └── social_empires.py
│   │   ├── leaderboard.py      # ELO calculation
│   │   └── cleanup.py          # Stale game cleanup task
│   └── social_empires/         # SE game logic (ported from Flask)
│       ├── command.py           # Flash command handler
│       ├── constants.py         # Game data constants
│       ├── engine.py            # Timestamp + utilities
│       ├── sessions.py          # Village save management
│       ├── get_game_config.py   # Game config builder
│       ├── get_player_info.py   # Player info API
│       ├── quests.py            # Quest map loader
│       └── version.py           # Save migration
├── frontend/                   # React + Vite
│   └── src/
│       ├── App.jsx             # Router + layout
│       ├── api.js              # Axios instance (JWT interceptor)
│       ├── socket.js           # Socket.IO singleton
│       ├── stores/             # Zustand state management
│       │   ├── authStore.js
│       │   ├── gameStore.js
│       │   └── chatStore.js
│       ├── pages/              # Route pages
│       │   ├── LoginPage.jsx
│       │   ├── HomePage.jsx
│       │   ├── GameRoomPage.jsx
│       │   ├── LeaderboardPage.jsx
│       │   ├── VillageSelectPage.jsx
│       │   └── SEPlayPage.jsx
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── ChatSidebar.jsx
│       │   └── boards/         # Game board renderers
│       └── styles/
│           └── index.css       # Full design system
├── assets/                     # SE Flash assets (SWFs, images, sounds)
├── config/                     # SE game config JSONs + patches
├── villages/                   # SE quest maps
├── saves/                      # SE village save files
├── mods/                       # SE mod support
├── wave-drifter/               # Wave Drifter Godot source (git clone)
│   ├── project.godot           # Godot project file
│   ├── scenes/                 # Game scenes
│   └── scripts/                # GDScript source
└── stub/                       # crossdomain.xml
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL** (with peer authentication)

### 1. Database Setup

```bash
# Create the database
sudo -u postgres createdb social_empires

# Tables are auto-created on first startup via SQLAlchemy
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

The backend runs on `http://127.0.0.1:5050`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies API to backend)
npm run dev
```

The frontend runs on `http://localhost:5173`.

### 4. Play

Open `http://localhost:5173` in your browser, create an account, and start playing!

---

## ⚙️ Configuration

All settings are in `backend/config.py` and can be overridden via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://adem@/social_empires?host=/var/run/postgresql` | PostgreSQL connection string |
| `JWT_SECRET` | `super-secret-...` | JWT signing secret (**change in production**) |
| `JWT_EXPIRE_MINUTES` | `10080` (1 week) | Token expiration |
| `HOST` | `127.0.0.1` | Server bind address |
| `PORT` | `5050` | Server port |

---

## 🎯 API Overview

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login (returns JWT) |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/games` | List available games |
| GET | `/api/games/{slug}/rooms` | List open rooms |
| GET | `/api/leaderboard/{slug}` | Game leaderboard |
| GET | `/api/se/villages` | List SE villages |
| POST | `/api/se/villages/new` | Create new village |

### Socket.IO Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `create_game` | Client → Server | Create a new game room |
| `join_game` | Client → Server | Join an existing room |
| `make_move` | Client → Server | Submit a move |
| `game_update` | Server → Client | Game state broadcast |
| `find_match` | Client → Server | Quick matchmaking |
| `send_message` | Client → Server | Send chat message |
| `new_message` | Server → Client | Chat message broadcast |

---

## 🏰 Social Empires

This project includes a full preservation of **Social Empires**, a Flash strategy game originally by Social Point. The Flash SWF runs in-browser via [Ruffle](https://ruffle.rs/) WebAssembly emulator.

- **Multiple villages** — Create and switch between villages
- **Save system** — Persistent JSON-based saves with migration support
- **Mod support** — JSON patches in `mods/` directory
- **Original CDN structure** — Routes mimic the original game servers for SWF compatibility

### Social Empires Credits

Based on the [Social Emperors](https://github.com/AcidCaos/socialemperors) preservation project.

---

## 📄 License [![GPL v3](https://img.shields.io/badge/GPL%20v3-blue)](http://www.gnu.org/licenses/gpl-3.0)

```
Mini Games Platform — Social Empires preservation project.
Copyright (C) 2022  The Social Emperors team
See the GNU General Public License <https://www.gnu.org/licenses/>.
```
