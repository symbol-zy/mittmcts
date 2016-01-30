from collections import namedtuple
from copy import copy


class GameWithOneMove(object):
    """An extremely silly game where you can only choose to win.
    MCTS should choose to win this game every time"""

    State = namedtuple('GameWithOneMoveState',
                       'winner, current_player')

    @classmethod
    def initial_state(cls):
        return cls.State(winner=None, current_player=1)

    @classmethod
    def get_moves(cls, state):
        if state.winner:
            return (False, [])
        else:
            return (False, ['win'])

    @classmethod
    def apply_move(cls, state, move):
        if move != 'win':
            raise ValueError('Invalid move')
        return cls.State(winner=state.current_player, current_player=1)

    @classmethod
    def get_winner(cls, state):
        return state.winner

    @classmethod
    def current_player(cls, state):
        return state.current_player


class GameWithTwoMoves(object):
    """A game with two players where the first player can choose to win or
    pass and then the next player has to choose to win if the first player
    passed"""

    State = namedtuple('GameWithOneMoveState',
                       'board, winner, current_player')

    @classmethod
    def initial_state(cls):
        return cls.State(board=[0, 0], winner=None, current_player=1)

    @classmethod
    def get_moves(cls, state):
        return (False, [position for position, player in enumerate(state.board)
                        if player == 0])

    @classmethod
    def apply_move(cls, state, move):
        winner = None
        new_board = copy(state.board)
        if state.board[move] != 0:
            raise ValueError('Invalid move')
        new_board[move] = state.current_player
        if move == 1:
            winner = state.current_player
        return cls.State(board=new_board,
                         winner=winner,
                         current_player=state.current_player + 1)

    @classmethod
    def get_winner(cls, state):
        return state.winner

    @classmethod
    def current_player(cls, state):
        return state.current_player


class SimpleDiceRollingGame(object):
    """A one-player game where the player chooses to roll 0, 1 or 2 dice and
    rolls them. The player wins if they roll a total of 6 or above"""

    State = namedtuple('SimpleDiceRollingGameState',
                       'score, winner, round, dice_to_roll')
    die_roll_outcome = range(1, 7)

    @classmethod
    def initial_state(cls):
        return cls.State(score=0,
                         winner=None,
                         dice_to_roll=0,
                         round=0)

    @classmethod
    def get_moves(cls, state):
        if state.round == 2:
            return (False, [])

        if state.round == 0:
            return (False, [0, 1, 2])

        elif state.dice_to_roll == 0:
            return (True, [0])
        elif state.dice_to_roll == 1:
            return (True, cls.die_roll_outcome)
        elif state.dice_to_roll == 2:
            return (True, [x + y
                           for x in cls.die_roll_outcome
                           for y in cls.die_roll_outcome])

    @classmethod
    def apply_move(cls, state, move):
        dice_to_roll = 0
        score = 0
        winner = None

        if state.round == 0:
            dice_to_roll = move

        if state.round == 1:
            score = move
            if score > 5:
                winner = 1
            else:
                winner = 2

        return cls.State(dice_to_roll=dice_to_roll,
                         score=score,
                         winner=winner,
                         round=state.round + 1)

    @classmethod
    def get_winner(cls, state):
        return state.winner

    @classmethod
    def update_misc(cls, end_node, misc_by_player):
        if 'scores' not in misc_by_player[1]:
            misc_by_player[1] = {
                'scores': [],
                'avg_score': 0,
                'min_score': 0,
                'max_score': 0,
            }
        misc = misc_by_player[1]
        scores = misc['scores']
        scores.append(end_node.score)
        misc.update({'avg_score': sum(scores) / len(scores),
                     'min_score': min(scores),
                     'max_score': max(scores)})

    @classmethod
    def current_player(cls, state):
        return 1


class TicTacToeGame(object):
    """Standard tic-tac-toe game"""

    State = namedtuple('TicTacToeState', 'board, current_player, winner')
    winning_scores = [7, 56, 448, 73, 146, 292, 273, 84]

    @classmethod
    def initial_state(cls):
        return cls.State(board=[None] * 9, current_player='X', winner=None)

    @classmethod
    def apply_move(cls, state, move):
        new_board = copy(state.board)
        if state.board[move]:
            raise Exception('Already played there')
        new_board[move] = state.current_player
        next_player = state.current_player == 'X' and 'O' or 'X'
        winner = None
        for player in ['X', 'O']:
            score = sum([2 ** i for i, spot in enumerate(new_board)
                        if spot == player])
            for winning_score in cls.winning_scores:
                if winning_score & score == winning_score:
                    winner = player
        return cls.State(board=new_board,
                         current_player=next_player,
                         winner=winner)

    @classmethod
    def get_moves(cls, state):
        if state.winner:
            return (False, [])
        return (False, [i for i, spot in enumerate(state.board)
                        if spot is None])

    @classmethod
    def get_winner(cls, state):
        return state.winner

    @classmethod
    def current_player(cls, state):
        return state.current_player
