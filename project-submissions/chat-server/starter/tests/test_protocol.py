# Protocol Tests
#
# TODO: Test encode/decode round-trip for all message types
# TODO: Test that encoded messages end with newline
# TODO: Test unicode body handling
# TODO: Test large body handling
# TODO: Test empty field handling

from protocol import Message, encode, decode


def test_encode_decode_roundtrip():
    pass


def test_all_message_types():
    pass


def test_encode_ends_with_newline():
    pass


if __name__ == "__main__":
    test_encode_decode_roundtrip()
    test_all_message_types()
    test_encode_ends_with_newline()
    print("All protocol tests passed")
