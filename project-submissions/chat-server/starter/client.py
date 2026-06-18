# Chat Client
#
# TODO: Connect to server via asyncio.open_connection
# TODO: receive_loop -- read messages from server and display them
# TODO: send_loop -- read user input and send as chat messages
# TODO: Handle /slash commands by calling commands.parse_command
# TODO: Display messages with timestamps and colored output
# TODO: Handle disconnection gracefully

import asyncio
import sys
import time


async def receive_loop(reader: asyncio.StreamReader):
    pass


async def send_loop(writer: asyncio.StreamWriter, username: str):
    pass


async def main():
    pass


if __name__ == "__main__":
    asyncio.run(main())
