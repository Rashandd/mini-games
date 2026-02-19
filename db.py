import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Database configuration
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql:///social_empires'  # Uses Unix socket (peer auth)
)

def init_db(app):
    """Initialize the database with the Flask app."""
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        # Import all models so they are registered
        import models  # noqa: F401
        from auth import User  # noqa: F401
        db.create_all()
        _seed_games()

def _seed_games():
    """Seed default games if they don't exist."""
    from models import Game
    defaults = [
        {
            "slug": "tic-tac-toe",
            "name": "Tic-Tac-Toe",
            "description": "Classic 3×3 strategy game. Get three in a row to win!",
            "icon": "❌⭕",
            "min_players": 2,
            "max_players": 2,
        },
        {
            "slug": "chess",
            "name": "Chess",
            "description": "The king of strategy games. Checkmate your opponent!",
            "icon": "♟️♚",
            "min_players": 2,
            "max_players": 2,
        },
        {
            "slug": "backgammon",
            "name": "Backgammon",
            "description": "Ancient board game of luck and strategy. Bear off all your pieces!",
            "icon": "🎲🔵",
            "min_players": 2,
            "max_players": 2,
        },
        {
            "slug": "checkers",
            "name": "Checkers",
            "description": "Jump and capture all your opponent's pieces!",
            "icon": "🔴⚫",
            "min_players": 2,
            "max_players": 2,
        },
        {
            "slug": "social-empires",
            "name": "Social Empires",
            "description": "Featured: The classic Flash empire-building game. Grow your village and train your army!",
            "icon": "⚔️🏰",
            "min_players": 1,
            "max_players": 1,
        },
    ]
    for g in defaults:
        if not Game.query.filter_by(slug=g["slug"]).first():
            db.session.add(Game(**g))
    db.session.commit()
