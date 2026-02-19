"""Checkers (draughts) game engine — 8×8 board."""
from games.base_game import BaseGame


class CheckersGame(BaseGame):
    """
    Standard 8×8 checkers.
    Player 1 = dark pieces (bottom, moves up). Player 2 = light pieces (top, moves down).
    Board is 8×8, playable squares at (r, c) where (r+c) % 2 == 1.
    Pieces: 1=man, 2=king for each player.
    """

    SIZE = 8

    def init_state(self):
        board = [[0] * self.SIZE for _ in range(self.SIZE)]
        # Player 2 (top, rows 0-2)
        for r in range(3):
            for c in range(self.SIZE):
                if (r + c) % 2 == 1:
                    board[r][c] = -1  # -1 = player2 man
        # Player 1 (bottom, rows 5-7)
        for r in range(5, 8):
            for c in range(self.SIZE):
                if (r + c) % 2 == 1:
                    board[r][c] = 1  # 1 = player1 man

        return {
            'board': board,
            'current_player': 1,
            'winner': None,
            'game_over': False,
            'must_jump_from': None,  # forced multi-jump
        }

    def make_move(self, state, move, player):
        if state['game_over']:
            return state, "Game is already over."
        if state['current_player'] != player:
            return state, "Not your turn."

        fr = move.get('from_row')
        fc = move.get('from_col')
        tr = move.get('to_row')
        tc = move.get('to_col')

        if None in (fr, fc, tr, tc):
            return state, "Move requires from_row, from_col, to_row, to_col."

        # Validate forced jump
        if state['must_jump_from']:
            if (fr, fc) != tuple(state['must_jump_from']):
                return state, "Must continue jumping from the same piece."

        board = [row[:] for row in state['board']]
        piece = board[fr][fc]

        if not self._owns(piece, player):
            return state, "Not your piece."

        is_king = abs(piece) == 2
        dr = tr - fr
        dc = tc - fc

        # Simple move
        if abs(dr) == 1 and abs(dc) == 1:
            # Check direction
            if not is_king and not self._correct_direction(player, dr):
                return state, "Man can only move forward."
            if board[tr][tc] != 0:
                return state, "Destination not empty."
            # Check no jumps available (must jump if possible)
            jumps = self._get_jumps(board, player)
            if jumps:
                return state, "Jump is available — you must jump."
            board[tr][tc] = piece
            board[fr][fc] = 0
            board = self._promote(board, tr, tc)
            new_state = self._next_state(board, state, player)
            return new_state, None

        # Jump
        if abs(dr) == 2 and abs(dc) == 2:
            mr, mc = (fr + tr) // 2, (fc + tc) // 2
            captured = board[mr][mc]
            if not self._is_opponent(captured, player):
                return state, "No opponent piece to jump over."
            if board[tr][tc] != 0:
                return state, "Destination not empty."
            if not is_king and not self._correct_direction(player, dr):
                return state, "Man can only jump forward."

            board[tr][tc] = piece
            board[fr][fc] = 0
            board[mr][mc] = 0
            board = self._promote(board, tr, tc)

            # Check multi-jump
            more_jumps = self._get_piece_jumps(board, tr, tc, player)
            if more_jumps:
                return {
                    'board': board,
                    'current_player': player,
                    'winner': None,
                    'game_over': False,
                    'must_jump_from': [tr, tc],
                }, None
            else:
                new_state = self._next_state(board, state, player)
                return new_state, None

        return state, "Invalid move distance."

    def get_valid_moves(self, state, player):
        if state['game_over'] or state['current_player'] != player:
            return []

        board = state['board']

        if state['must_jump_from']:
            r, c = state['must_jump_from']
            return self._get_piece_jumps(board, r, c, player)

        jumps = self._get_jumps(board, player)
        if jumps:
            return jumps

        moves = []
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                piece = board[r][c]
                if not self._owns(piece, player):
                    continue
                is_king = abs(piece) == 2
                for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    if not is_king and not self._correct_direction(player, dr):
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.SIZE and 0 <= nc < self.SIZE and board[nr][nc] == 0:
                        moves.append({'from_row': r, 'from_col': c, 'to_row': nr, 'to_col': nc})
        return moves

    def is_game_over(self, state):
        return state.get('game_over', False)

    def get_winner(self, state):
        return state.get('winner')

    # --- Helpers ---

    def _owns(self, piece, player):
        if player == 1:
            return piece > 0
        return piece < 0

    def _is_opponent(self, piece, player):
        if player == 1:
            return piece < 0
        return piece > 0

    def _correct_direction(self, player, dr):
        return (player == 1 and dr < 0) or (player == 2 and dr > 0)

    def _promote(self, board, r, c):
        piece = board[r][c]
        if piece == 1 and r == 0:
            board[r][c] = 2
        elif piece == -1 and r == self.SIZE - 1:
            board[r][c] = -2
        return board

    def _get_jumps(self, board, player):
        jumps = []
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if self._owns(board[r][c], player):
                    jumps.extend(self._get_piece_jumps(board, r, c, player))
        return jumps

    def _get_piece_jumps(self, board, r, c, player):
        piece = board[r][c]
        is_king = abs(piece) == 2
        jumps = []
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            if not is_king and not self._correct_direction(player, dr):
                continue
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if 0 <= tr < self.SIZE and 0 <= tc < self.SIZE:
                if self._is_opponent(board[mr][mc], player) and board[tr][tc] == 0:
                    jumps.append({'from_row': r, 'from_col': c, 'to_row': tr, 'to_col': tc})
        return jumps

    def _next_state(self, board, old_state, player):
        next_player = 2 if player == 1 else 1
        new_state = {
            'board': board,
            'current_player': next_player,
            'winner': None,
            'game_over': False,
            'must_jump_from': None,
        }
        # Check if next player has any moves
        if not self.get_valid_moves(new_state, next_player):
            new_state['winner'] = player
            new_state['game_over'] = True
        return new_state
