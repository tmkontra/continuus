import collections
import enum
import itertools
import random
from dataclasses import dataclass, field
from typing import Optional, Union, List, Iterator, Dict, Tuple

from lib import matrix

T = 10


class InvalidCellSelection(Exception):
    pass


def main():
    board = Board.new_board(["Tyler", "Madison"])
    while not board.winner():
        current_player = board.next_player()
        card, moves = try_play_card(board, current_player)
        while True:
            try:
                for i, move in enumerate(moves, 1):
                    print(f"{i}. {move}")
                try:
                    # inp = input("Select a move number: ")
                    inp = 1
                    select = int(inp)
                    select -= 1
                    row, column = moves[select]
                except (IndexError, ValueError) as e:
                    print(f"Invalid selection: {inp}")
                    continue
                board.turn(row, column, card, current_player)
                break
            except InvalidCellSelection as e:
                print(f"ERROR: {e}")
                continue
    print(f"{board.winner().name} won! ({board._turn_number} turns)")


def try_play_card(board, current_player):
    while True:
        print(f"{current_player.name}'s turn. Select a card to play")
        for i, potential_card in enumerate(current_player.hand, 1):
            print(f"{i}. {potential_card}")
        # inp = input("Select a move number: ")
        inp = 1
        select = int(inp)
        select -= 1
        card = current_player.select_card(select)
        try:
            return card, board.find_valid_cells(card, current_player)
        except DeadCardError as e:
            current_player.use_card(card)
            board._discard_pile.append(card)
            current_player.draw_card(board.draw_card)


class DeadCardError(Exception):
    pass


class Board:
    __DIM = 10
    ROWS = __DIM
    COLUMNS = __DIM
    SEQUENCE_LENGTH = 5

    def __init__(self, cells, players):
        self.cells: List[List[Cell]] = cells
        Board._check_valid_board(self)
        self._cells_by_card: Dict['Card', List[Tuple[int, int]]] = Board._hashmap(self.cells)
        self.players: List[Player] = players
        self.win_count = 2 if len(players) < 3 else 1
        self._turn_order = itertools.cycle(self.players)
        self._deck: Iterator[Card] = Board.new_deck()
        self._deal_initial_hands()
        self._discard_pile = []
        self._turn_number = 1

    @staticmethod
    def _check_valid_board(board: 'Board'):
        all_cells = itertools.chain.from_iterable(board.cells)
        card_count = collections.Counter([c.card for c in all_cells])
        incorrect = []
        for card in generate_deck():
            if card.rank != Rank.JACK:
                if card_count[card] != 2:
                    incorrect.append((card, card_count[card]))
        if card_count[Wild] != 4:
            incorrect.append(("Wild", card_count[Wild]))
        if incorrect:
            raise RuntimeError(f"Invalid board: {incorrect}")

    @staticmethod
    def new_deck() -> Iterator['Card']:
        single = generate_deck()
        doubled = single * 2
        random.shuffle(doubled)
        return iter(doubled)

    def next_player(self) -> 'Player':
        return next(self._turn_order)

    def winner(self):
        sequence_counts = collections.Counter(self._find_sequences())
        winning, high_count = next(iter(sequence_counts.most_common(1)), (None, 0))
        return winning if high_count >= self.win_count else None

    def turn(self, row, column, card: 'Card', player: 'Player'):
        cell = self._get_cell(row, column)
        player.use_card(card)
        result = Board._place(player, card, cell)
        self._discard_pile.append(card)
        player.draw_card(self.draw_card)
        self._turn_number += 1
        return result

    @staticmethod
    def _place(player, card: 'Card', cell: 'Cell'):
        print(f"Playing {card} on {cell}")
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

    def _get_cell(self, row, column):
        if row >= self.ROWS:
            raise InvalidCellSelection(f"Row must be between 0 and {self.ROWS}")
        if column >= self.COLUMNS:
            raise InvalidCellSelection(f"Column must be between 0 and {self.COLUMNS}")
        return self.cells[row][column]

    @classmethod
    def new_board(cls, player_names: list):
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
            [N, 9,  8, 7, 6, 5, 4, 3, 2, N],
        ]
        cells = []
        for r in range(cls.ROWS):
            row = []
            for c in range(cls.COLUMNS):
                # TODO rank int to Rank
                row.append(Cell.from_values(rank=ranks[r][c], suit=suits[r][c]))
            cells.append(row)
        for row in cells:
            print([c.card.debug for c in row])
        players = [Player(i, name) for i, name in enumerate(player_names)]
        return cls(cells=cells, players=players)

    def _deal_initial_hands(self):
        card_count = {
            2: 7,
            3: 6,
            4: 6,
            6: 5,
            8: 4,
            9: 4,
            10: 3,
            12: 3,
        }[len(self.players)]
        for i in range(card_count):
            for player in self.players:
                player.draw_card(self.draw_card)

    @classmethod
    def random_board(cls):
        S = Suit.SPADES
        C = Suit.CLUBS
        D = Suit.DIAMONDS
        H = S.HEARTS
        N = None
        suits = [
            [N, C, C, C, C, S, S, S, S, N],
            [H, C, C, C, C, S, S, S, S, D],
            [H, H, C, C, C, S, S, S, D, D],
            [H, H, H, H, C, S, D, D, D, D],
            [H, H, H, H, H, D, D, D, D, D],
            [D, D, D, D, D, H, H, H, H, H],
            [D, D, D, D, S, C, H, H, H, H],
            [D, D, S, S, S, C, C, C, H, H],
            [D, S, S, S, S, C, C, C, C, H],
            [N, S, S, S, S, C, C, C, C, N],
        ]

    def _find_sequences(self):
        for player in self.players:
            yield from self._find_sequences_for_player(player)

    def _find_sequences_for_player(self, player: 'Player'):
        for sequence in matrix.all_submatrix(self.cells, self.SEQUENCE_LENGTH):
            occupied = [
                cell.player == player or cell.is_wild
                for cell in sequence
            ]
            if all(occupied):
                yield player

    def draw_card(self) -> 'Card':
        try:
            return next(self._deck)
        except StopIteration:
            random.shuffle(self._discard_pile)
            self._deck = iter(list(self._discard_pile))
            self._discard_pile = []
            return self.draw_card()

    def find_valid_cells(self, card: 'Card', player: 'Player'):
        if card.is_one_eyed_jack:
            moves = self._all_occupied(player)
        elif card.rank == Rank.JACK:  # TWO EYED JACK WILD
            moves = self._all_unoccupied()
        else:
            moves: List[Tuple[int, int]] = self._cells_by_card[card]
            moves = [m for m in moves if self.cells[m[0]][m[1]].player != player]
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


def generate_deck():
    return [
        Card(s, r)
        for s in Suit
        for r in Rank
    ]


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

if __name__ == "__main__":
    main()