import json
import time
from dataclasses import dataclass


@dataclass
class Message:
    type: str
    sender: str
    room: str
    body: str
    timestamp: float


def encode(msg: Message) -> bytes:
    data = {
        "type": msg.type,
        "sender": msg.sender,
        "room": msg.room,
        "body": msg.body,
        "ts": msg.timestamp,
    }
    return json.dumps(data, separators=(",", ":")).encode() + b"\n"


def decode(raw: bytes) -> Message:
    data = json.loads(raw.decode().strip())
    return Message(
        type=data["type"],
        sender=data["sender"],
        room=data["room"],
        body=data["body"],
        timestamp=data["ts"],
    )
