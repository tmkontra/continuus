import threading
from multiprocessing import Queue

import rich.prompt
import rich.prompt
from rich.console import Console
from rich.live import Live

from net.utils import make_thread


class Interface:
    def __init__(self):
        self._console = Console()
        self._update = Queue()

    def echo(self, message):
        self._console.print(message)

    def enqueue(self, render):
        self._update.put(render)

    def display_until(self, render, stop):
        display_thread = make_thread(target=self.live, args=(render, stop))
        return display_thread

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