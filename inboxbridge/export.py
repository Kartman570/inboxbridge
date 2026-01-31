import json


def export_messages(store, stream):
    after = 0
    count = 0
    while True:
        page = store.messages(after=after, limit=500)
        if not page:
            return count
        for message in page:
            stream.write(json.dumps(message, ensure_ascii=False) + "\n")
            count += 1
        after = page[-1]["id"]
