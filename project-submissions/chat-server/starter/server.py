# Chat Server
#
# TODO: Accept multiple client connections via asyncio TCP server
# TODO: Track connected users (username -> StreamWriter)
# TODO: Track rooms (room_name -> set of usernames)
# TODO: Handle MSG (broadcast to room), PM (direct message)
# TODO: Handle NICK (change username), JOIN (join/create room)
# TODO: Handle LEAVE (leave room), USERS (list users in room)
# TODO: Implement rate limiting per user
# TODO: Clean up on disconnect -- remove from users, rooms

import asyncio
import time

HOST = "0.0.0.0"
PORT = 7777


async def handle_client(reader: asyncio.StreamReader,
                        writer: asyncio.StreamWriter):
    pass


async def main():
    pass


if __name__ == "__main__":
    asyncio.run(main())
