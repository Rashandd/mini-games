"""Bridge for Social Empires (Flash game)."""
from games.base_game import BaseGame


class SocialEmpiresGame(BaseGame):
    """
    Social Empires is a Flash game, so its state is handled by the SWF.
    This class serves as a placeholder for the platform's game registry.
    """

    def init_state(self):
        return {
            'is_flash': True,
            'game_over': False,
        }

    def make_move(self, state, move, player):
        return state, "Social Empires state is managed by the game client."

    def get_valid_moves(self, state, player):
        return []

    def is_game_over(self, state):
        return False

    def get_winner(self, state):
        return None
