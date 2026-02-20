"""FastAPI application — Mini Games Platform."""
import asyncio
from contextlib import asynccontextmanager

import socketio as sio_pkg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print(" [+] Starting Mini Games Platform (FastAPI)...")

    # Init database
    await init_db()
    print(" [+] Database initialized.")

    # Load SE villages + config
    from social_empires.sessions import load_saved_villages
    from social_empires.get_game_config import load_game_config

    await load_game_config()
    print(" [+] Game config loaded.")

    await load_saved_villages()
    print(" [+] Villages loaded.")

    # Start cleanup background task
    from services.cleanup import cleanup_loop
    cleanup_task = asyncio.create_task(cleanup_loop())
    print(" [+] Cleanup task started.")

    print(f" [+] Mini Games Platform running on http://{settings.HOST}:{settings.PORT}")
    yield

    # Shutdown
    cleanup_task.cancel()
    print(" [+] Shutting down...")


# Create FastAPI app
app = FastAPI(title="Mini Games Platform", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
app.mount("/assets", StaticFiles(directory=settings.ASSETS_DIR), name="assets")

# Stub files (crossdomain, etc.)
import os
if os.path.exists(settings.STUB_DIR):
    app.mount("/stub", StaticFiles(directory=settings.STUB_DIR), name="stub")

# ─── Routers ────────────────────────────────────────────────────────────────

from routers.auth import router as auth_router
from routers.games import router as games_router
from routers.leaderboard import router as leaderboard_router
from routers.chat import router as chat_router
from routers.users import router as users_router
from routers.social_empires import router as se_router

app.include_router(auth_router)
app.include_router(games_router)
app.include_router(leaderboard_router)
app.include_router(chat_router)
app.include_router(users_router)
app.include_router(se_router)


# ─── Socket.IO (ASGI mount) ────────────────────────────────────────────────

from socket_events import sio

socket_app = sio_pkg.ASGIApp(sio, other_asgi_app=app)


# ─── Health check ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ─── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:socket_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
