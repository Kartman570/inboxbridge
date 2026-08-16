import argparse
import json
import sys

from inboxbridge.config import load_rules
from inboxbridge.export import export_messages

from inboxbridge.messages import from_telegram
from inboxbridge.store import Store


def main():
    parser = argparse.ArgumentParser(description="A small durable chat inbox")
    parser.add_argument("--db", default="inbox.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("file")
    ingest.add_argument("--rules")
    commands.add_parser("list")
    commands.add_parser("export")
    commands.add_parser("unread")
    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--room")
    for name in ("archive", "restore", "activity", "label"):
        command = commands.add_parser(name)
        command.add_argument("id", type=int)
        if name == "label":
            command.add_argument("label")
    args = parser.parse_args()
    store = Store(args.db)
    try:
        if args.command == "ingest":
            with open(args.file, encoding="utf-8") as stream:
                update = json.load(stream)
            message = from_telegram(update)
            rules = load_rules(args.rules) if args.rules else []
            print(json.dumps({"inserted": bool(message and store.ingest_routed(message, rules))}))
        elif args.command == "export":
            export_messages(store, sys.stdout)
        elif args.command == "search":
            print(json.dumps(store.search(args.query, args.room), indent=2))
        elif args.command == "unread":
            print(json.dumps(store.unread(), indent=2))
        elif args.command == "label":
            print(json.dumps({"changed": store.label(args.id, args.label)}))
        elif args.command in ("archive", "restore"):
            print(json.dumps({"changed": store.archive(args.id, args.command == "archive")}))
        elif args.command == "activity":
            print(json.dumps(store.activity(args.id), indent=2))
        else:
            print(json.dumps(store.messages(), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, "inboxbridge: " + str(error) + "\n")
    finally:
        store.close()


if __name__ == "__main__":
    main()
