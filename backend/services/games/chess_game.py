"""Chess game engine using python-chess."""
import chess
from .base_game import BaseGame


class ChessGame(BaseGame):

    def init_state(self):
        return {
            'fen': chess.STARTING_FEN,
            'current_player': 1,  # 1=white, 2=black
            'move_history': [],
            'winner': None,
            'game_over': False,
            'check': False,
        }

    def make_move(self, state, move, player):
        if state['game_over']:
            return state, "Game is already over."
        if state['current_player'] != player:
            return state, "Not your turn."

        board = chess.Board(state['fen'])
        move_uci = move.get('uci', '')

        try:
            chess_move = chess.Move.from_uci(move_uci)
        except (ValueError, chess.InvalidMoveError):
            return state, f"Invalid move format: {move_uci}"

        if chess_move not in board.legal_moves:
            return state, f"Illegal move: {move_uci}"

        # Apply move
        san = board.san(chess_move)
        board.push(chess_move)

        new_state = {
            'fen': board.fen(),
            'current_player': 2 if player == 1 else 1,
            'move_history': list(state['move_history']) + [{'uci': move_uci, 'san': san, 'player': player}],
            'winner': None,
            'game_over': False,
            'check': board.is_check(),
            'last_move': move_uci,
        }

        # Check end conditions
        if board.is_checkmate():
            new_state['winner'] = player
            new_state['game_over'] = True
        elif board.is_stalemate() or board.is_insufficient_material() or \
             board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
            new_state['winner'] = 0  # draw
            new_state['game_over'] = True

        return new_state, None

    def get_valid_moves(self, state, player):
        if state['game_over'] or state['current_player'] != player:
            return []
        board = chess.Board(state['fen'])
        return [{'uci': m.uci()} for m in board.legal_moves]

    def is_game_over(self, state):
        return state.get('game_over', False)

    def get_winner(self, state):
        return state.get('winner')

    def state_for_client(self, state, player):
        """Chess is fully visible, return everything."""
        return state
