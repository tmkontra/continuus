import sys
import threading

from console import ConsoleGame
from console.interface import Interface
from console.lobby import ConsoleLobby
from lib.game import PublicGameState, Game
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
        self._refresh = None

    @property
    def game_started(self):
        return self._console_game is not None

    @property
    def game_winner(self):
        return self._console_game._game.winner()

    def run(self):
        self.game_loop()

    def game_loop(self):
        while not self._player_id:
            self.join_game()
        self._interface.echo("Entering lobby!")
        self.poll()
        stop_lobby, lobby_thread, self._refresh = self._render_lobby()
        while not self.game_started:
            self.poll()
        stop_lobby.set()
        lobby_thread.join()
        self._interface.echo("Game beginning!")
        while True:  # wait turn, move, repeat
            stop_board, board_thread, self._refresh = self._render_game()
            while not self.is_turn:
                self.poll()
            self.poll()
            stop_board.set()
            board_thread.join()
            self._handle_player_turn()
            self._refresh = None
            self.poll()

    def join_game(self):
        player_name = self._interface.prompt("Enter player name")
        resp = self._client.send(Request(Action.JOIN, player_name, player_id=self._player_id), immediate=True)
        if resp is None:
            self._interface.echo("No host found")
            return
        if resp.status == Status.ack:
            self._player_id = resp.value
        else:
            self._interface.echo("Lobby was not yet open, please try again.")

    def _handle_player_turn(self):
        card, move = self._console_game._handle_turn(self._console_game._game, self.player)
        message = Request(Action.MOVE, (card, move), self._player_id)
        reply = self._client.send(message)
        return reply

    def poll(self):
        reply = self._client.send(Request(Action.POLL, "", self._player_id))
        if reply.status == Status.ack:
            new_state = reply.value
            if new_state:
                if isinstance(new_state, ConsoleLobby):
                    self._lobby = new_state
                elif isinstance(new_state, PublicGameState):
                    self.set_state(new_state)
                if self._refresh is not None:
                    self.refresh_display(self._refresh)

    def set_state(self, new_state: PublicGameState):
        if not self._console_game:
            self._console_game = ConsoleGame(use_console=self._interface._console)
        self._state = new_state
        self._console_game._game = Game(new_state.players)
        self._console_game._game.board = new_state.board
        self._console_game.players = new_state.players

    @property
    def player(self):
        return self._state.player

    @property
    def board(self):
        return self._console_game._game.board

    @property
    def current_player_turn(self):
        return self._state.current_player_turn

    def _render_lobby(self):
        stop = threading.Event()
        t = self._interface.display_until(self.__render_lobby, stop)
        return stop, t, self.__render_lobby

    def __render_lobby(self):
        return self._lobby.render()

    def _render_game(self):
        stop = threading.Event()
        t = self._interface.display_until(self.__render_board, stop)
        return stop, t, self.__render_board

    def __render_board(self):
        return self._console_game._render_board(self._console_game._game, self.player)

    def refresh_display(self, render):
        self._interface.enqueue(render())

    @property
    def is_turn(self):
        try:
            return self.current_player_turn == self.player
        except:
            return False


if __name__ == "__main__":
    GameClient(sys.argv[1]).run()
