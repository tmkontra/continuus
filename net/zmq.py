import logging
import time

import zmq

from net.dispatch import ActionDispatch
from net.protocol import Request, Reply, Action, Status


class ClientZMQ:
    def __init__(self, addr):
        self.context = zmq.Context()
        self.socket = socket = self.context.socket(zmq.REQ)
        addr = "ipc://" + addr
        socket.connect(addr)

    def send(self, msg: Request, immediate=False):
        out = Request.serialize(msg)
        immediate = zmq.NOBLOCK if immediate else 0
        try:
            self.socket.send(out, immediate)
            return self._recv()
        except zmq.error.Again:
            if immediate:
                return None
            else:
                raise

    def _recv(self, immediate=False) -> Reply:
        immediate = zmq.NOBLOCK if immediate else 0
        received: bytes = self.socket.recv(immediate)
        return Reply.deserialize(received)


class HostServerZMQ:
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
            elif action == Action.POLL:
                status, reply = self.dispatch.poll(player_id=player_id)
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