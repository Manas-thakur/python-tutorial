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
