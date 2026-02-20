"""Tic-Tac-Toe game engine."""
from .base_game import BaseGame


class TicTacToeGame(BaseGame):

    def init_state(self):
        return {
            'board': [0] * 9,  # 0=empty, 1=X, 2=O
            'current_player': 1,
            'winner': None,
            'game_over': False,
        }

    def make_move(self, state, move, player):
        if state['game_over']:
            return state, "Game is already over."
        if state['current_player'] != player:
            return state, "Not your turn."

        pos = move.get('position')
        if pos is None or not (0 <= pos <= 8):
            return state, "Invalid position (must be 0-8)."
        if state['board'][pos] != 0:
            return state, "Cell already occupied."

        new_state = {
            'board': list(state['board']),
            'current_player': state['current_player'],
            'winner': state['winner'],
            'game_over': state['game_over'],
        }
        new_state['board'][pos] = player

        # Check win
        winner = self._check_winner(new_state['board'])
        if winner:
            new_state['winner'] = winner
            new_state['game_over'] = True
        elif 0 not in new_state['board']:
            # Draw
            new_state['winner'] = 0
            new_state['game_over'] = True
        else:
            new_state['current_player'] = 2 if player == 1 else 1

        return new_state, None

    def get_valid_moves(self, state, player):
        if state['game_over'] or state['current_player'] != player:
            return []
        return [{'position': i} for i, v in enumerate(state['board']) if v == 0]

    def is_game_over(self, state):
        return state.get('game_over', False)

    def get_winner(self, state):
        return state.get('winner')

    def _check_winner(self, board):
        lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
            (0, 4, 8), (2, 4, 6),              # diags
        ]
        for a, b, c in lines:
            if board[a] != 0 and board[a] == board[b] == board[c]:
                return board[a]
        return None
