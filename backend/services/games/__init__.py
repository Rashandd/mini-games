"""Game engine registry and base class."""
from .base_game import BaseGame
from .tic_tac_toe_game import TicTacToeGame
from .chess_game import ChessGame
from .backgammon_game import BackgammonGame
from .checkers_game import CheckersGame
from .social_empires import SocialEmpiresGame

# Game registry: slug -> engine class
GAME_ENGINES = {
    'tic-tac-toe': TicTacToeGame,
    'chess': ChessGame,
    'backgammon': BackgammonGame,
    'checkers': CheckersGame,
    'social-empires': SocialEmpiresGame,
}

def get_engine(slug):
    """Get a game engine instance by slug."""
    cls = GAME_ENGINES.get(slug)
    if cls is None:
        raise ValueError(f"Unknown game: {slug}")
    return cls()
