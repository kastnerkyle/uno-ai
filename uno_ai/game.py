"""
Core Uno game logic.
"""

from enum import Enum
import random

from .cards import CardType, full_deck


class GameState(Enum):
    PLAY_OR_DRAW = 0
    PLAY = 1
    PLAY_DRAWN = 2
    PICK_COLOR = 3
    PICK_COLOR_INIT = 4
    CHALLENGE = 5


class Game:
    def __init__(self, num_players):
        self._num_players = num_players
        self._deck = full_deck()
        random.shuffle(self._deck)
        self._discard = []
        self._hands = []
        for _ in range(num_players):
            hand = []
            for _ in range(7):
                hand.append(self._deck.pop())
            self._hands.append(hand)
        while self._deck[-1].card_type == CardType.WILD_DRAW:
            random.shuffle(self._deck)
        self._discard.append(self._deck.pop())

        self._direction = 1
        self._turn = 0
        self._state = GameState.PLAY_OR_DRAW

        self._update_init_state()

    def winner(self):
        """
        If the game has ended, get the winner.
        """
        for i, hand in self._hands:
            if not len(hand):
                return i
        return None

    def mask(self, player):
        """
        Get the current action mask for the player.
        """
        pass

    def obs(self, player):
        """
        Generate an observation vector for the player.
        """
        pass

    def act(self, logits):
        """
        Perform actions by providing the logits for all of
        the players.

        Args:
            logits: a list of numpy arrays, one per player.
              These will automatically be masked.
        """
        pass

    def _draw(self):
        if len(self._deck):
            return self._deck.pop()
        self._deck = self._discard[:-1]
        self._discard = [self._discard[-1]]
        random.shuffle(self._deck)
        for card in self._deck:
            if card.card_type == CardType.WILD or card.card_type == CardType.WILD_DRAW:
                card.color = None
        return self._deck.pop()

    def _update_init_state(self):
        first_card = self._discard[0]
        if first_card.card_type == CardType.SKIP:
            self._turn += 1
        elif first_card.card_type == CardType.REVERSE:
            self._direction = -1
            self._turn = self._num_players - 1
        elif first_card.card_type == CardType.DRAW_TWO:
            for _ in range(2):
                self._hands[0].append(self._draw())
            self._turn = 1
        elif first_card.card_type == CardType.WILD:
            self._state = GameState.PICK_COLOR_INIT
