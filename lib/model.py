import enum
from dataclasses import field, dataclass
from typing import List, Union, Optional


@enum.unique
class Suit(enum.Enum):
    SPADES = 1
    DIAMONDS = 2
    HEARTS = 3
    CLUBS = 4

    @property
    def is_one_eyed(self):
        return self == self.SPADES or self == self.HEARTS

    def __str__(self):
        return str(self.name.title())

    def __hash__(self):
        return hash(self.value)


@enum.unique
class Rank(enum.Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    def __str__(self):
        return str(self.value) if (self.value > 1 and self.value < 11) else str(self.name.title())


@dataclass(frozen=True)
class Card:
    suit: Suit
    rank: Rank

    def __post_init__(self):
        if not isinstance(self.rank, Rank):
            raise TypeError(f"Card.rank must be Rank, got {self.rank.__class__}")
        if not isinstance(self.suit, Suit):
            raise TypeError(f"Card.suit must be Suit, got {self.suit.__class__}")

    @property
    def is_one_eyed_jack(self):
        return self.suit.is_one_eyed and self.rank == Rank.JACK

    @property
    def is_two_eyed_jack(self):
        return not self.suit.is_one_eyed and self.rank == Rank.JACK

    def __str__(self):
        return f"{self.rank} of {self.suit}"

    def __hash__(self):
        return hash((self.suit.value, self.rank))

    @property
    def debug(self):
        return f"{self.rank}|{self.suit}"


@dataclass
class Player:
    id: str
    name: str
    hand: List['Card'] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)

    def select_card(self, i):
        return self.hand[i]

    def draw_card(self, draw_card_func):
        new_card = draw_card_func()
        if not isinstance(new_card, Card):
            raise TypeError(f"Player hand expected to receive Card, got {new_card.__class__}")
        self.hand.append(new_card)

    def use_card(self, card):
        self.hand.remove(card)


class WildCard:
    @property
    def debug(self):
        return "Wild"


Wild = WildCard()


@dataclass
class Cell:
    card: Union[Card, type(Wild)]
    player: Optional[Player]

    @classmethod
    def from_values(cls, rank, suit):
        if rank is None and suit is None:
            card = Wild
        elif rank is None or suit is None:
            raise ValueError(f"Rank [{rank}] and Suit [{suit}] must both be given or both be none")
        else:
            if isinstance(rank, int):
                rank = Rank(rank)
            card = Card(suit, rank)
        return Cell(card, player=None)

    @property
    def is_occupied(self):
        return self.player is not None

    def can_play_card(self, card):
        if self.is_wild:
            return False
        return self.card.suit == card.suit and self.card.rank == card.rank

    @property
    def is_wild(self):
        return self.card is Wild


def generate_deck():
    return [
        Card(s, r)
        for s in Suit
        for r in Rank
    ]
