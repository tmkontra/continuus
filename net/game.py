import logging
import logging
import os
import sys
import threading
import time
from multiprocessing import Queue
from typing import Union, Tuple

import pytermgui.input
import rich.prompt
import zmq
from rich.console import Console
from rich.live import Live

from console import ConsoleGame
from console.lobby import InvalidLobbyError
from lib.model import Player
from net.protocol import Request, Reply, Status, Action

ReplyArgs = Tuple[Status, str]


class ActionDispatch:
    def handle_join(self, name) -> Union[None, ReplyArgs]:
        pass

    def kick_player(self, player_id):
        pass

    def player_move(self, player_id, card, coordinate):
        pass

    def poll(self, player_id):
        pass


class NetworkedGameDispatch(ActionDispatch):
    def __init__(self, game: 'NetworkedGame'):
        self.game = game

    def handle_join(self, name) -> Union[None, ReplyArgs]:
        if game.get_state() == "LOBBY":
            print(f"adding {name}")
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
        return self.game.get_player_state(player_id)


class GameServerZMQ:
    def __init__(self, dispatch: ActionDispatch, address):
        self.context = zmq.Context()
        self.socket = sock = self.context.socket(zmq.REP)
        sock.bind("ipc://" + address)
        self.dispatch = dispatch
        self._keepalive = {}

    def _check_connections(self):
        t = time.time()
        for player_id, last_ts in self._keepalive.items():
            if last_ts < t - 30:
                self.dispatch.kick_player(player_id)

    def serve_forever(self):
        while True:
            message = self._recv()
            reply = self.handle_message(message)
            self._send(reply)

    def _recv(self) -> Request:
        return Request.deserialize(self.socket.recv())

    def _send(self, reply: Reply):
        self.socket.send(Reply.serialize(reply))

    def handle_message(self, message: Request):
        try:
            action, params, player_id = message.action, message.value, message.player_id
            if player_id:
                self._keepalive[player_id] = time.time()
            if action == Action.JOIN:
                status, reply = self.dispatch.handle_join(params)
                return Reply(status, reply)
            elif action == Action.MOVE:
                status, reply = self.dispatch.player_move(player_id, *params)
                return Reply(status, reply)
            else:
                self.log("Unsupported action:", action)
                return Reply(Status.unsupport)
        except Exception as e:
            logging.exception(e)
            return Reply(Status.err, value=str(e))

    def log(self, *args):
        # TODO: stderr? logfile?
        return


class Interface:
    def __init__(self):
        self._log_console = Console()
        self._console = Console()
        self._update = Queue()

    def echo(self, message):
        self._console.print(message)

    def enqueue(self, render):
        self._update.put(render)

    def live(self, render, stop: threading.Event):
        with Live(render(), console=self._console, transient=False, auto_refresh=False) as live:
            while not stop.is_set():
                if not self._update.empty():
                    update = self._update.get(block=False)
                    live.update(update)
                    live.refresh()
            live.refresh()

    def prompt(self, message):
        return rich.prompt.Prompt.ask(message, console=self._console)

    def wait_for_input(self):
        return pytermgui.input.getch()

    def confirm(self, prompt):
        return rich.prompt.Confirm.ask(prompt, console=self._console)


class NetworkedGame:
    def __init__(self, address):
        self._interface = Interface()
        self._dispatch = NetworkedGameDispatch(self)
        self._server = GameServerZMQ(self._dispatch, address)
        self._server_thread = None
        self._console_game = ConsoleGame(use_console=self._interface._console)
        self._live = None
        self._state = "INIT"

    def get_state(self):
        return self._state

    def get_player_state(self, player_id):
        player = self._get_player(player_id)
        return self.game.get_state_perspective(player)

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
        self._server_thread = self._thread(target=self._server.serve_forever)

    def _do_lobby(self):
        self.echo("Starting lobby")
        self._console_game.open_lobby(self._handle_lobby)

    def _handle_lobby(self):
        stop = threading.Event()
        self._state = "LOBBY"
        display = self._display(self._console_game._lobby.render, stop)
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
        game = self.game
        while not game.winner():
            current_player = game.next_player()
            self._interface.echo(self._console_game._render_board(game, current_player))
            input("Enter to advance")

    def update_lobby(self, player):
        player = self._console_game.add_player_to_lobby(player)
        self._interface.enqueue(self._console_game._lobby.render())
        return player

    def render_teams(self):
        pass # TODO

    def _display(self, render, stop):
        display_thread = self._thread(target=self._interface.live, args=(render, stop))
        return display_thread

    def _thread(self, target, args=None):
        t = threading.Thread(target=target, args=args or [])
        t.daemon = True
        t.start()
        return t

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