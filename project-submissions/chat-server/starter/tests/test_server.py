# Server Tests
#
# TODO: Test client connect triggers JOIN broadcast
# TODO: Test client disconnect triggers LEAVE broadcast
# TODO: Test message broadcast reaches all room members
# TODO: Test PM reaches only the target user
# TODO: Test room join/part functionality
# TODO: Test NICK change updates username everywhere

import asyncio
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from protocol import Message, encode, decode


def test_connect_disconnect():
    pass


def test_message_broadcast():
    pass


def test_private_message():
    pass


def test_join_room():
    pass


if __name__ == "__main__":
    test_connect_disconnect()
    test_message_broadcast()
    test_private_message()
    test_join_room()
    print("All server tests passed")
