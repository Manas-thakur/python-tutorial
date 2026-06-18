import asyncio
import sys
import time
from protocol import Message, encode, decode

COLORS = {
    "MSG": "\033[94m",
    "PM": "\033[92m",
    "JOIN": "\033[93m",
    "LEAVE": "\033[91m",
    "NICK": "\033[95m",
    "ERROR": "\033[91m",
    "OK": "\033[96m",
    "RESET": "\033[0m",
}


def _ts(ts: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(ts))


async def receive_loop(reader: asyncio.StreamReader):
    while True:
        try:
            raw = await reader.readline()
            if not raw:
                print(f"{COLORS['LEAVE']}[disconnected from server]{COLORS['RESET']}")
                break
            msg = decode(raw)
            c = COLORS.get(msg.type, COLORS["RESET"])
            r = COLORS["RESET"]
            t = _ts(msg.timestamp)
            match msg.type:
                case "MSG" | "PM":
                    print(f"{c}[{t}][{msg.room}] {msg.sender}: {msg.body}{r}")
                case "JOIN" | "LEAVE" | "NICK":
                    print(f"{c}[{t}] {msg.body}{r}")
                case "ERROR":
                    print(f"{c}[{t}][error] {msg.body}{r}")
                case "OK":
                    print(f"{c}[{t}][ok] {msg.body}{r}")
        except (ConnectionError, asyncio.IncompleteReadError):
            print(f"{COLORS['LEAVE']}[connection lost]{COLORS['RESET']}")
            break


async def send_loop(writer: asyncio.StreamWriter, username: str):
    loop = asyncio.get_running_loop()
    stdin_reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(stdin_reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await stdin_reader.readline()
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
            if msg.type == "ERROR":
                print(f"{COLORS['ERROR']}[{_ts(msg.timestamp)}] {msg.body}{COLORS['RESET']}")
                continue
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
        print(f"{COLORS['ERROR']}Could not connect to server at 127.0.0.1:7777{COLORS['RESET']}")
        return

    reg = Message("MSG", username, "general", "connected", time.time())
    writer.write(encode(reg))
    await writer.drain()

    await asyncio.gather(
        receive_loop(reader),
        send_loop(writer, username),
    )


if __name__ == "__main__":
    asyncio.run(main())
