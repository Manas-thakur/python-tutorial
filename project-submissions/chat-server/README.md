---
title: Build a Chat Server & Client
author: Python Interactive Tutorial
uid: chat-server
datePublished: 2026-06-18
description: Build a multi-client TCP chat application with user authentication, chat rooms, private messaging, and slash commands — all powered by Python's asyncio.
published: false
readTime: 120
prerequisites: Python, Async basics
versions: Python 3.10+
tags:
  - intermediate
  - python
  - networking
---

## Introduction

Every chat app you've ever used — WhatsApp, Discord, Slack, IRC — shares the same fundamental architecture: a central server that routes messages between connected clients. In this project, you'll build one from scratch using only Python's standard library.

Here's what you'll learn:

- **TCP socket programming** — establish connections, send and receive bytes over the network
- **asyncio** — handle hundreds of concurrent clients in a single thread
- **Wire protocol design** — define a JSON-based message format with frame delimiters
- **Message routing** — broadcast to rooms, unicast private messages, handle join/part events
- **Command parsing** — implement slash commands like `/nick`, `/join`, `/pm`
- **Authentication** — register and log in with salted, hashed passwords
- **Testing networked code** — write tests for protocol encoding and server behavior

By the end, you'll have a fully functional multi-user chat system running in your terminal — and a deep understanding of how real-time messaging works under the hood.

## Setting Up

Create a new directory for the project:

```bash
mkdir chat-server
cd chat-server
```

Grab the starter template from our repo at [https://github.com/Manas-thakur/python-tutorial](https://github.com/Manas-thakur/python-tutorial) (path: `project-submissions/chat-server/starter/`).

Your project will end up with this structure:

```
chat-server/
├── protocol.py      # Message format, encode/decode helpers
├── server.py        # TCP server: accepts connections, routes messages
├── client.py        # Terminal client: concurrent send/receive loops
├── commands.py      # Slash command parser (/nick, /join, /pm, ...)
├── auth.py          # User registration and login with hashed passwords
├── users.json       # Stored user credentials (auto-generated)
└── tests/
    ├── test_protocol.py   # Round-trip encoding tests
    └── test_server.py     # Server behavior tests
```

**Python version:** You'll need Python 3.10+ for the `str | None` union syntax and `match` statement. If you're on an older version, use `Optional[str]` and `if/elif` chains instead.

There are no external dependencies. Everything uses Python's standard library.

## Step 1: Message Protocol (protocol.py)

Every message between client and server is a JSON object followed by a newline (`\n`). The newline acts as a frame delimiter so the receiver knows where one message ends and the next begins.

Create `protocol.py`:

```python
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
    return json.dumps(data).encode() + b"\n"


def decode(raw: bytes) -> Message:
    data = json.loads(raw.decode().strip())
    return Message(
        type=data["type"],
        sender=data["sender"],
        room=data["room"],
        body=data["body"],
        timestamp=data["ts"],
    )
```

**Why JSON?** Human-readable (you can `print()` raw bytes during debugging), every language supports it, and extra fields don't break old parsers — you can add features without breaking existing clients.

**Message types:**

| Type | Direction | Purpose |
|------|-----------|---------|
| `MSG` | Client → Server → Room | Broadcast a chat message |
| `PM` | Client → Server → User | Private message to one user |
| `JOIN` | Client → Server | Join a room |
| `LEAVE` | Client → Server | Leave a room / disconnect |
| `NICK` | Client → Server | Change nickname |
| `USERS` | Client → Server | Request user list |
| `OK` | Server → Client | Success response |
| `ERROR` | Server → Client | Error response |

**Wire format example:**

```
{"type":"MSG","sender":"alice","room":"general","body":"hello everyone","ts":1700000000.0}\n
```

**Dry run — encoding:**

```python
>>> encode(Message("MSG", "alice", "general", "hello", 1700000000.0))
b'{"type":"MSG","sender":"alice","room":"general","body":"hello","ts":1700000000.0}\n'
```

**Dry run — decoding:**

```python
>>> raw = b'{"type":"MSG","sender":"alice","room":"general","body":"hello","ts":1700000000.0}\n'
>>> decode(raw)
Message(type='MSG', sender='alice', room='general', body='hello', timestamp=1700000000.0)
```

## Step 2: Basic Server (server.py)

The server uses `asyncio.start_server` to accept TCP connections. Each connected client gets a dedicated coroutine that reads messages from the wire and dispatches them.

```python
import asyncio
import time
from protocol import Message, encode, decode


users: dict[str, asyncio.StreamWriter] = {}
rooms: dict[str, set[str]] = {"general": set()}


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
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
                await broadcast("general", Message(
                    "JOIN", "SERVER", "general",
                    f"{username} joined the chat", time.time(),
                ), exclude=None)
            else:
                await route_message(msg)
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        if username:
            users.pop(username, None)
            for room in rooms.values():
                room.discard(username)
            await broadcast("general", Message(
                "LEAVE", "SERVER", "general",
                f"{username} left the chat", time.time(),
            ), exclude=None)
        writer.close()


async def broadcast(room: str, msg: Message, exclude: str | None):
    for uname in rooms.get(room, set()):
        if uname != exclude and uname in users:
            try:
                users[uname].write(encode(msg))
                await users[uname].drain()
            except ConnectionError:
                pass


async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 7777)
    print("Chat server listening on 0.0.0.0:7777")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
```

**Data structures:**

- `users: dict[str, StreamWriter]` — maps username to the write end of their TCP connection. O(1) lookups for PM routing.
- `rooms: dict[str, set[str]]` — maps room name to a set of usernames. Fast membership checks and iteration for broadcast.

**Dry run — a client connects:**

1. `asyncio.start_server(handle_client, ..., 7777)` — kernel listens on port 7777
2. A TCP SYN arrives → kernel accepts, creates `(reader, writer)` pair
3. `handle_client` coroutine starts
4. First message arrives — say `{"type":"MSG","sender":"bob","room":"general","body":"hello"}`
5. `username` is `None`, so the server registers **bob**: `users["bob"] = writer`, adds bob to `rooms["general"]`
6. Broadcasts a JOIN message: "bob joined the chat"
7. Subsequent messages hit `route_message()` directly

**Why `await writer.drain()`?** `writer.write()` buffers data in memory. `drain()` flushes the buffer and back-pressures the producer if the OS buffer is full (the client is reading too slowly). Without it, a slow client causes unbounded memory growth on the server.

## Step 3: Client Connection (client.py)

The client needs two concurrent loops: one reads from the keyboard, the other reads from the network. If we only had one, typing a slow message would block us from hearing incoming messages.

```python
import asyncio
import sys
import time
from protocol import Message, encode, decode


async def receive_loop(reader: asyncio.StreamReader):
    while True:
        try:
            raw = await reader.readline()
            if not raw:
                print("[disconnected from server]")
                break
            msg = decode(raw)
            match msg.type:
                case "MSG" | "PM":
                    print(f"[{msg.room}] {msg.sender}: {msg.body}")
                case "JOIN" | "LEAVE" | "NICK":
                    print(f"[server] {msg.body}")
                case "ERROR":
                    print(f"[error] {msg.body}")
                case "OK":
                    print(f"[ok] {msg.body}")
        except (ConnectionError, asyncio.IncompleteReadError):
            print("[connection lost]")
            break


async def send_loop(writer: asyncio.StreamWriter, username: str):
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break
        text = line.decode().strip()
        if not text:
            continue

        if text.startswith("/"):
            from commands import parse_command
            result = parse_command(text)
            if result is None:
                continue
            msg = result
            msg.sender = username
            if msg.type == "LEAVE":
                writer.write(encode(msg))
                await writer.drain()
                writer.close()
                return
        else:
            msg = Message("MSG", username, "general", text, time.time())

        writer.write(encode(msg))
        await writer.drain()


async def main():
    username = input("Username: ").strip()
    if not username:
        username = "anonymous"

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", 7777)
    except ConnectionRefusedError:
        print("Could not connect to server. Is it running?")
        return

    msg = Message("MSG", username, "general", "connected", time.time())
    writer.write(encode(msg))
    await writer.drain()

    await asyncio.gather(
        receive_loop(reader),
        send_loop(writer, username),
    )


if __name__ == "__main__":
    asyncio.run(main())
```

**Why two concurrent loops?** Input functions like `input()` block the thread. If we called `input()` in the same coroutine that reads from the socket, we'd never see new messages while typing. By using `asyncio.gather()`, both loops run concurrently — `receive_loop` yields at `await reader.readline()` and `send_loop` yields at `await reader.readline()` (on stdin), so the event loop switches between them as data arrives.

**How stdin reading works:** Since `sys.stdin` is a blocking file descriptor, we use `loop.connect_read_pipe()` to wrap it in an asyncio `StreamReader`. This lets us `await` keyboard input just like we `await` network data — no threads needed.

## Step 4: Rooms & Broadcasting

Now implement the message routing logic. Add `route_message()` to `server.py`:

```python
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
                    except ConnectionError:
                        pass
                else:
                    writer = users.get(msg.sender)
                    if writer:
                        writer.write(encode(Message(
                            "ERROR", "SERVER", "",
                            f"User '{target}' not found", time.time(),
                        )))
                        await writer.drain()

        case "NICK":
            old = msg.sender
            new = msg.body.strip()
            if not new or new in users:
                writer = users.get(old)
                if writer:
                    writer.write(encode(Message(
                        "ERROR", "SERVER", "",
                        "Invalid or taken username", time.time(),
                    )))
                    await writer.drain()
                return
            users[new] = users.pop(old)
            for room_set in rooms.values():
                if old in room_set:
                    room_set.remove(old)
                    room_set.add(new)
            await broadcast(msg.room, Message(
                "NICK", "SERVER", msg.room,
                f"{old} is now known as {new}", time.time(),
            ), exclude=None)

        case "JOIN":
            room = msg.body
            if room not in rooms:
                rooms[room] = set()
            rooms[room].add(msg.sender)
            await broadcast(room, Message(
                "JOIN", "SERVER", room,
                f"{msg.sender} joined {room}", time.time(),
            ), exclude=None)

        case "LEAVE":
            rooms.get(msg.body, set()).discard(msg.sender)

        case "USERS":
            writer = users.get(msg.sender)
            if writer:
                room = next(
                    (r for r, m in rooms.items() if msg.sender in m), "general"
                )
                member_list = ", ".join(sorted(rooms.get(room, set())))
                writer.write(encode(Message(
                    "OK", "SERVER", room,
                    f"Users in {room}: {member_list}", time.time(),
                )))
                await writer.drain()
```

**Routing table:**

| Type | Action |
|------|--------|
| `MSG` | Broadcast to everyone in sender's room (excluding sender) |
| `PM` | Find target user's writer and send directly |
| `NICK` | Update username in `users` dict and all room sets |
| `JOIN` | Add user to a room (create if it doesn't exist) |
| `LEAVE` | Remove user from a room |
| `USERS` | List all users in sender's current room |

**Dry run — alice sends a PM to bob:**

1. Client sends bytes: `{"type":"PM","sender":"alice","room":"general","body":"bob hey whats up","ts":...}\n`
2. Server decodes → `Message("PM", "alice", "general", "bob hey whats up", ...)`
3. `route_message` hits the `PM` case
4. `msg.body.split(maxsplit=1)` → `["bob", "hey whats up"]`
5. `target = "bob"`, `text = "hey whats up"`
6. `"bob" in users` → `True`
7. `users["bob"].write(encode(pm))` — delivers directly to bob's socket
8. `drain()` ensures bytes leave the buffer

The `exclude` parameter in `broadcast()` prevents the sender from receiving their own messages echoed back.

## Step 5: Slash Commands (commands.py)

Slash commands give the user a way to control the client without a GUI. They're parsed from the raw input line and translated into the appropriate `Message` type.

Create `commands.py`:

```python
import shlex
import time
from protocol import Message


def parse_command(text: str) -> Message | None:
    if not text.startswith("/"):
        return None

    parts = shlex.split(text[1:])
    cmd = parts[0].lower() if parts else ""
    args = parts[1:] if len(parts) > 1 else []

    ts = time.time()

    match cmd:
        case "nick":
            if not args:
                return Message("ERROR", "CLIENT", "",
                    "Usage: /nick <new_username>", ts)
            return Message("NICK", "", "", args[0], ts)

        case "join":
            room = args[0] if args else "general"
            return Message("JOIN", "", "", room, ts)

        case "pm":
            if len(args) < 2:
                return Message("ERROR", "CLIENT", "",
                    "Usage: /pm <user> <message>", ts)
            return Message("PM", "", "", f"{args[0]} {' '.join(args[1:])}", ts)

        case "users":
            return Message("USERS", "", "", "", ts)

        case "quit":
            return Message("LEAVE", "", "general", "", ts)

        case "help":
            return Message("OK", "CLIENT", "",
                "Commands: /nick <name>  /join <room>  /pm <user> <msg>  "
                "/users  /quit  /help", ts)

        case _:
            return Message("ERROR", "CLIENT", "",
                f"Unknown command: /{cmd}. Type /help for commands.", ts)
```

**Why `shlex.split` instead of `str.split()`?** `shlex.split` respects quoted strings, so `/pm alice "hello there"` correctly produces `["pm", "alice", "hello there"]` with the message body intact.

**Dry run — typing "/join python":**

1. User types `/join python` and presses Enter
2. `send_loop` detects `line.startswith("/")` is `True`
3. Calls `parse_command("/join python")` → `shlex.split("join python")` → `["join", "python"]`
4. `cmd = "join"`, `args = ["python"]`
5. Returns `Message("JOIN", "", "", "python", timestamp)`
6. Client sets `msg.sender = username`, sends to server
7. Server's `route_message` hits the `JOIN` case: `rooms.setdefault("python", set()).add(username)`
8. Server broadcasts a JOIN notification to the "python" room

## Step 6: Authentication (auth.py)

Even a toy chat server should not store plaintext passwords. We use SHA-256 with a per-user random salt.

Create `auth.py`:

```python
import hashlib
import json
import os
from pathlib import Path

USERS_FILE = Path("users.json")


def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text())
    return {}


def _save_users(users: dict) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2))


def register(username: str, password: str) -> str | None:
    users = _load_users()
    if username in users:
        return "Username already taken"
    salt = os.urandom(16).hex()
    users[username] = {
        "salt": salt,
        "hash": _hash(password, salt),
    }
    _save_users(users)
    return None


def login(username: str, password: str) -> str | None:
    users = _load_users()
    if username not in users:
        return "User not found"
    record = users[username]
    if _hash(password, record["salt"]) != record["hash"]:
        return "Invalid password"
    return None
```

**Why hashing?** If someone gains access to `users.json`, they get **salted hashes**, not passwords. A salt prevents rainbow table attacks — two users with the same password get different hashes because their salts differ.

**Why not bcrypt / argon2?** This is a teaching project. In production, use a dedicated key-derivation function like `hashlib.pbkdf2_hmac` or `bcrypt`. The principle — never store plaintext — is what matters here.

**Dry run — register("alice", "pass123"):**

1. `_load_users()` → `{}` (file doesn't exist yet)
2. `"alice" not in {}` → `True`
3. `salt = os.urandom(16).hex()` → e.g. `"a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"`
4. `_hash("pass123", salt)` → `sha256("a1b2c3...5d6" + "pass123")` → `"9f8e..."` (64 hex chars)
5. `users["alice"] = {"salt": "a1b2...", "hash": "9f8e..."}`
6. Write `users.json`

**Dry run — login("alice", "pass123"):**

1. Load users, find alice's record
2. Recalculate hash with stored salt, compare — match → `return None` (success)
3. Wrong password → hash differs → `return "Invalid password"`

## Step 7: Running It

Open two (or more) terminal windows:

```bash
# Terminal 1 — start the server
python server.py
# Output: Chat server listening on 0.0.0.0:7777
```

```bash
# Terminal 2 — start a client
python client.py
Username: alice
```

```bash
# Terminal 3 — start another client
python client.py
Username: bob
```

Type messages in any terminal — they appear in all others connected to the same room.

### Commands

```
/join python          # Join or create a room
/nick alice_the_great  # Change your display name
/pm bob hey there      # Send a private message
/users                 # List users in current room
/help                  # Show available commands
/quit                  # Disconnect
```

### Running tests

```bash
python -m pytest tests/ -v
```

Or without pytest:

```bash
python tests/test_protocol.py
python tests/test_server.py
```

## Step 8: Extensions

Your chat server is working. Here are ways to take it further:

| Feature | Difficulty | How |
|---------|-----------|-----|
| **Message history** | Easy | Store `Message` objects in a `deque(maxlen=200)` per room, send last N on `JOIN` |
| **File sharing** | Medium | Base64-encode file data into `body`, set `type` to `"FILE"` with filename metadata |
| **End-to-end encryption** | Hard | Clients exchange public keys on connect, encrypt `body` with recipient's public key |
| **Web client** | Medium | Add a WebSocket listener in `server.py`, write a minimal HTML/JS chat UI |
| **IRC bridge** | Hard | Parse IRC protocol messages and translate between IRC commands and your Message types |
| **Rate limiting** | Easy | Track messages-per-minute per user, drop if over threshold (hint: `collections.deque` with maxlen) |
| **Typing indicators** | Easy | Send `TYPING` messages that expire after 3 seconds, show "... is typing" in the client |

**What you've learned:**

- TCP socket programming with asyncio
- JSON-based wire protocol with frame delimiters
- Message routing patterns (broadcast vs unicast)
- Concurrent I/O with `asyncio.gather` and `connect_read_pipe`
- Command parsing with `shlex`
- Password hashing with salt
- How real chat systems like IRC, Slack, and Discord work under the hood

## Conclusion

You built a fully functional multi-client TCP chat server from scratch — one that handles concurrent connections, routes messages to rooms, supports private messaging, and authenticates users with hashed passwords.

Here's what you accomplished:

- Designed a JSON-based wire protocol with a dataclass-backed message format
- Built an asyncio TCP server that accepts and manages hundreds of concurrent clients
- Implemented room-based message broadcasting with sender exclusion
- Created a terminal client with concurrent send/receive loops
- Parsed slash commands into structured messages using `shlex`
- Added user authentication with salted SHA-256 password hashing
- Wrote protocol and server tests to verify correctness

### Next Steps

- Add persistent message history so rejoining a room shows recent messages
- Implement file sharing via base64-encoded payloads
- Add end-to-end encryption using Python's `cryptography` library
- Build a web-based client using WebSockets
- Containerize the server with Docker for easy deployment
- Package your chat app with `pyproject.toml` and publish it to PyPI

The full source code for this tutorial is available at [https://github.com/Manas-thakur/python-tutorial](https://github.com/Manas-thakur/python-tutorial) (path: `project-submissions/chat-server/solution/`).
