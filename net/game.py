import os
import socketserver
import sys

from rich.console import Console


class Interface:
    def __init__(self):
        self._console = Console()

    def echo(self, message):
        self._console.print(message)


class ActionDispatch:
    def handle_join(self, name):
        pass


class NetworkedGameDispatch(ActionDispatch):
    def __init__(self, game: 'NetworkedGame'):
        self.game = game

    def handle_join(self, name):
        print(name, "joined!")


class GameServer(socketserver.UnixStreamServer):
    def __init__(self, dispatch: ActionDispatch, address, handler):
        super(GameServer, self).__init__(address, handler)
        self.dispatch = dispatch


class ServerRequestHandler(socketserver.BaseRequestHandler):
    BUFFER_SIZE = 1024
    server: GameServer

    def handle(self) -> None:
        # whitespace padded BUFFER_SIZE message
        while True:
            print("waiting for", self.client_address)
            try:
                try:
                    message = self.request.recv(self.BUFFER_SIZE).strip().decode("utf-8")
                    action, params = message.split(":")
                    if action == "join":
                        self.server.dispatch.handle_join(params)
                        self._reply("ack")
                    else:
                        print("Unsupported action:", action)
                        self._reply("err")
                except Exception:
                    self._reply("fatal")
            except BrokenPipeError:
                print("Conn closed from", self.client_address)
                break
                
    def _reply(self, message):
        self.request.sendall(self._encode(message))

    def _encode(self, message):
        return (message + "\n").encode("utf-8")


class NetworkedGame:
    def __init__(self, address):
        self._interface = Interface()
        self._server = GameServer(
            NetworkedGameDispatch(self), address, ServerRequestHandler
        )

    def start(self):
        self._lobby()

    def echo(self, message):
        self._interface.echo(message)

    def _lobby(self):
        self.echo("Starting lobby")
        with self._server as server:
            try:
                server.serve_forever()
            except:
                pass
        os.unlink(self._server.server_address)



if __name__ == "__main__":
    try:
        addr = sys.argv[1]
        game = NetworkedGame(addr)
        game.start()
    except Exception as e:
        print(e)
        sys.exit(1)