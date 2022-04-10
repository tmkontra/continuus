from typing import Callable, Any

from rich import console, table, box
from rich.prompt import Prompt, Confirm
from rich.style import Style
from rich.text import Text

from console import utils
from console.lobby import ConsoleLobby
from lib.game import Game
from lib.model import Player, InvalidCellSelection, DeadCardError, Card


class ConsoleGame:
    def __init__(self, use_console=None):
        self._console = use_console or console.Console()
        self._players = []
        self._colors = {
            "red": "red",
            "black": "black",
            "wild": "white",
        }
        self._lobby: ConsoleLobby = ConsoleLobby()
        self._game: Game = None
        # self.teams = None

    def start(self):
        self.open_lobby()
        self.close_lobby()
        self._play()

    def _play(self):
        game = self._game
        while not game.winner():
            current_player: Player = game.next_player()
            self._echo(f"{current_player} is up next")
            self._handle_turn(game, current_player)
        return game.turn_count

    def _handle_turn(self, game: Game, current_player: Player):
        card, moves = self._select_card_to_play(game, current_player)
        while True:
            try:
                move = self._select_move_to_make(game, current_player, moves)
                row, column = move
                game.take_turn(row, column, card, current_player)
                break
            except InvalidCellSelection as e:
                continue

    def _prompt_choice(self, prompt: str, options: list, render: Callable[[Any], str] = str):
        return utils.prompt_choice(prompt, options, render, self._echo)

    def _select_card_to_play(self, game: Game, current_player: Player):
        while True:
            card = self._prompt_choice(
                "Select a card to play",
                current_player.hand,
                self._card_text
            )
            try:
                return card, game.board.find_valid_cells(card, current_player)
            except DeadCardError:
                self._echo(f"Exchanging dead card: {card}")
                game.exchange_dead_card(current_player, card)

    def _card_text(self, card: Card):
        text = Text(str(card))
        text.stylize(self._card_color(card))
        return text

    def _card_color(self, card):
        if card.black:
            return Style(color=self._colors["black"])
        elif card.red:
            return Style(color=self._colors["red"])
        else:
            return Style(color=self._colors["wild"], bgcolor="black")

    def _select_move_to_make(self, game: Game, player, possible_moves):
        display = self._render_board(game, player, possible_moves)
        self._echo(display)
        return self._prompt_choice("Select a move to make", possible_moves)

    @property
    def players(self):
        return self._players

    @players.setter
    def players(self, value):
        self._players = [Player(str(i), name) for i, name in enumerate(value)]

    def _echo(self, message):
        self._console.print(message)

    def open_lobby(self, lobby_handler=None):
        self._lobby.open()
        if lobby_handler is not None:
            lobby_handler()
        else:
            self._local_lobby(self._lobby)

    @staticmethod
    def _local_lobby(lobby):
        players = []
        while True and len(players) < 12:
            player = Prompt.ask("Enter a players name")
            lobby.add_player(player)
            if len(players) >= 2:
                more = Confirm.ask("Add another player?")
                if not more:
                    break

    def _get_teams(self):
        teams = []
        use_teams = Confirm.ask("Playing on teams?")
        if not use_teams:
            return
        self._echo("First declare the team names")
        while True:
            team_name = Prompt.ask("Enter team name")
            teams.append(team_name)
            more = Confirm.ask("Add another team?")
            if not more:
                break
        team_list = []
        assigned = set()
        for team in teams:
            team_members = []
            while True:
                options = [p for p in self.players if p not in assigned]
                for i, player in enumerate(options, 1):
                    self._echo(f"{i}. {player.name}")
                player_index = Prompt.ask(f"Add a player to team '{team}'")
                team_members.append(options[int(player_index)-1])
                more = Confirm.ask(f"Add another player to team '{team}'?")
                if not more:
                    break
            team_list.append([team, team_members])
        return teams

    def _render_board(self, game: Game, player: Player, moves=None):
        out = table.Table(
            min_width=(7 + 5)*game.board.COLUMNS,
            show_header=False, box=box.ROUNDED,
            padding=(0, 0)
        )
        for i in range(game.board.COLUMNS):
            out.add_column(vertical="middle", justify="center")
        if moves:
            moves = {
                m: i
                for i, m in enumerate(moves, 1)
            }
        else:
            moves = {}
        for r, row in enumerate(game.board.cells):
            outrow = []
            for c, cell in enumerate(row):
                move_index = moves.get((r, c))
                cell_text = self._fmt_cell(cell, game.color_for_player, player, move=move_index)
                outrow.append(cell_text)
            out.add_row(*outrow)
        return out

    def _fmt_cell(self, cell, get_color, player, move=None):
        CELL_HEADER = "*******\n"

        if cell.is_occupied:
            header = Text(CELL_HEADER, get_color(cell.player).value)
            occupy = ("O", get_color(cell.player).value)
            if move:
                header.stylize(Style(color="white", bgcolor=get_color(player).value))
                movetext = (f" {move}", get_color(player).value)
            else:
                movetext = ""
        else:
            header = Text(CELL_HEADER)
            occupy = ""
            if move:
                header.stylize(Style(color="white", bgcolor=get_color(player).value))
                movetext = (str(move), get_color(player).value)
            else:
                movetext = ""
        moveline = Text.assemble(occupy, movetext, "\n")
        text = Text.assemble(cell.card.debug, "\n")
        text.stylize(self._card_color(cell.card))
        outtext = Text()
        for line in [header, text, moveline, header]:
            outtext.append(line)
        return outtext

    def add_player_to_lobby(self, player):
        return self._lobby.add_player(player)

    def close_lobby(self):
        players = self._lobby.close()
        self._players = players
        self._game = Game(self._players)
