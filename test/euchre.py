from collections import namedtuple
from random import shuffle, choice
from itertools import chain

from constraint import AllDifferentConstraint, Problem

from six import iteritems
from six.moves import filter, range


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


team = {
    0: 0,
    1: 1,
    2: 0,
    3: 1
}


same_color = {
    'd': 'h',
    'h': 'd',
    'c': 's',
    's': 'c'
}


suits = ['d', 'h', 's', 'c']


def deal():
    return [value + suit
            for suit in suits
            for value in ['a', 'k', 'q', 'j', '0', '9']]


def jack_of_trump(trump):
    return 'j' + trump


def second_highest_jack(trump):
    return 'j' + same_color[trump]


def value(card):
    return {
        '9': 9,
        '0': 10,
        'j': 11,
        'q': 12,
        'k': 13,
        'a': 14
    }[card[0]]


def sort_by_trump_and_lead(trump, lead_suit, cards):
    return sorted(cards,
                  key=lambda c: (c == jack_of_trump(trump),
                                 c == second_highest_jack(trump),
                                 suit(trump, c) == trump,
                                 suit(trump, c) == lead_suit,
                                 value(c)),
                  reverse=True)


def winning_card(trump, lead_suit, cards):
    return sort_by_trump_and_lead(trump, lead_suit, cards)[0]


def suit(trump, card):
    if card == second_highest_jack(trump):
        return trump
    if card is not None:
        try:
            return card[1]
        except IndexError:
            return ValueError('Cards need to be two characters long')


def playable_cards(trump, lead_suit, hand):
    if lead_suit is None:
        return hand

    must_play = [card for card in hand
                 if suit(trump, card) == lead_suit]
    if must_play:
        return must_play

    return hand


def potential_cards_given_voids(trump, voids, cards):
    """During the simulation we will distribute cards to players and track
    when they have played off on a certain lead. This function returns the
    cards a player can select when they have played off on certain suits"""
    return [card for card in cards if suit(trump, card) not in voids]


class EuchreGame(object):
    """A simple trick-taking card game"""

    State = namedtuple('EuchreState', 'hands,'
                                      'cards_played_by_player,'
                                      'current_player,'
                                      'lead_card,'
                                      'trump,'
                                      'winning_team,'
                                      'tricks_won_by_team,'
                                      'cards_played,'
                                      'voids_by_player')

    @classmethod
    def initial_state(cls, visible_hand=None, trump=None):
        all_cards = deal()
        if not visible_hand:
            visible_hand = deal()
            shuffle(visible_hand)
            visible_hand = visible_hand[:5]
        if len(visible_hand) != 5:
            raise ValueError('visible_hand should have 5 cards')
        for card in visible_hand:
            if card not in all_cards:
                raise ValueError('Invalid card in visible hand')
        if trump is None:
            trump = choice(suits)
        if trump not in suits:
            raise ValueError('Invalid trump suit')
        return cls.State(hands=[visible_hand, [], [], []],
                         cards_played_by_player=[None] * 4,
                         current_player=0,
                         lead_card=None,
                         trump=trump,
                         winning_team=None,
                         tricks_won_by_team=[0, 0],
                         cards_played=[],
                         voids_by_player=[set(), set(), set(), set()])

    @classmethod
    def apply_move(cls, state, move):
        cards_played_by_player = state.cards_played_by_player[:]
        voids_by_player = state.voids_by_player
        hands = [hand[:] for hand in state.hands]
        tricks_won_by_team = state.tricks_won_by_team
        lead_card = state.lead_card
        cards_played = state.cards_played

        if state.lead_card is None:
            lead_card = move

        lead_suit = suit(state.trump, lead_card)
        if (suit(state.trump, move) in
                state.voids_by_player[state.current_player]):
            raise ValueError('Did not follow suit voids_by_player=%r move=%r' %
                             (state.voids_by_player, move))

        if (state.lead_card and move not in
                playable_cards(state.trump,
                               lead_suit,
                               hands[state.current_player])):
            raise ValueError('Cheating trump=%r lead=%r hand=%r move=%r' %
                             (state.trump,
                              lead_suit,
                              hands[state.current_player],
                              move))
        cards_played_by_player[state.current_player] = move
        hands[state.current_player].remove(move)

        if lead_suit != suit(state.trump, move):
            voids_by_player = [set(x) for x in state.voids_by_player]
            voids_by_player[state.current_player].add(lead_suit)

        next_player = (state.current_player + 1) % 4

        number_of_cards_played = len(
            list(filter(None, cards_played_by_player)))

        if number_of_cards_played == 4:
            winner = winning_card(state.trump,
                                  lead_suit,
                                  cards_played_by_player)
            winning_player = cards_played_by_player.index(winner)
            tricks_won_by_team = tricks_won_by_team[:]
            winning_team = team[winning_player]
            tricks_won_by_team[winning_team] = (
                tricks_won_by_team[winning_team] + 1)

            # reset the state for a new trick
            next_player = winning_player
            cards_played = cards_played[:]
            cards_played.extend(cards_played_by_player)
            cards_played_by_player = [None] * 4
            lead_card = None

        winning_team = None
        if sum(tricks_won_by_team) == 5:
            if tricks_won_by_team[0] > tricks_won_by_team[1]:
                winning_team = 0
            else:
                winning_team = 1

        return cls.State(hands=hands,
                         cards_played_by_player=cards_played_by_player,
                         current_player=next_player,
                         lead_card=lead_card,
                         winning_team=winning_team,
                         trump=state.trump,
                         tricks_won_by_team=tricks_won_by_team,
                         cards_played=cards_played,
                         voids_by_player=voids_by_player)

    @classmethod
    def get_moves(cls, state):
        return (False,
                playable_cards(state.trump,
                               suit(state.trump, state.lead_card),
                               state.hands[state.current_player]))

    @classmethod
    def determine(cls, state):
        remaining_hand_size = 5 - sum(state.tricks_won_by_team)
        cards = list(set(deal()) -
                     set(list(chain(*state.hands))) -
                     set(state.cards_played))
        shuffle(cards)

        if remaining_hand_size < 5:
            problem = Problem()
            for player in range(4):
                for card_index in range(remaining_hand_size):
                    variable_name = 'p{}{}'.format(player, card_index)
                    if state.hands[player]:
                        problem.addVariable(variable_name,
                                            [state.hands[player][card_index]])
                    else:
                        problem.addVariable(variable_name, cards)
                        voids_by_player = state.voids_by_player[player]
                        if voids_by_player:
                            def ensure_voids(card,
                                             voids_by_player=voids_by_player,
                                             player=player):
                                return (
                                    suit(state.trump, card)
                                    not in voids_by_player)
                            problem.addConstraint(
                                ensure_voids,
                                (variable_name,))
            problem.addConstraint(AllDifferentConstraint())

            cards = sorted(iteritems(problem.getSolution()))
            hands = list(chunks([c[1] for c in cards], remaining_hand_size))
        else:
            hands = [hand[:] for hand in state.hands]
            new_hands = iter(chunks(cards, remaining_hand_size))
            for i, hand in enumerate(state.hands):
                if not hand:
                    hands[i] = next(new_hands)

        state = state._replace(hands=hands)
        return state

    @classmethod
    def get_winner(cls, state):
        return state.winning_team

    @classmethod
    def current_player(cls, state):
        return team[state.current_player]

    @classmethod
    def print_board(cls, state):
        print('lead_suit=%r trump=%r cards_played_by_player=%r\nhands=%r' % (
            state.lead_card and suit(state.trump, state.lead_card) or '?',
            state.trump,
            state.cards_played_by_player,
            state.hands))
        print('')
