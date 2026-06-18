import asyncio
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from protocol import Message, encode, decode

PORT = 18777
server_instance = None


async def create_client(username: str):
    reader, writer = await asyncio.open_connection("127.0.0.1", PORT)
    reg = Message("MSG", username, "general", "connected", time.time())
    writer.write(encode(reg))
    await writer.drain()
    return reader, writer


async def read_msg(reader, timeout: float = 3.0):
    raw = await asyncio.wait_for(reader.readline(), timeout=timeout)
    if not raw:
        return None
    return decode(raw)


def reset_state():
    import server as srv
    srv.users.clear()
    srv.rooms.clear()
    srv.rooms["general"] = set()
    srv.rate_limits.clear()


async def test_connect_disconnect():
    r, w = await create_client("disc_user")
    join_msg = await read_msg(r)
    assert join_msg is not None
    assert join_msg.type == "JOIN"
    assert "disc_user" in join_msg.body

    import server as srv
    assert "disc_user" in srv.users

    w.close()
    await w.wait_closed()
    await asyncio.sleep(0.05)

    assert "disc_user" not in srv.users
    assert "disc_user" not in srv.rooms["general"]
    print("  PASS test_connect_disconnect")


async def test_message_broadcast():
    a_r, a_w = await create_client("alice_br")
    await read_msg(a_r)
    b_r, b_w = await create_client("bob_br")
    await read_msg(b_r)
    await read_msg(a_r)

    chat = Message("MSG", "alice_br", "general", "hello!", time.time())
    a_w.write(encode(chat))
    await a_w.drain()

    received = await read_msg(b_r)
    assert received is not None
    assert received.type == "MSG"
    assert received.body == "hello!"
    assert received.sender == "alice_br"

    a_w.close()
    b_w.close()
    print("  PASS test_message_broadcast")


async def test_private_message():
    a_r, a_w = await create_client("alice_p2")
    await read_msg(a_r)
    b_r, b_w = await create_client("bob_p2")
    await read_msg(b_r)
    await read_msg(a_r)

    pm = Message("PM", "alice_p2", "general", "bob_p2 secret", time.time())
    a_w.write(encode(pm))
    await a_w.drain()

    received = await read_msg(b_r)
    assert received is not None
    assert received.type == "PM"
    assert received.body == "secret"
    assert received.sender == "alice_p2"

    a_w.close()
    b_w.close()
    print("  PASS test_private_message")


async def test_join_room():
    r, w = await create_client("room_user")
    await read_msg(r)

    join = Message("JOIN", "room_user", "", "python", time.time())
    w.write(encode(join))
    await w.drain()

    notify = await read_msg(r)
    assert notify is not None
    assert notify.type == "JOIN"
    assert "python" in notify.room

    import server as srv
    assert "room_user" in srv.rooms.get("python", set())

    w.close()
    print("  PASS test_join_room")


async def test_nick_change():
    r, w = await create_client("nick_old")
    await read_msg(r)

    nick = Message("NICK", "nick_old", "general", "nick_new", time.time())
    w.write(encode(nick))
    await w.drain()

    notify = await read_msg(r)
    assert notify is not None
    assert notify.type == "NICK"
    assert "nick_new" in notify.body

    import server as srv
    assert "nick_new" in srv.users
    assert "nick_old" not in srv.users

    w.close()
    print("  PASS test_nick_change")


async def main():
    import server as srv
    reset_state()

    global server_instance
    server_instance = await asyncio.start_server(
        srv.handle_client, "127.0.0.1", PORT,
    )
    print(f"Test server on 127.0.0.1:{PORT}")

    try:
        await test_connect_disconnect()
        reset_state()
        await test_message_broadcast()
        reset_state()
        await test_private_message()
        reset_state()
        await test_join_room()
        reset_state()
        await test_nick_change()
        print("\nAll server tests passed")
    finally:
        server_instance.close()
        await server_instance.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
