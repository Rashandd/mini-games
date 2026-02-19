"""Game engine registry and base class."""
from games.base_game import BaseGame
from games.tic_tac_toe_game import TicTacToeGame
from games.chess_game import ChessGame
from games.backgammon_game import BackgammonGame
from games.checkers_game import CheckersGame
from games.social_empires import SocialEmpiresGame

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
