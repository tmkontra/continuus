import collections
import itertools

from lib.model import generate_deck, Rank, Wild, Board


def _check_valid_board(board: Board):
    all_cells = itertools.chain.from_iterable(board.cells)
    card_count = collections.Counter([c.card for c in all_cells])
    incorrect = []
    for card in generate_deck():
        if card.rank != Rank.JACK:
            if card_count[card] != 2:
                incorrect.append((card, card_count[card]))
    if card_count[Wild] != 4:
        incorrect.append(("Wild", card_count[Wild]))
    if incorrect:
        raise RuntimeError(f"Invalid board: {incorrect}")
