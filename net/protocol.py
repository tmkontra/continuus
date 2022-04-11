import enum
import pickle
from dataclasses import dataclass
from typing import Optional, Any


class Status(enum.IntEnum):
    ack = 1
    err = 2
    unsupport = 3


class Action(enum.Enum):
    JOIN = "join"
    LEAVE = "leave"
    MOVE = "move"
    POLL = "poll"


class Serde:
    @classmethod
    def serialize(cls, this):
        return pickle.dumps(this)

    @classmethod
    def deserialize(cls, bytestring):
        return pickle.loads(bytestring)


@dataclass
class Request(Serde):
    action: Action
    value: Any
    player_id: Optional[str]


@dataclass
class Reply(Serde):
    status: Status
    value: Optional[str] = None
