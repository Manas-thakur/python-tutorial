# Slash Commands
#
# TODO: Parse /command args from user input using shlex.split
# TODO: Support /nick <username> -- change display name
# TODO: Support /join <room> -- join or create a room
# TODO: Support /pm <user> <message> -- private message
# TODO: Support /users -- list users in current room
# TODO: Support /quit -- disconnect from server
# TODO: Support /help -- show available commands
# TODO: Return ERROR message for invalid usage

import shlex
import time

from protocol import Message


def parse_command(text: str) -> Message | None:
    pass
