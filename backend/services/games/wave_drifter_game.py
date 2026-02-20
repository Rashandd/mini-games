"""Bridge for Wave Drifter (Godot HTML5 game)."""
from .base_game import BaseGame


class WaveDrifterGame(BaseGame):
    """
    Wave Drifter runs in the browser via Godot HTML5 export.
    This placeholder registers it in the platform's game list.
    """

    def init_state(self):
        return {
            'is_embedded': True,
            'game_over': False,
        }

    def make_move(self, state, move, player):
        return state, "Wave Drifter state is managed by the game client."

    def get_valid_moves(self, state, player):
        return []

    def is_game_over(self, state):
        return False

    def get_winner(self, state):
        return None
