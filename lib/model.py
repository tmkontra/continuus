import collections
import enum
from dataclasses import field, dataclass
from typing import List, Union, Optional, Dict, Tuple

from lib import matrix


class InvalidCellSelection(Exception):
    pass


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

    @property
    def debug(self):
        return str(self)[0]


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
    def red(self):
        return self.suit in (Suit.DIAMONDS, Suit.HEARTS)

    @property
    def black(self):
        return self.suit in (Suit.CLUBS, Suit.SPADES)

    @property
    def debug(self):
        return f"{self.rank.debug}|{self.suit.name[0]}"


class Color(enum.Enum):
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'


@dataclass
class Player:
    id: str
    name: str
    hand: List['Card'] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Player):
            return self.id == other.id
        return False

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
    suit = None
    rank = None

    @property
    def debug(self):
        return "W"

    @property
    def red(self):
        return False

    @property
    def black(self):
        return False


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


class DeadCardError(Exception):
    pass


class Board:
    __DIM = 10
    ROWS = __DIM
    COLUMNS = __DIM
    SEQUENCE_LENGTH = 5

    def __init__(self, cells):
        self.cells: List[List[Cell]] = cells
        self._cells_by_card: Dict['Card', List[Tuple[int, int]]] = Board._hashmap(self.cells)

    @staticmethod
    def claim_cell(player, card: 'Card', cell: 'Cell'):
        if cell.is_wild:
            raise ValueError("Wild space cannot be played!")
        if cell.is_occupied:
            if cell.player == player:
                raise ValueError("Player cannot play on a cell they already possess")
            if card.is_one_eyed_jack:
                cell.player = None
                return True
        if card.is_two_eyed_jack:
            cell.player = player
            return True
        if cell.can_play_card(card):
            cell.player = player
            return True
        else:
            raise RuntimeError("Cell does not match card.")

    def get_cell(self, row, column):
        if row >= self.ROWS:
            raise InvalidCellSelection(f"Row must be between 0 and {self.ROWS}")
        if column >= self.COLUMNS:
            raise InvalidCellSelection(f"Column must be between 0 and {self.COLUMNS}")
        return self.cells[row][column]

    @classmethod
    def new_board(cls):
        S = Suit.SPADES
        C = Suit.CLUBS
        D = Suit.DIAMONDS
        H = S.HEARTS
        N = None
        T = 10
        A = Rank.ACE
        Q = Rank.QUEEN
        K = Rank.KING
        suits = [
            [N, D, D, D, D, D, D, D, D, N],
            [D, H, H, S, S, S, S, S, S, C],
            [D, H, D, D, C, C, C, C, S, C],
            [D, H, D, H, H, H, H, C, S, C],
            [D, H, D, H, H, H, H, C, S, C],
            [S, H, D, H, H, H, H, C, S, C],
            [S, H, D, C, C, C, C, C, S, C],
            [S, H, D, D, D, D, D, D, S, C],
            [S, H, H, H, H, C, C, C, C, C],
            [N, S, S, S, S, S, S, S, S, N],
        ]
        ranks = [
            [N, 6, 7, 8, 9, T, Q, K, A, N],
            [5, 3, 2, 2, 3, 4, 5, 6, 7, A],
            [4, 4, K, A, A, K, Q, T, 8, K],
            [3, 5, Q, Q, T, 9, 8, 9, 9, Q],
            [2, 6, T, K, 3, 2, 7, 8, T, T],
            [A, 7, 9, A, 4, 5, 6, 7, Q, 9],
            [K, 8, 8, 2, 3, 4, 5, 6, K, 8],
            [Q, 9, 7, 6, 5, 4, 3, 2, A, 7],
            [T, T, Q, K, A, 2, 3, 4, 5, 6],
            [N, 9, 8, 7, 6, 5, 4, 3, 2, N],
        ]
        cells = []
        for r in range(cls.ROWS):
            row = []
            for c in range(cls.COLUMNS):
                row.append(Cell.from_values(rank=ranks[r][c], suit=suits[r][c]))
            cells.append(row)
        return cls(cells=cells)

    def find_sequences_for_player(self, player: Player, win_count: int):
        def condition(cell: Cell):
            return cell.player == player or cell.is_wild
        yield from matrix.get_valid_sequences(self.cells, self.SEQUENCE_LENGTH, condition, win_count)

    def find_valid_cells(self, card: 'Card', player: 'Player'):
        if card.is_one_eyed_jack:
            moves = self._all_occupied(player)
        elif card.rank == Rank.JACK:  # TWO EYED JACK WILD
            moves = self._all_unoccupied()
        else:
            moves: List[Tuple[int, int]] = self._cells_by_card[card]
            moves = [m for m in moves if not self.cells[m[0]][m[1]].is_occupied]
        if moves is not None and not moves:
            raise DeadCardError(f"No valid moves found for {card}")
        return moves

    @staticmethod
    def _hashmap(cells) -> Dict['Card', List[Tuple[int, int]]]:
        cell_map = collections.defaultdict(list)
        for r, row in enumerate(cells):
            for c, cell in enumerate(row):
                cell_map[cell.card].append((r, c))
        return cell_map

    def _all_occupied(self, player: 'Player'):
        moves = []
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                if cell.is_occupied and not cell.player == player:
                    moves.append((r, c))
        return moves

    def _all_unoccupied(self):
        moves = []
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                if not cell.is_occupied and not cell.is_wild:
                    moves.append((r, c))
        return moves