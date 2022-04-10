import collections
import itertools
import json
import random
import statistics
import time
from typing import List, Dict, Tuple

from tqdm import tqdm

from lib import matrix
from lib.model import Card, Suit, Rank, Cell, Player, generate_deck



class InvalidCellSelection(Exception):
    pass


class Strategy:
    def select_card(self, hand) -> int:
        raise NotImplemented

    def select_move(self, moves) -> int:
        pass


class FifoStrategy(Strategy):
    def select_card(self, hand):
        return 1

    def select_move(self, moves):
        return 1


class RandomStrategy(Strategy):
    def select_card(self, hand) -> int:
        return random.randint(1, len(hand))

    def select_move(self, moves) -> int:
        return random.randint(1, len(moves))


class CPUSim:
    CPU_NAMES = ["Abbott", "Bionicle", "Cleopatra", "David", "Erasmus", "Fergus"]

    def __init__(self, num_players, strategy: Strategy = None):
        self.players = list(itertools.islice(self.CPU_NAMES, num_players))
        self.game = Game(self.players)
        self.strategy: Strategy = strategy or FifoStrategy()

    def run(self):
        game = self.game
        while not game.winner():
            current_player = game.next_player()
            card, moves = self.try_play_card(game, current_player)
            while True:
                try:
                    select = self.strategy.select_move(moves)
                    select -= 1
                    row, column = moves[select]
                    game.take_turn(row, column, card, current_player)
                    break
                except InvalidCellSelection as e:
                    continue
        # print(f"{game.winner().name} won! ({game.turn_count} turns)")
        return game.turn_count

    def try_play_card(self, game: 'Game', current_player):
        board = game.board
        while True:
            # inp = input("Select a move number: ")
            select = self.strategy.select_card(current_player.hand)
            select -= 1
            card = current_player.select_card(select)
            try:
                return card, board.find_valid_cells(card, current_player)
            except DeadCardError as e:
                game.exchange_dead_card(current_player, card)


class DeadCardError(Exception):
    pass


class Game:
    def __init__(self, player_names: List[str]):
        self.players: List[Player] = [Player(str(i), name) for i, name in enumerate(player_names)]
        self._turn_order = itertools.cycle(self.players)
        self.win_count = 2 if len(self.players) < 3 else 1
        self.board = Board.new_board()
        self._deck: List[Card] = Game.new_deck()
        self._deal_initial_hands()
        self._discard_pile = []
        self.turn_count = 0

    def next_player(self) -> Player:
        return next(self._turn_order)

    def winner(self):
        sequence_counts = collections.Counter(self._find_sequences())
        winning, high_count = next(iter(sequence_counts.most_common(1)), (None, 0))
        return winning if high_count >= self.win_count else None

    def take_turn(self, row, column, card: Card, player: Player):
        cell = self.board.get_cell(row, column)
        player.use_card(card)
        result = Board.claim_cell(player, card, cell)
        self._discard_pile.append(card)
        player.draw_card(self.draw_card)
        self.turn_count += 1
        return result

    def exchange_dead_card(self, player, card):
        player.use_card(card)
        self._discard_pile.append(card)
        player.draw_card(self.draw_card)

    def _find_sequences(self):
        for player in self.players:
            yield from self.board.find_sequences_for_player(player)

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

    def draw_card(self) -> Card:
        try:
            return self._deck.pop()
        except IndexError:
            random.shuffle(self._discard_pile)
            self._deck = list(self._discard_pile)
            self._discard_pile = []
            return self.draw_card()

    @staticmethod
    def new_deck() -> List['Card']:
        single = generate_deck()
        doubled = single * 2
        random.shuffle(doubled)
        return doubled


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
            [N, 9,  8, 7, 6, 5, 4, 3, 2, N],
        ]
        cells = []
        for r in range(cls.ROWS):
            row = []
            for c in range(cls.COLUMNS):
                row.append(Cell.from_values(rank=ranks[r][c], suit=suits[r][c]))
            cells.append(row)
        return cls(cells=cells)

    def find_sequences_for_player(self, player: Player):
        for sequence in matrix.all_submatrix(self.cells, self.SEQUENCE_LENGTH):
            occupied = [
                cell.player == player or cell.is_wild
                for cell in sequence
            ]
            if all(occupied):
                yield player

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


def simulate(n):
    results = collections.defaultdict(lambda: collections.defaultdict(list))
    for players in [2, 3, 4]:
        for _ in tqdm(range(n)):
            start = time.time()
            turns = CPUSim(players, FifoStrategy()).run()
            end = time.time()
            results[players]["time"].append(end - start)
            results[players]["turns"].append(turns)
    for pc, data in results.items():
        meantime = statistics.mean(data['time'])
        medtime = statistics.median(data['time'])
        meanturn = statistics.mean(data['turns'])
        medturn = statistics.median(data['turns'])
        tpt = []
        for totaltime, turns in zip(data['time'], data['turns']):
            tpt.append(totaltime / turns)
        meantpt = statistics.mean(tpt)
        dat = {
            "meantime": meantime,
            "mediantime": medtime,
            "meanturn": meanturn,
            "medianturn": medturn,
            "mean_time_per_turn": meantpt,
        }
        print(f"For {pc} players:")
        print(json.dumps(dat, indent=4))

if __name__ == "__main__":
    simulate(20)

