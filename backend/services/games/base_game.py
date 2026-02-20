"""Abstract base class for all game engines."""
from abc import ABC, abstractmethod


class BaseGame(ABC):
    """Every game must implement these methods."""

    @abstractmethod
    def init_state(self):
        """Return the initial game state as a dict."""
        pass

    @abstractmethod
    def make_move(self, state, move, player):
        """
        Apply a move to the state.
        Args:
            state: current game state dict
            move: move data (format depends on the game)
            player: 1 or 2
        Returns:
            (new_state, error_msg or None)
        """
        pass

    @abstractmethod
    def get_valid_moves(self, state, player):
        """Return list of valid moves for the given player."""
        pass

    @abstractmethod
    def is_game_over(self, state):
        """Return True if the game has ended."""
        pass

    @abstractmethod
    def get_winner(self, state):
        """Return winner (1 or 2), 0 for draw, None if game not over."""
        pass

    def get_current_player(self, state):
        """Return which player's turn it is (1 or 2)."""
        return state.get('current_player', 1)

    def state_for_client(self, state, player):
        """
        Return a client-safe view of the state.
        Override to hide information (e.g., opponent's hand in card games).
        """
        return state
