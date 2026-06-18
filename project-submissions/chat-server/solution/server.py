import asyncio
import time
from collections import defaultdict
from protocol import Message, encode, decode

users: dict[str, asyncio.StreamWriter] = {}
rooms: dict[str, set[str]] = {"general": set()}
rate_limits: dict[str, list[float]] = defaultdict(list)

MAX_MSG_PER_MINUTE = 30


async def broadcast(room: str, msg: Message, exclude: str | None = None):
    for uname in list(rooms.get(room, set())):
        if uname != exclude and uname in users:
            try:
                users[uname].write(encode(msg))
                await users[uname].drain()
            except (ConnectionError, OSError):
                pass


async def route_message(msg: Message):
    match msg.type:
        case "MSG":
            await broadcast(msg.room, msg, exclude=msg.sender)

        case "PM":
            parts = msg.body.split(maxsplit=1)
            if len(parts) >= 1:
                target = parts[0]
                text = parts[1] if len(parts) > 1 else ""
                pm = Message("PM", msg.sender, "", text, msg.timestamp)
                if target in users:
                    try:
                        users[target].write(encode(pm))
                        await users[target].drain()
                    except (ConnectionError, OSError):
                        pass
                else:
                    writer = users.get(msg.sender)
                    if writer:
                        err = Message("ERROR", "SERVER", "",
                            f"User '{target}' not found", time.time())
                        writer.write(encode(err))
                        await writer.drain()

        case "NICK":
            old = msg.sender
            new = msg.body.strip()
            if not new or new in users:
                writer = users.get(old)
                if writer:
                    err = Message("ERROR", "SERVER", "",
                        "Invalid or taken username", time.time())
                    writer.write(encode(err))
                    await writer.drain()
                return
            users[new] = users.pop(old)
            for room_set in rooms.values():
                if old in room_set:
                    room_set.remove(old)
                    room_set.add(new)
            notify = Message("NICK", "SERVER", msg.room,
                f"{old} is now known as {new}", msg.timestamp)
            await broadcast(msg.room, notify, exclude=None)

        case "JOIN":
            room = msg.body or "general"
            rooms.setdefault(room, set()).add(msg.sender)
            notify = Message("JOIN", "SERVER", room,
                f"{msg.sender} joined {room}", msg.timestamp)
            await broadcast(room, notify, exclude=None)

        case "LEAVE":
            rooms.get(msg.body, set()).discard(msg.sender)

        case "USERS":
            writer = users.get(msg.sender)
            if writer:
                current_room = next(
                    (r for r, m in rooms.items() if msg.sender in m),
                    "general",
                )
                members = sorted(rooms.get(current_room, set()))
                resp = Message("OK", "SERVER", current_room,
                    f"Users in {current_room}: {', '.join(members)}",
                    time.time())
                writer.write(encode(resp))
                await writer.drain()


async def handle_client(reader: asyncio.StreamReader,
                        writer: asyncio.StreamWriter):
    username = None
    try:
        while True:
            raw = await reader.readline()
            if not raw:
                break
            msg = decode(raw)

            if username is None:
                username = msg.sender
                users[username] = writer
                rooms["general"].add(username)
                join_msg = Message("JOIN", "SERVER", "general",
                    f"{username} joined the chat", time.time())
                await broadcast("general", join_msg, exclude=None)
            else:
                now = time.time()
                timestamps = rate_limits[username]
                timestamps[:] = [t for t in timestamps if now - t < 60]
                if len(timestamps) >= MAX_MSG_PER_MINUTE:
                    err = Message("ERROR", "SERVER", msg.room,
                        "Rate limit exceeded (30 msg/min)", now)
                    writer.write(encode(err))
                    await writer.drain()
                    continue
                timestamps.append(now)

                await route_message(msg)

    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        if username:
            users.pop(username, None)
            for room in rooms.values():
                room.discard(username)
            rate_limits.pop(username, None)
            leave_msg = Message("LEAVE", "SERVER", "general",
                f"{username} left the chat", time.time())
            await broadcast("general", leave_msg, exclude=None)
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 7777)
    addr = server.sockets[0].getsockname()
    print(f"Chat server listening on {addr[0]}:{addr[1]}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
