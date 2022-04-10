import logging
import os
import socketserver
import sys
import threading
import time
from multiprocessing import Queue
from time import sleep
from typing import List, Optional

import rich.prompt
import zmq
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from console import ConsoleGame
from lib.game import Game


class ActionDispatch:
    def handle_join(self, name):
        pass


class NetworkedGameDispatch(ActionDispatch):
    def __init__(self, game: 'NetworkedGame'):
        self.game = game

    def handle_join(self, name):
        if game.get_state() == "LOBBY":
            print(f"adding {name}")
            self.game.update_lobby(name)
            return True


class GameServerZMQ:
    def __init__(self, dispatch: ActionDispatch, address):
        self.context = zmq.Context()
        self.socket = sock = self.context.socket(zmq.REP)
        sock.bind("ipc://" + address)
        self.dispatch = dispatch

    def serve_forever(self):
        while True:
            message = self.socket.recv().decode("utf-8")
            reply = self.handle_message(message)
            self.socket.send(reply.encode("utf-8"))

    def handle_message(self, message):
        try:
            action, params = message.split(":")
            if action == "join":
                result = self.dispatch.handle_join(params)
                if result:
                    return "ack"
                else:
                    return "err"
            else:
                self.log("Unsupported action:", action)
                return "unsupport"
        except Exception as e:
            logging.exception(e)
            return str(e)

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
        return self._console.input()

    def confirm(self, prompt):
        return rich.prompt.Confirm.ask(prompt, console=self._console)


class NetworkedGame:
    def __init__(self, address):
        self._interface = Interface()
        self._dispatch = NetworkedGameDispatch(self)
        self._server = GameServerZMQ(self._dispatch, "/home/tmck/ordo")
        self._server_thread = None
        self._players = []
        self._game: Optional[Game] = None
        self._live = None
        self._state = "INIT"

    def get_state(self):
        return self._state

    def start(self):
        try:
            self._start_server()
            self._lobby()
            # self._teams()
            self._game = game = Game(self._players)
            console_game = ConsoleGame(use_players=self._players, use_console=self._interface._console)
            self._play(console_game)
        finally:
            try:
                os.unlink(self._server.server_address)
            except:
                pass

    def _start_server(self):
        self._server_thread = self._thread(target=self._server.serve_forever)

    def _lobby(self):
        self.echo("Starting lobby")
        stop = threading.Event()
        self._state = "LOBBY"
        self._display(self.render_lobby, stop)
        self.echo(">> Press enter to close lobby and begin game")
        self._interface.wait_for_input()
        stop.set()
        time.sleep(0.5)

    # def _teams(self):
    #     if self.confirm("Use teams?"):
    #         self._state = "TEAMS"
    #         teams = []
    #         while True:
    #             team = self.prompt("Enter team name")
    #             teams.append(team)
    #         self.echo("Press enter to save teams ")
    #         self._interface.wait_for_input()

    def _play(self, cg: ConsoleGame):
        while not self._game.winner():
            current_player = self._game.next_player()
            self._interface.echo(cg._render_board(self._game, current_player))
            input("Enter to advance")

    def update_lobby(self, player):
        self._players.append(player)
        self._interface.enqueue(self.render_lobby())

    def render_lobby(self):
        table = Table()
        table.add_column("Player")
        for player in self._players:
            table.add_row(player)
        return table

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


if __name__ == "__main__":
    try:
        addr = sys.argv[1]
        game = NetworkedGame(addr)
        game.start()
    except Exception as e:
        print(e)
        sys.exit(1)