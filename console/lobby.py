import secrets
from typing import List

from rich.table import Table

from lib.model import Player


class LobbyError(Exception):
    pass


class InvalidLobbyError(Exception):
    pass


class TeamsRequired(Exception):
    pass


class ConsoleLobby:
    def __init__(self, player_names: List[str] = None):
        self._players = []
        if player_names:
            for player_name in player_names:
                self.add_player(player_name)
        self._open = False

    @property
    def is_open(self):
        return self._open

    def render(self):
        table = Table()
        table.add_column("Player")
        for player in self._players:
            table.add_row(player.name)
        return table

    def add_player(self, player_name):
        if self.is_open:
            player = Player(id=secrets.token_hex(8), name=player_name)
            self._players.append(player)
            return player
        else:
            raise LobbyError("Lobby is closed!")

    def open(self):
        self._open = True

    def close(self):
        if 2 <= len(self._players) <= 3:
            pass
        elif 3 < len(self._players) <= 12:
            raise TeamsRequired
        else:
            raise InvalidLobbyError("Must have between 2 and 12 players!")
        self._open = False
        return self._players
