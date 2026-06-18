import time
from protocol import Message, encode, decode


def test_encode_decode_roundtrip():
    msg = Message("MSG", "alice", "general", "hello world", 1700000000.0)
    raw = encode(msg)
    decoded = decode(raw)
    assert decoded.type == "MSG"
    assert decoded.sender == "alice"
    assert decoded.room == "general"
    assert decoded.body == "hello world"
    assert decoded.timestamp == 1700000000.0


def test_all_message_types():
    types = ["MSG", "PM", "JOIN", "LEAVE", "NICK", "USERS", "OK", "ERROR"]
    for t in types:
        msg = Message(t, "test", "room", "body", 12345.0)
        raw = encode(msg)
        decoded = decode(raw)
        assert decoded.type == t
        assert decoded.sender == "test"
        assert decoded.body == "body"


def test_encode_ends_with_newline():
    msg = Message("MSG", "a", "b", "c", 0.0)
    raw = encode(msg)
    assert raw.endswith(b"\n")


def test_decode_strips_whitespace():
    raw = b'{"type":"MSG","sender":"a","room":"b","body":"c","ts":0.0}\n  \n'
    msg = decode(raw)
    assert msg.type == "MSG"
    assert msg.sender == "a"


def test_unicode_body():
    msg = Message("MSG", "alice", "general", "héllo wörld 🌍", 1000.0)
    raw = encode(msg)
    decoded = decode(raw)
    assert decoded.body == "héllo wörld 🌍"


def test_message_dataclass_equality():
    ts = time.time()
    a = Message("MSG", "alice", "general", "hello", ts)
    b = Message("MSG", "alice", "general", "hello", ts)
    assert a == b


def test_empty_fields():
    msg = Message("OK", "", "", "", 0.0)
    raw = encode(msg)
    decoded = decode(raw)
    assert decoded.sender == ""
    assert decoded.room == ""
    assert decoded.body == ""


def test_large_body():
    body = "A" * 10000
    msg = Message("MSG", "a", "b", body, 0.0)
    raw = encode(msg)
    decoded = decode(raw)
    assert decoded.body == body
    assert len(raw) > 10000


if __name__ == "__main__":
    test_encode_decode_roundtrip()
    test_all_message_types()
    test_encode_ends_with_newline()
    test_decode_strips_whitespace()
    test_unicode_body()
    test_message_dataclass_equality()
    test_empty_fields()
    test_large_body()
    print("All protocol tests passed")
