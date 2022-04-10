import sys
import threading
import time

from rich import prompt

from console import ConsoleGame
from console.lobby import ConsoleLobby
from console.utils import prompt_choice
from lib.game import PublicGameState, Game
from console.interface import Interface

from net.protocol import Request, Action, Status
from net.zmq import ClientZMQ


class GameClient:
    def __init__(self, host_addr):
        self._interface = Interface()
        self._client = ClientZMQ(host_addr)
        self._player_id: str = None
        self._lobby: ConsoleLobby = None
        self._console_game: ConsoleGame = None
        self._state: PublicGameState = None

    def get_action(self):
        available_actions = [
            a for a in Action
            if (a != Action.JOIN) or (a == Action.JOIN and self._player_id is None)
        ]
        action = prompt_choice("Select action", available_actions, lambda r: r.value, print)
        if action == Action.JOIN:
            value = input("Player name: ")
        elif action == Action.MOVE:
            if self._console_game is None:
                raise ValueError("Still in lobby")
            card = prompt_choice("Select card to play", self.player.hand, str, print)
            move = prompt_choice("Select cell to play", self._console_game._game.board.find_valid_cells(card, self.player), str, print)
            value = (card, move)
        else:
            value = None
        return action, value

    def get_input(self, message: str):
        return prompt.Prompt.ask(message)

    def render(self):
        stop = threading.Event()
        if self._console_game:
            self._render_game(stop)
        elif self._lobby:
            self._render_lobby(stop)

    def run(self):
        player_name = self.get_input("Enter player name")
        resp = self._client.send(Request(Action.JOIN, player_name, player_id=self._player_id))
        if resp.status == Status.ack:
            print("Got player id", resp.value)
            self._player_id = resp.value
        self.poll()
        self.render()
        while True:
            self.render()
            try:
                action, value = self.get_action()
            except ValueError as e:
                print(e)
                continue
            if action == Action.POLL:
                self.poll()
            else:
                msg = Request(action, value, player_id=self._player_id)
                reply = self._client.send(msg)
                if reply.status == Status.ack:
                    print("OK.")

    def poll(self):
        reply = self._client.send(Request(Action.POLL, "", self._player_id))
        if reply.status == Status.ack:
            new_state = reply.value
            if new_state:
                if isinstance(new_state, ConsoleLobby):
                    self._lobby = new_state
                elif isinstance(new_state, PublicGameState):
                    self.set_state(new_state)

    def set_state(self, new_state: PublicGameState):
        print('set state')
        if not self._console_game:
            self._console_game = ConsoleGame(use_console=self._interface._console)
        self._state = new_state
        self._console_game._game = Game(new_state.players)
        self._console_game._game.board = new_state.board
        self._console_game.players = new_state.players
        self._refresh()

    @property
    def player(self):
        return self._state.player

    @property
    def board(self):
        return self._console_game._game.board

    @property
    def current_player_turn(self):
        return self._state.current_player_turn

    def _render_lobby(self, stop):
        t = self._interface.display_until(self.__render_lobby, stop)
        while True:
            self.poll()
            if self._console_game:
                stop.set()
                t.join()
                return
            else:
                self._interface.enqueue(self.__render_lobby())

    def __render_lobby(self):
        return self._lobby.render()

    def _refresh(self):
        render = self._console_game._render_board(self._console_game._game, self.player)
        self._interface.enqueue(render)

    def _render_game(self, stop):
        t = self._interface.display_until(self.__render_board, stop)
        while not self.is_turn:
            self.poll()
            self._interface.enqueue(self.__render_board())
        stop.set()
        t.join()
        self._interface.enqueue(self.__render_board())

    def __render_board(self):
        return self._console_game._render_board(self._console_game._game, self.player)

    @property
    def is_turn(self):
        try:
            return self.current_player_turn == self.player
        except:
            return False


if __name__ == "__main__":
    GameClient(sys.argv[1]).run()
