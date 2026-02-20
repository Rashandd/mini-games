"""Backgammon game engine."""
import random
from .base_game import BaseGame


class BackgammonGame(BaseGame):
    """
    Simplified backgammon: 24 points, 15 pieces per player.
    Player 1 moves from point 24→1 (bearing off at 0).
    Player 2 moves from point 1→24 (bearing off at 25).
    """

    TOTAL_PIECES = 15

    # Standard opening positions: {point: (player, count)}
    INITIAL_POSITIONS = {
        1: (1, 2), 6: (2, 5), 8: (2, 3), 12: (1, 5),
        13: (2, 5), 17: (1, 3), 19: (1, 5), 24: (2, 2),
    }

    def init_state(self):
        # board[i] = (player, count) for points 1-24; index 0 unused
        board = [None] * 25
        for i in range(25):
            board[i] = (0, 0)
        for pt, (player, count) in self.INITIAL_POSITIONS.items():
            board[pt] = (player, count)

        return {
            'board': board,
            'bar': {1: 0, 2: 0},       # pieces on the bar
            'borne_off': {1: 0, 2: 0},  # pieces borne off
            'current_player': 1,
            'dice': [],
            'remaining_moves': [],
            'winner': None,
            'game_over': False,
            'needs_roll': True,
        }

    def roll_dice(self, state):
        """Roll two dice. Doubles give four moves."""
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        if d1 == d2:
            remaining = [d1] * 4
        else:
            remaining = sorted([d1, d2], reverse=True)

        new_state = dict(state)
        new_state['dice'] = [d1, d2]
        new_state['remaining_moves'] = remaining
        new_state['needs_roll'] = False

        # Check if any moves are possible
        valid = self.get_valid_moves(new_state, new_state['current_player'])
        if not valid:
            # No valid moves, pass turn
            new_state['current_player'] = 2 if new_state['current_player'] == 1 else 1
            new_state['remaining_moves'] = []
            new_state['needs_roll'] = True

        return new_state

    def make_move(self, state, move, player):
        if state['game_over']:
            return state, "Game is already over."
        if state['current_player'] != player:
            return state, "Not your turn."

        action = move.get('action', 'move')

        if action == 'roll':
            if not state['needs_roll']:
                return state, "Already rolled."
            return self.roll_dice(state), None

        if state['needs_roll']:
            return state, "You need to roll first."

        from_pt = move.get('from')
        die_value = move.get('die')

        if die_value not in state['remaining_moves']:
            return state, f"Die value {die_value} not available."

        new_state = self._deep_copy_state(state)
        board = new_state['board']
        bar = new_state['bar']
        borne = new_state['borne_off']

        # Must enter from bar first
        if bar[player] > 0:
            if from_pt != 'bar':
                return state, "Must enter pieces from the bar first."
            if player == 1:
                to_pt = 25 - die_value
            else:
                to_pt = die_value
            if not self._can_land(board, to_pt, player):
                return state, f"Cannot land on point {to_pt}."
            bar[player] -= 1
            self._land_on(board, bar, to_pt, player)
        else:
            if not isinstance(from_pt, int) or not (1 <= from_pt <= 24):
                return state, "Invalid from point."
            if board[from_pt][0] != player or board[from_pt][1] == 0:
                return state, "No piece on that point."

            if player == 1:
                to_pt = from_pt - die_value
            else:
                to_pt = from_pt + die_value

            # Bearing off
            if (player == 1 and to_pt <= 0) or (player == 2 and to_pt >= 25):
                if not self._all_in_home(board, bar, player):
                    return state, "Cannot bear off yet — not all pieces in home."
                p, c = board[from_pt]
                board[from_pt] = (p if c > 1 else 0, max(c - 1, 0))
                borne[player] += 1
            else:
                if not (1 <= to_pt <= 24):
                    return state, "Invalid destination."
                if not self._can_land(board, to_pt, player):
                    return state, f"Cannot land on point {to_pt}."
                p, c = board[from_pt]
                board[from_pt] = (p if c > 1 else 0, max(c - 1, 0))
                self._land_on(board, bar, to_pt, player)

        # Remove used die
        new_state['remaining_moves'].remove(die_value)

        # Check win
        if borne[player] >= self.TOTAL_PIECES:
            new_state['winner'] = player
            new_state['game_over'] = True
            return new_state, None

        # End turn if no moves left
        if not new_state['remaining_moves']:
            new_state['current_player'] = 2 if player == 1 else 1
            new_state['needs_roll'] = True
        else:
            # Check if remaining moves are valid
            valid = self.get_valid_moves(new_state, player)
            if not valid:
                new_state['current_player'] = 2 if player == 1 else 1
                new_state['remaining_moves'] = []
                new_state['needs_roll'] = True

        return new_state, None

    def get_valid_moves(self, state, player):
        if state['game_over'] or state['current_player'] != player:
            return []
        if state['needs_roll']:
            return [{'action': 'roll'}]

        moves = []
        board = state['board']
        bar = state['bar']

        for die in set(state['remaining_moves']):
            if bar[player] > 0:
                if player == 1:
                    to_pt = 25 - die
                else:
                    to_pt = die
                if self._can_land(board, to_pt, player):
                    moves.append({'from': 'bar', 'die': die})
            else:
                for pt in range(1, 25):
                    if board[pt][0] != player or board[pt][1] == 0:
                        continue
                    if player == 1:
                        to_pt = pt - die
                    else:
                        to_pt = pt + die
                    if (player == 1 and to_pt <= 0) or (player == 2 and to_pt >= 25):
                        if self._all_in_home(board, bar, player):
                            moves.append({'from': pt, 'die': die})
                    elif 1 <= to_pt <= 24 and self._can_land(board, to_pt, player):
                        moves.append({'from': pt, 'die': die})

        return moves

    def is_game_over(self, state):
        return state.get('game_over', False)

    def get_winner(self, state):
        return state.get('winner')

    # --- Helpers ---

    def _can_land(self, board, pt, player):
        if not (1 <= pt <= 24):
            return False
        occ_player, occ_count = board[pt]
        if occ_player == 0 or occ_player == player:
            return True
        return occ_count <= 1  # can hit a blot

    def _land_on(self, board, bar, pt, player):
        occ_player, occ_count = board[pt]
        opponent = 2 if player == 1 else 1
        if occ_player == opponent and occ_count == 1:
            # Hit!
            bar[opponent] += 1
            board[pt] = (player, 1)
        else:
            new_count = (occ_count + 1) if occ_player == player else 1
            board[pt] = (player, new_count)

    def _all_in_home(self, board, bar, player):
        if bar[player] > 0:
            return False
        if player == 1:
            # Home = points 1-6
            for pt in range(7, 25):
                if board[pt][0] == player and board[pt][1] > 0:
                    return False
        else:
            # Home = points 19-24
            for pt in range(1, 19):
                if board[pt][0] == player and board[pt][1] > 0:
                    return False
        return True

    def _deep_copy_state(self, state):
        return {
            'board': [tuple(x) for x in state['board']],
            'bar': dict(state['bar']),
            'borne_off': dict(state['borne_off']),
            'current_player': state['current_player'],
            'dice': list(state['dice']),
            'remaining_moves': list(state['remaining_moves']),
            'winner': state['winner'],
            'game_over': state['game_over'],
            'needs_roll': state['needs_roll'],
        }
