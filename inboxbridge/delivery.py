import argparse
import json
import os

from inboxbridge.outbox import Outbox
from inboxbridge.telegram import Telegram
from inboxbridge.worker import deliver_one


def main():
    parser = argparse.ArgumentParser(description="Inspect or process outgoing messages")
    parser.add_argument("--db", default="inbox.sqlite3")
    parser.add_argument("command", choices=["list", "once", "stats", "replay"])
    parser.add_argument("--id", type=int)
    args = parser.parse_args()
    if args.command == "replay" and args.id is None:
        parser.error("replay requires --id")
    box = Outbox(args.db)
    try:
        if args.command == "list":
            print(json.dumps(box.list(), indent=2))
        elif args.command == "stats":
            print(json.dumps(box.stats()))
        elif args.command == "replay":
            print(json.dumps({"replayed": box.replay(args.id)}))
        else:
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            print(json.dumps({"processed": deliver_one(box, Telegram(token))}))
    finally:
        box.close()


if __name__ == "__main__":
    main()
