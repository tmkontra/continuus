"""Unused socketserver implementation.

Too difficult to get working, switched to zeromq
"""
import socketserver

from net.game import ActionDispatch


class GameServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    def __init__(self, dispatch: ActionDispatch, address):
        super(GameServer, self).__init__(address, ServerRequestHandler)
        self.dispatch = dispatch

class ServerRequestHandler(socketserver.BaseRequestHandler):
    BUFFER_SIZE = 1024
    server: GameServer

    def log(self, *args):
        return

    def handle(self) -> None:
        # whitespace padded BUFFER_SIZE message
        while True:
            self.log("waiting for", self.client_address)
            try:
                try:
                    message = self.request.recv(self.BUFFER_SIZE).strip().decode("utf-8")
                    action, params = message.split(":")
                    if action == "join":
                        result = self.server.dispatch.handle_join(params)
                        if result:
                            self._reply("ack")
                        else:
                            self._reply("err")
                    else:
                        self.log("Unsupported action:", action)
                        self._reply("unsupport")
                except Exception:
                    self._reply("fatal")
            except BrokenPipeError:
                self.log("Conn closed from", self.client_address)
                break

    def _reply(self, message):
        self.request.sendall(self._encode(message))

    def _encode(self, message):
        return (message + "\n").encode("utf-8")
