from typing import Union, Tuple

from net.protocol import Status


ReplyArgs = Tuple[Status, str]


class ActionDispatch:
    def handle_join(self, name) -> Union[None, ReplyArgs]:
        pass

    def kick_player(self, player_id):
        pass

    def player_move(self, player_id, card, coordinate):
        pass

    def poll(self, player_id):
        pass