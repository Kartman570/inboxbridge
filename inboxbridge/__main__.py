import argparse
import json

from inboxbridge.messages import from_telegram
from inboxbridge.store import Store


def main():
    parser = argparse.ArgumentParser(description="A small durable chat inbox")
    parser.add_argument("--db", default="inbox.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("file")
    commands.add_parser("list")
    args = parser.parse_args()
    store = Store(args.db)
    try:
        if args.command == "ingest":
            with open(args.file, encoding="utf-8") as stream:
                update = json.load(stream)
            message = from_telegram(update)
            print(json.dumps({"inserted": bool(message and store.ingest(message))}))
        else:
            print(json.dumps(store.messages(), indent=2))
    finally:
        store.close()


if __name__ == "__main__":
    main()
