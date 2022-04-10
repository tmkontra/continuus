import collections
import itertools
import pickle
from collections import Callable
from dataclasses import dataclass
from typing import List

from console import ConsoleGame
from lib.game import Game
from lib.model import InvalidCellSelection, DeadCardError, Board, Card, Player
from sim.strategy import StrategyProvider, RandomStrategy


@dataclass
class PlayerPerspectiveBoard:
    cells: List[int]  # 0 = empty, 1 = you, 2/3 = other player/team

    @classmethod
    def from_board(cls, board: Board, get_pid: Callable):
        cells = []
        for row in board.cells:
            for cell in row:
                if cell.is_occupied:
                    cells.append(get_pid(cell.player))
                else:
                    cells.append(0)
        return cls(cells=cells)


@dataclass
class PlayerPerspectiveState:
    board: PlayerPerspectiveBoard  # the cell states
    hand: List[Card]  # the players hand state

    @classmethod
    def from_game(cls, game: Game, player: Player):
        # rotate players so player of interest is index 0
        pid = game.players.index(player)
        player_q = collections.deque(game.players)
        player_q.rotate(pid)
        player_list = list(player_q)

        def get_player_id(cell_player: Player):
            return player_list.index(cell_player) + 1

        board = PlayerPerspectiveBoard.from_board(
            game.board, get_player_id
        )
        return cls(board=board, hand=player.hand)


@dataclass
class PlayerPerspectiveOutcome:
    states: List[PlayerPerspectiveState]
    outcome: int


class CPUSim:
    CPU_NAMES = ["Abbott", "Bionicle", "Cleopatra", "David", "Erasmus", "Fergus"]

    def __init__(self, num_players, strategies: StrategyProvider=None, step=False):
        self.players = list(itertools.islice(self.CPU_NAMES, num_players))
        self.game = Game(self.players)
        self.strategy_provider: StrategyProvider = strategies or StrategyProvider.constant(RandomStrategy())
        self._step = step
        self._replay_buffers = collections.defaultdict(list)

    def _get_strategy(self, player):
        return self.strategy_provider(player.name)

    def save_buffers(self, f):
        buffers = list(self._replay_buffers.values())
        pickle.dump(buffers, f)

    def run(self):
        game = self.game
        started = steps = 0
        while not game.winner():
            if not self._step or steps > 0:
                current_player = game.next_player()
                card, moves = self.try_play_card(game, current_player)
                while True:
                    try:
                        select = self._get_strategy(current_player).select_move(moves)
                        select -= 1
                        row, column = moves[select]
                        state = PlayerPerspectiveState.from_game(self.game, current_player)
                        self._replay_buffers[current_player].append(state)
                        game.take_turn(row, column, card, current_player)
                        break
                    except InvalidCellSelection as e:
                        continue
                steps -= 1
            else:
                if started:
                    cmd = input("Enter cmd [print]: ")
                    if cmd == "print":
                        console = ConsoleGame()
                        console._players = self.players
                        bd = console._render_board(self.game, current_player)
                        console._echo(bd)
                else:
                    started = 1
                more_steps = input("How many turns would you like to advance?: ")
                more_steps = int(more_steps)
                steps += more_steps

        return game.turn_count

    def try_play_card(self, game: 'Game', current_player):
        board = game.board
        while True:
            select = self._get_strategy(current_player).select_card(current_player.hand)
            card = current_player.select_card(select)
            try:
                return card, board.find_valid_cells(card, current_player)
            except DeadCardError:
                game.exchange_dead_card(current_player, card)