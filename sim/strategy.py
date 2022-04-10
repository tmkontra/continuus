import random


class Strategy:
    def select_card(self, hand) -> int:
        raise NotImplemented

    def select_move(self, moves) -> int:
        pass


class RandomStrategy(Strategy):
    """Selects a random card, and a random move
    """

    def select_card(self, hand) -> int:
        return random.randint(0, len(hand)-1)

    def select_move(self, moves) -> int:
        return random.randint(0, len(moves)-1)


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