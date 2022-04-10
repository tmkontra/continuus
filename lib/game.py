import collections
import itertools
import random
from dataclasses import dataclass, field
from typing import List, Union

from lib.model import Player, Card, generate_deck, Board, Color


@dataclass
class PublicPlayer(Player):
    hand: List = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)


@dataclass
class PublicGameState:
    player: Player
    players: List[PublicPlayer]
    board: Board
    current_player_turn: Player

    def get_possible_moves(self, card):
        self.board.find_valid_cells(card, self.player)


class Game:
    def __init__(self, players: Union[List[str], List[Player]]):
        self.players: List[Player] = (
            [Player(str(i), name) for i, name in enumerate(players)]
            if isinstance(players[0], str)  # string names
            else players  # player objects already
        )
        self._colors = {
            self.players[i]: color
            for i, color in enumerate([Color.RED, Color.BLUE, Color.GREEN][:len(players)])
        }
        self._players_by_id = {
            p.id: p for p in self.players
        }
        self._turn_order = itertools.cycle(self.players)
        self.win_count = 2 if len(self.players) < 3 else 1
        self.board = Board.new_board()
        self._deck: List[Card] = Game.new_deck()
        self._deal_initial_hands()
        self._discard_pile = []
        self.turn_count = 0

    def color_for_player(self, player):
        return self._colors.get(player)

    def next_player(self) -> Player:
        return next(self._turn_order)

    def get_player(self, player_id):
        return self._players_by_id.get(player_id)

    def winner(self):
        sequence_counts = collections.Counter(self._find_sequences())
        winning, high_count = next(iter(sequence_counts.most_common(1)), (None, 0))
        return winning if high_count >= self.win_count else None

    def take_turn(self, row, column, card: Card, player: Player):
        cell = self.board.get_cell(row, column)
        player.use_card(card)
        result = Board.claim_cell(player, card, cell)
        self._discard_pile.append(card)
        player.draw_card(self.draw_card)
        self.turn_count += 1
        return result

    def exchange_dead_card(self, player, card):
        player.use_card(card)
        self._discard_pile.append(card)
        player.draw_card(self.draw_card)

    def _find_sequences(self):
        for player in self.players:
            yield from self.board.find_sequences_for_player(player)

    def _deal_initial_hands(self):
        card_count = {
            2: 7,
            3: 6,
            4: 6,
            6: 5,
            8: 4,
            9: 4,
            10: 3,
            12: 3,
        }[len(self.players)]
        for i in range(card_count):
            for player in self.players:
                player.draw_card(self.draw_card)

    def draw_card(self) -> Card:
        try:
            return self._deck.pop()
        except IndexError:
            random.shuffle(self._discard_pile)
            self._deck = list(self._discard_pile)
            self._discard_pile = []
            return self.draw_card()

    @staticmethod
    def new_deck() -> List['Card']:
        single = generate_deck()
        doubled = single * 2
        random.shuffle(doubled)
        return doubled

    def get_state_perspective(self, player: Player, current_player_turn: Player):
        return PublicGameState(
            players=[
                PublicPlayer(id=p.id, name=p.name) for p in self.players
            ],
            player=player,
            board=self.board,
            current_player_turn=current_player_turn
        )
