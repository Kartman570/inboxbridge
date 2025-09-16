import argparse
import json
import os

from inboxbridge.outbox import Outbox
from inboxbridge.telegram import Telegram
from inboxbridge.worker import deliver_one


def main():
    parser = argparse.ArgumentParser(description="Inspect or process outgoing messages")
    parser.add_argument("--db", default="inbox.sqlite3")
    parser.add_argument("command", choices=["list", "once"])
    args = parser.parse_args()
    box = Outbox(args.db)
    try:
        if args.command == "list":
            print(json.dumps(box.list(), indent=2))
        else:
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            print(json.dumps({"processed": deliver_one(box, Telegram(token))}))
    finally:
        box.close()


if __name__ == "__main__":
    main()
