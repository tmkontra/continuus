from typing import Callable

from rich.prompt import Prompt
from rich.text import Text


def prompt_choice(prompt, options, render: Callable, echo):
    for i, option in enumerate(options, 1):
        num = Text(f"{i}.", "bold cyan")
        msg = Text.assemble(num, render(option))
        echo(msg)
    while True:
        index = Prompt.ask(prompt)
        try:
            index = int(index) - 1
            return options[index]
        except (IndexError, ValueError):
            echo(f"Please enter a selection 1 through {len(options)}")
            continue
