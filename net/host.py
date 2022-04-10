import os
import sys
import threading
from queue import Queue
from typing import Union

from console import ConsoleGame
from console.interface import Interface
from console.lobby import InvalidLobbyError
from lib.model import Player
from net.dispatch import ActionDispatch, ReplyArgs
from net.protocol import Status
from net.utils import make_thread
from net.zmq import HostServerZMQ


class NetworkedGameDispatch(ActionDispatch):
    def __init__(self, game: 'NetworkedGame'):
        self.game = game

    def handle_join(self, name) -> Union[None, ReplyArgs]:
        if game.get_state() == "LOBBY":
            player: Player = self.game.update_lobby(name)
            return Status.ack, player.id

    def kick_player(self, player_id):
        # TODO: implement disconnect
        pass

    def player_move(self, player_id, card, coordinate):
        ok = self.game.player_move(player_id, card, coordinate)
        if ok:
            return Status.ack, self.get_state(player_id)
        else:
            return Status.err, None

    def poll(self, player_id):
        state = self.get_state(player_id)
        if state:
            return Status.ack, state
        else:
            return Status.err, None

    def get_state(self, player_id):
        if game.get_state() == "LOBBY":
            return self.game._console_game._lobby
        else:
            return self.game.get_player_state(player_id)


class NetworkedGame:
    def __init__(self, address):
        self._interface = Interface()
        self._dispatch = NetworkedGameDispatch(self)
        self._server = HostServerZMQ(self._dispatch, address)
        self._server_thread = None
        self._console_game = ConsoleGame(use_console=self._interface._console)
        self._live = None
        self._state = "INIT"
        self._next_move = Queue(maxsize=1)
        self._current_player = None

    def get_state(self):
        return self._state

    def get_player_state(self, player_id):
        player = self._get_player(player_id)
        return self.game.get_state_perspective(player, self._current_player)

    def start(self):
        try:
            self._start_server()
            self._do_lobby()
            # self._teams()
            self._play()
        finally:
            try:
                os.unlink(self._server.server_address)
            except:
                pass

    def _start_server(self):
        self._server_thread = make_thread(target=self._server.serve_forever)

    def _do_lobby(self):
        self.echo("Starting lobby")
        self._console_game.open_lobby(self._handle_lobby)

    def _handle_lobby(self):
        stop = threading.Event()
        self._state = "LOBBY"
        display = self._interface.display_until(self._console_game._lobby.render, stop)
        self.echo(">> Press enter to close lobby and begin game")
        while True:
            self._interface.wait_for_input()
            try:
                self._console_game.close_lobby()
                stop.set()
                display.join()
                return
            except InvalidLobbyError as e:
                self.echo(f">> {e}")
                continue

    # def _teams(self):
    #     if self.confirm("Use teams?"):
    #         self._state = "TEAMS"
    #         teams = []
    #         while True:
    #             team = self.prompt("Enter team name")
    #             teams.append(team)
    #         self.echo("Press enter to save teams ")
    #         self._interface.wait_for_input()

    def _play(self):
        self._state = "PLAY"
        game = self.game
        while not game.winner():
            current_player = game.next_player()
            self._interface.echo(self._console_game._render_board(game, current_player))
            self._wait_for_turn(current_player)
            input("Enter to advance")

    def _wait_for_turn(self, player: Player):
        self._state = "WAIT_TURN"
        self._current_player = player
        while self._next_move.empty():
            pass
        card, coordinate = self._next_move.get()
        self.player_move(player.id, card, coordinate)
        self._current_player = None

    def update_lobby(self, player):
        player = self._console_game.add_player_to_lobby(player)
        self._interface.enqueue(self._console_game._lobby.render())
        return player

    def render_teams(self):
        pass # TODO

    def echo(self, message):
        self._interface.echo(message)

    def prompt(self, message):
        self._interface.prompt(message)

    def confirm(self, prompt):
        self._interface.confirm(prompt)

    def player_move(self, player_id, card, coordinate):
        row, column = coordinate
        player = self._get_player(player_id)
        return self.game.take_turn(row, column, card, player)

    def _get_player(self, player_id):
        return self.game.get_player(player_id)

    @property
    def game(self):
        return self._console_game._game


if __name__ == "__main__":
    try:
        addr = sys.argv[1]
        game = NetworkedGame(addr)
        game.start()
    except Exception as e:
        print(e)
        sys.exit(1)