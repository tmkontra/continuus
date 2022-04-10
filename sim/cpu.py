import itertools

from console import ConsoleGame
from lib.game import Game
from lib.model import InvalidCellSelection, DeadCardError
from sim.strategy import StrategyProvider, FifoStrategy


class CPUSim:
    CPU_NAMES = ["Abbott", "Bionicle", "Cleopatra", "David", "Erasmus", "Fergus"]

    def __init__(self, num_players, strategies: StrategyProvider = None, step=False):
        self.players = list(itertools.islice(self.CPU_NAMES, num_players))
        self.game = Game(self.players)
        self.strategy_provider: StrategyProvider = strategies or (lambda _: FifoStrategy())
        self._step = step

    def _get_strategy(self, player):
        return self.strategy_provider(player.name)

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