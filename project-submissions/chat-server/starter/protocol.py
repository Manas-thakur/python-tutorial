# Message Protocol
#
# TODO: Define Message dataclass: type, sender, room, body, timestamp
# TODO: encode(msg) -> bytes -- serialize Message to JSON + newline
# TODO: decode(raw) -> Message -- parse JSON bytes back to Message
# TODO: Support types: MSG, PM, JOIN, LEAVE, NICK, USERS, OK, ERROR

import json
import time
from dataclasses import dataclass


@dataclass
class Message:
    type: str = ""
    sender: str = ""
    room: str = ""
    body: str = ""
    timestamp: float = 0.0


def encode(msg: Message) -> bytes:
    pass


def decode(raw: bytes) -> Message:
    pass
