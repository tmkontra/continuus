import pickle
import sys

import zmq

from console.utils import prompt_choice
from lib.game import PublicGameState
from net.protocol import Request, Reply, Action, Status


class ClientZMQ:
    def __init__(self, addr):
        self.context = zmq.Context()
        self.socket = socket = self.context.socket(zmq.REQ)
        addr = "ipc://" + addr
        print(addr)
        socket.connect(addr)

    def send(self, msg: Request):
        out = pickle.dumps(msg)
        self.socket.send(out)
        return self._recv()

    def _recv(self) -> Reply:
        received: bytes = self.socket.recv()
        return pickle.loads(received)


def _handle_reply(reply):
    print(f"Received reply [ {reply} ]")
    ack, value = reply.status, reply.value
    if ack == Status.ack:
        if value:
            print("Got reply", value)
            return value
        else:
            print("OK.")
    else:
        print("ERROR:", ack)


def get_action(state: PublicGameState = None, player_id=None):
    available_actions = [
        a for a in Action
        if (a != Action.JOIN) or (a == Action.JOIN and player_id is None)
    ]
    action = prompt_choice("Select action", available_actions, lambda r: r.value, print)
    if action == Action.JOIN:
        value = input("Player name: ")
    elif action == Action.MOVE:
        card = prompt_choice(state.)
        move = prompt_choice()
        value = (card, move)
    return action, value


def run(client):
    state = None
    player_id = None
    while True:
        action, value = get_action(state, player_id=player_id)
        msg = Request(action, value, player_id=player_id)
        reply = client.send(msg)
        new_state = _handle_reply(reply)
        if new_state and action == Action.JOIN:
            player_id = new_state
        elif new_state:
            state = new_state


if __name__ == "__main__":
    run(
        ClientZMQ(sys.argv[1])
    )
