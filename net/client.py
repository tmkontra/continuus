import sys

import zmq


class ClientZMQ:
    def __init__(self, addr):
        self.context = zmq.Context()
        self.socket = socket = self.context.socket(zmq.REQ)
        addr = "ipc://" + addr
        print(addr)
        socket.connect(addr)

    def run(self):
        while True:
            msg = input("")
            self.socket.send(msg.encode("utf-8"))
            message = self.socket.recv()
            print(f"Received reply [ {message} ]")

c = ClientZMQ(sys.argv[1])
c.run()
