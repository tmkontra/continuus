import threading


def make_thread(target, args=None):
    t = threading.Thread(target=target, args=args or [])
    t.daemon = True
    t.start()
    return t