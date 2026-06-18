from python_tutorial.models import ProjectTutorial, Section

TUTORIAL = ProjectTutorial(
    slug="chat-server",
    title="Build a Chat Server & Client",
    description="A multi-client TCP chat application with user authentication, rooms, and slash commands using asyncio.",
    difficulty="intermediate",
    project_dir="chat-server",
    prerequisites=["Functions", "Classes", "Async basics"],
    steps=[
        Section(
            heading="Step 1: Understanding the Architecture",
            content='''\
We\'ll build a TCP chat server that handles many concurrent clients using Python\'s `asyncio` module.

**Client-Server Model**

The server listens on a TCP port. Each client connects and the server assigns an `asyncio` task to handle that connection. This is the same model used by IRC, Discord gateways, and multiplayer games.

**TCP vs UDP**

| Protocol | Use Case | Trade-off |
|----------|----------|-----------|
| TCP      | Chat, HTTP, file transfer | Reliable, ordered, connection-oriented |
| UDP      | VoIP, video games, DNS | Fast, lossy, connectionless |

Chat needs reliable, ordered delivery — if a message arrives out of order the conversation doesn\'t make sense. We use TCP.

**Why asyncio?**

Thread-per-client wastes memory (~8 MB per thread). asyncio multiplexes thousands of connections in a single thread using cooperative multitasking. Each connection costs ~a few KB.

**Files in this project:**

```
chat-server/
├── protocol.py   # JSON message format, encode/decode helpers
├── server.py     # Main server: accepts connections, routes messages
├── client.py     # Terminal client: send/receive loops
├── commands.py   # Slash command parser (/nick, /join, /pm, etc.)
└── auth.py       # User registration & login with hashed passwords
```''',
        ),
        Section(
            heading="Step 2: Message Protocol (protocol.py)",
            content='''\
Every message between client and server uses JSON over TCP. A single message is a JSON object followed by a newline (`\\n`). The newline acts as a frame delimiter so the receiver knows where one message ends and the next begins.

```python
# protocol.py
import json
import time
from dataclasses import dataclass


@dataclass
class Message:
    type: str      # "MSG", "PM", "JOIN", "LEAVE", "NICK", "ERROR", "OK"
    sender: str    # username
    room: str      # room name
    body: str      # payload text
    timestamp: float  # seconds since epoch


def encode(msg: Message) -> bytes:
    data = {
        "type": msg.type,
        "sender": msg.sender,
        "room": msg.room,
        "body": msg.body,
        "ts": msg.timestamp,
    }
    return json.dumps(data).encode() + b"\\n"


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

**Why JSON?** Human-readable (you can `print()` the raw bytes during debugging), every language supports it, and it gracefully handles future fields (extra keys don\'t break old parsers).

**Dry run — encoding a message:**

```
encode(Message("MSG", "alice", "general", "hello", 1700000000.0))
```

1. Build dict: `{"type": "MSG", "sender": "alice", "room": "general", "body": "hello", "ts": 1700000000.0}`
2. `json.dumps(...)` → `\'{"type":"MSG","sender":"alice","room":"general","body":"hello","ts":1700000000.0}\'`
3. `.encode()` → bytes
4. Append `b"\\n"` → 73 raw bytes
5. Server reads until `\\n`, calls `decode()` and gets back a `Message` dataclass

**Wire format example:**

```
{"type":"MSG","sender":"alice","room":"general","body":"hello","ts":1700000000.0}\\n
```''',
        ),
        Section(
            heading="Step 3: Server Core (server.py)",
            content='''\
The server uses `asyncio.start_server` to accept TCP connections. Each client gets a dedicated coroutine that reads messages from the wire and dispatches them.

```python
# server.py
import asyncio
from protocol import Message, encode, decode

# Global state
users: dict[str, asyncio.StreamWriter] = {}    # username → writer
rooms: dict[str, set[str]] = {"general": set()}  # room → set of usernames


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
                if username not in rooms["general"]:
                    rooms["general"].add(username)
                await broadcast("general", Message("JOIN", "SERVER", "general",
                    f"{username} joined the chat", msg.timestamp), exclude=None)
            else:
                await route_message(msg)
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        if username:
            users.pop(username, None)
            for room in rooms.values():
                room.discard(username)
            await broadcast("general", Message("LEAVE", "SERVER", "general",
                f"{username} left the chat", time.time()), exclude=None)
        writer.close()


async def broadcast(room: str, msg: Message, exclude: str | None):
    for uname in rooms.get(room, set()):
        if uname != exclude and uname in users:
            users[uname].write(encode(msg))
            await users[uname].drain()


async def route_message(msg: Message):
    match msg.type:
        case "MSG":
            await broadcast(msg.room, msg, exclude=msg.sender)
        case "PM":
            parts = msg.body.split(maxsplit=1)
            if len(parts) >= 1:
                target = parts[0]
                text = parts[1] if len(parts) > 1 else ""
                pm = Message("PM", msg.sender, msg.room, text, msg.timestamp)
                if target in users:
                    users[target].write(encode(pm))
                    await users[target].drain()
        case "NICK":
            old = msg.sender
            new = msg.body.strip()
            users[new] = users.pop(old)
            for room_set in rooms.values():
                if old in room_set:
                    room_set.remove(old)
                    room_set.add(new)
            nick_msg = Message("NICK", "SERVER", msg.room,
                f"{old} is now known as {new}", msg.timestamp)
            await broadcast(msg.room, nick_msg, exclude=None)
        case "JOIN":
            rooms.setdefault(msg.body, set()).add(msg.sender)
            await broadcast(msg.body, Message("JOIN", "SERVER", msg.body,
                f"{msg.sender} joined {msg.body}", msg.timestamp), exclude=None)
        case "LEAVE":
            rooms.get(msg.body, set()).discard(msg.sender)


async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 7777)
    print("Chat server listening on 0.0.0.0:7777")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
```

**Dry run — a client connects:**

1. `asyncio.start_server(handle_client, ..., 7777)` — kernel listens on port 7777
2. A TCP SYN arrives → kernel accepts, creates `(reader, writer)` pair
3. `handle_client` coroutine starts
4. First message arrives — say `{"type":"MSG","sender":"bob","room":"general","body":"hello"}`
5. `username` is `None`, so server registers **bob**: `users["bob"] = writer`, adds bob to `rooms["general"]`
6. Broadcasts a JOIN message to everyone in "general"
7. Subsequent messages hit `route_message()` directly

**Data structures:**

- `users: dict[str, StreamWriter]` — maps username to the write end of their TCP connection. O(1) lookups for PM routing.
- `rooms: dict[str, set[str]]` — maps room name to a set of usernames. Fast membership checks and iteration for broadcast.

**Why `await writer.drain()`?** `writer.write()` buffers data. `drain()` flushes the buffer and back-pressures the producer if the OS buffer is full (client reading too slowly). Without it you risk unbounded memory growth.''',
        ),
        Section(
            heading="Step 4: Message Routing",
            content='''\
The `route_message()` function dispatches incoming messages by type. This is the brains of the server.

**Message types handled:**

| Type   | Action |
|--------|--------|
| `MSG`  | Broadcast to everyone in the sender\'s room (excluding sender) |
| `PM`   | Find the target user\'s writer and send directly (no broadcast) |
| `NICK` | Update username in `users` dict and all room sets |
| `JOIN` | Add user to a room\'s set |
| `LEAVE`| Remove user from a room\'s set |

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
                pm = Message("PM", msg.sender, msg.room, text, msg.timestamp)
                if target in users:
                    users[target].write(encode(pm))
                    await users[target].drain()
        case "NICK":
            old = msg.sender
            new = msg.body.strip()
            users[new] = users.pop(old)
            for room_set in rooms.values():
                if old in room_set:
                    room_set.remove(old)
                    room_set.add(new)
            await broadcast(msg.room, Message("NICK", "SERVER", msg.room,
                f"{old} is now known as {new}", msg.timestamp), exclude=None)
        case "JOIN":
            rooms.setdefault(msg.body, set()).add(msg.sender)
            await broadcast(msg.body, Message("JOIN", "SERVER", msg.body,
                f"{msg.sender} joined {msg.body}", msg.timestamp), exclude=None)
        case "LEAVE":
            rooms.get(msg.body, set()).discard(msg.sender)
```

**Dry run — alice sends a private message to bob:**

1. Client sends bytes: `{"type":"PM","sender":"alice","room":"general","body":"bob hey whats up","ts":...}\\n`
2. Server `handle_client` reads, calls `decode()`, gets `Message("PM", "alice", "general", "bob hey whats up", ...)`
3. `route_message(msg)` → `msg.type` is `"PM"` → the `PM` case runs
4. `msg.body.split(maxsplit=1)` → `["bob", "hey whats up"]`
5. `target = "bob"`, `text = "hey whats up"`
6. Checks `if "bob" in users:` → `True`
7. `users["bob"].write(encode(pm))` — sends the private message directly to bob\'s socket
8. `.drain()` ensures bytes leave the buffer

The `exclude` parameter in `broadcast()` prevents the sender from receiving their own messages echoed back — the server doesn\'t show "you said: hello" unless the client chooses to.''',
        ),
        Section(
            heading="Step 5: Client (client.py)",
            content='''\
The client needs two concurrent loops: one reads from the keyboard, the other reads from the network. If we only had one, typing a slow message would block us from hearing incoming messages.

```python
# client.py
import asyncio
import json
import time
from protocol import Message, encode, decode


async def receive_loop(reader: asyncio.StreamReader):
    """Continuously read messages from server and print them."""
    while True:
        try:
            raw = await reader.readline()
            if not raw:
                print("[disconnected from server]")
                break
            msg = decode(raw)
            match msg.type:
                case "MSG" | "PM" | "JOIN" | "LEAVE" | "NICK":
                    print(f"[{msg.room}] {msg.sender}: {msg.body}")
                case "ERROR":
                    print(f"[error] {msg.body}")
                case "OK":
                    print(f"[ok] {msg.body}")
        except (ConnectionError, asyncio.IncompleteReadError):
            print("[connection lost]")
            break


async def send_loop(writer: asyncio.StreamWriter, username: str):
    """Read lines from stdin and send them as chat messages."""
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
            cmd, _, args = text[1:].partition(" ")
            match cmd:
                case "nick":
                    msg = Message("NICK", username, "", args.strip(), time.time())
                case "join":
                    msg = Message("JOIN", username, "", args.strip(), time.time())
                case "pm":
                    target, _, body = args.partition(" ")
                    msg = Message("PM", username, "", f"{target} {body}", time.time())
                case "users":
                    msg = Message("USERS", username, "", "", time.time())
                case "quit":
                    msg = Message("LEAVE", username, "general", "", time.time())
                    writer.write(encode(msg))
                    await writer.drain()
                    writer.close()
                    return
                case _:
                    print(f"[unknown command] /{cmd}")
                    continue
        else:
            msg = Message("MSG", username, "general", text, time.time())

        writer.write(encode(msg))
        await writer.drain()


async def main():
    username = input("Username: ").strip()
    if not username:
        username = "anonymous"

    reader, writer = await asyncio.open_connection("127.0.0.1", 7777)

    # Register with server by sending a MSG with our username
    msg = Message("MSG", username, "general", "connected", time.time())
    writer.write(encode(msg))
    await writer.drain()

    await asyncio.gather(
        receive_loop(reader),
        send_loop(writer, username),
    )


if __name__ == "__main__":
    import sys
    asyncio.run(main())
```

**Why two concurrent loops?**

Input functions like `input()` block the thread. If we called `input()` in the same coroutine that reads from the socket, we\'d never see new messages while typing. By using `asyncio.gather()`, both loops run concurrently — `receive_loop` yields at `await reader.readline()` and `send_loop` yields at `await reader.readline()` (on stdin), so the event loop switches between them as data arrives.

**Dry run — client startup:**

1. `asyncio.open_connection("127.0.0.1", 7777)` → TCP handshake to server
2. Client sends a registration `Message("MSG", username, "general", "connected", ...)`
3. `asyncio.gather(receive_loop(...), send_loop(...))` spawns both as concurrent tasks
4. `receive_loop` hits `await reader.readline()` — blocked waiting for network data
5. `send_loop` hits `await reader.readline()` on stdin — blocked waiting for keyboard input
6. User types "hello" and presses Enter
7. `send_loop` wakes up, encodes `Message("MSG", "alice", "general", "hello", ...)`, writes to socket
8. Meanwhile, if bob sends a message, `receive_loop` wakes up and prints it — even if the user is mid-sentence''',
        ),
        Section(
            heading="Step 6: Slash Commands (commands.py)",
            content='''\
Slash commands give the user a way to control the client without a GUI. They\'re parsed from the raw input line and translated into the appropriate `Message` type.

```python
# commands.py
import shlex
from protocol import Message
import time


def parse_command(text: str) -> Message | None:
    """Parse a slash command from user input.

    Returns a Message ready to send, or None if the input is not a command.
    """
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
            return Message("PM", "", "", f"{args[0]} {\' \'.join(args[1:])}", ts)

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

**Why slash commands?**

They\'re zero-friction — no buttons, no dropdowns, no GUI framework. The same pattern powers IRC, Discord, Slack, and Twitch chat. A simple `str.startswith("/")` check in the client\'s `send_loop` is all you need to distinguish commands from ordinary chat.

**Dry run — typing "/join python":**

1. User types `/join python` and presses Enter
2. `send_loop` detects `line.startswith("/")` is `True`
3. Calls `parse_command(" /join python")` → `shlex.split("join python")` → `["join", "python"]`
4. `cmd = "join"`, `args = ["python"]`
5. Returns `Message("JOIN", "", "", "python", timestamp)`
6. Client sends this to server
7. Server\'s `route_message` hits the `JOIN` case: `rooms.setdefault("python", set()).add(username)`
8. Server broadcasts a JOIN notification to the "python" room
9. Client\'s `receive_loop` prints messages from the "python" room going forward

**Why `shlex.split` instead of `str.split()`?** `shlex.split` respects quoted strings, so `/pm alice "hello there"` correctly produces `["pm", "alice", "hello there"]` with the message body intact.''',
        ),
        Section(
            heading="Step 7: Authentication (auth.py)",
            content='''\
Even a toy chat server must not store plaintext passwords. We use SHA-256 with a per-user random salt.

```python
# auth.py
import hashlib
import json
import os
from pathlib import Path

USERS_FILE = Path("users.json")


def _hash(password: str, salt: str) -> str:
    """Return the hex digest of SHA-256(salt + password)."""
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text())
    return {}


def _save_users(users: dict) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2))


def register(username: str, password: str) -> str | None:
    """Register a new user. Returns None on success, error string on failure."""
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
    """Authenticate a user. Returns None on success, error string on failure."""
    users = _load_users()
    if username not in users:
        return "User not found"
    record = users[username]
    if _hash(password, record["salt"]) != record["hash"]:
        return "Invalid password"
    return None
```

**Why hashing?**

If someone gains access to `users.json`, they get **salted hashes**, not passwords. Even with SHA-256 (fast to compute), a salt prevents rainbow table attacks. Two users with the same password get different hashes because their salts differ.

**Why not bcrypt / argon2?** This is a teaching project. In production you should use a dedicated key-derivation function like `bcrypt` or `hashlib.pbkdf2_hmac`. The principle — never store plaintext — is what matters here.

**Dry run — register("alice", "pass123"):**

1. `_load_users()` → `{}` (file doesn\'t exist yet)
2. `"alice" not in {}` → `True`
3. `salt = os.urandom(16).hex()` → e.g. `"a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"`
4. `_hash("pass123", salt)` → `sha256("a1b2c3...5d6" + "pass123")` → `"9f8e7d6c5b4a3..."` (64 hex chars)
5. `users["alice"] = {"salt": "a1b2...", "hash": "9f8e..."}`
6. Write `users.json`: `{"alice": {"salt": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6", "hash": "9f8e7d6c5b4a3210fedcba9876543210fedcba9876543210fedcba9876543210"}}`

**Dry run — login("alice", "pass123"):**

1. `_load_users()` reads `users.json`
2. `"alice" in users` → `True`
3. Gets `salt = "a1b2..."`, recalculates `_hash("pass123", salt)` → `"9f8e..."`
4. Compares with stored hash → match → `return None` (success)

If someone typed the wrong password the hash would differ and `login()` returns `"Invalid password"`.''',
        ),
        Section(
            heading="Step 8: Running and Extensions",
            content='''\
**Running the project**

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

Type messages in any terminal — they appear in all others connected to the same room. Try the commands:

```
# Change nickname
/nick alice_the_great

# Join or create a room
/join python

# Send a private message
/pm bob hey, check out this project

# List users
/users

# Get help
/help

# Quit
/quit
```

**Ideas for extension**

| Feature | Difficulty | How |
|---------|-----------|-----|
| Message history | Easy | Store `Message` objects in a `deque(maxlen=200)` per room, send last N on `JOIN` |
| File sharing | Medium | Base64-encode file data into `body`, set `type` to `"FILE"` with filename in `room` |
| End-to-end encryption | Hard | Clients exchange public keys on connect, encrypt `body` with recipient\'s public key (only decryptable by the intended reader — server sees gibberish) |
| Web client | Medium | Add a WebSocket listener in `server.py` using `websockets` library, write a minimal HTML page |
| IRC protocol bridge | Hard | Parse IRC protocol messages and translate between IRC commands and your `Message` types |
| Rate limiting | Easy | Track messages-per-minute per user in a dict, drop if > threshold |

**What you\'ve learned:**

- TCP socket programming with asyncio
- JSON-based wire protocol design
- Message routing patterns (broadcast vs unicast)
- Concurrent I/O with `asyncio.gather`
- Command parsing with `shlex`
- Password hashing with salt
- How real chat systems like IRC and Slack work under the hood''',
        ),
    ],
)
