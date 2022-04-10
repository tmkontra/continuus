import collections
import itertools

from lib.model import Suit, generate_deck, Rank, Wild


def random_board():
    S = Suit.SPADES
    C = Suit.CLUBS
    D = Suit.DIAMONDS
    H = S.HEARTS
    N = None
    suits = [
        [N, C, C, C, C, S, S, S, S, N],
        [H, C, C, C, C, S, S, S, S, D],
        [H, H, C, C, C, S, S, S, D, D],
        [H, H, H, H, C, S, D, D, D, D],
        [H, H, H, H, H, D, D, D, D, D],
        [D, D, D, D, D, H, H, H, H, H],
        [D, D, D, D, S, C, H, H, H, H],
        [D, D, S, S, S, C, C, C, H, H],
        [D, S, S, S, S, C, C, C, C, H],
        [N, S, S, S, S, C, C, C, C, N],
    ]
    return suits


def _check_valid_board(board: 'Board'):
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
