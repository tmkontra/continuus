import random


class Strategy:
    def select_card(self, hand) -> int:
        raise NotImplemented

    def select_move(self, moves) -> int:
        pass


class FifoStrategy(Strategy):
    """Selects the first available card (FIFO), and the first available move (Top-left of the board)
    """

    def select_card(self, hand):
        return 0

    def select_move(self, moves):
        return 0


class RandomStrategy(Strategy):
    """Selects a random card, and a random move
    """

    def select_card(self, hand) -> int:
        return random.randint(1, len(hand))

    def select_move(self, moves) -> int:
        return random.randint(1, len(moves))


class StrategyProvider:
    """Given a player, returns their strategy
    """

    def __init__(self, callable):
        self._call = callable

    def __call__(self, player) -> Strategy:
        return self._call(player)

    @classmethod
    def constant(cls, strategy: Strategy):
        provider = StrategyProvider(lambda _: strategy)
        return provider