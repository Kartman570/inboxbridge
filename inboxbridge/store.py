import json
import sqlite3

from inboxbridge.routing import route
from inboxbridge.outbox import Outbox


class Store:
    def __init__(self, path):
        queue = Outbox(path)
        queue.close()
        self.db = sqlite3.connect(path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS labels (
                message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                label TEXT NOT NULL, PRIMARY KEY(message_id, label)
            );
            CREATE TABLE IF NOT EXISTS archive (
                message_id INTEGER PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL,
                action TEXT NOT NULL, detail TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                room TEXT NOT NULL,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                UNIQUE(source, external_id)
            );
        """)

    def close(self):
        self.db.close()

    def ingest(self, message):
        message.validate()
        with self.db:
            cursor = self.db.execute(
                "INSERT OR IGNORE INTO messages(source, external_id, room, sender, text) VALUES(?,?,?,?,?)",
                (message.source, message.external_id, message.room, message.sender, message.text))
        return cursor.rowcount == 1

    def messages(self, after=0, limit=100):
        if after < 0 or not 1 <= limit <= 500:
            raise ValueError("Invalid page")
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM messages WHERE id>? ORDER BY id LIMIT ?", (after, limit))]

    def ingest_routed(self, message, rules):
        message.validate()
        destinations = route(message, rules)
        with self.db:
            cursor = self.db.execute(
                "INSERT OR IGNORE INTO messages(source, external_id, room, sender, text) VALUES(?,?,?,?,?)",
                (message.source, message.external_id, message.room, message.sender, message.text))
            if not cursor.rowcount:
                return False
            for destination in destinations:
                key = json.dumps([message.source, message.external_id, destination])
                self.db.execute(
                    "INSERT INTO outgoing(dedupe_key,destination,payload) VALUES(?,?,?)",
                    (key, destination, json.dumps({"text": message.text})))
        return True

    def search(self, query, room=None, after=0, limit=100):
        if not query.strip() or len(query) > 500 or after < 0 or not 1 <= limit <= 500:
            raise ValueError("Invalid search")
        needle = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql = "SELECT * FROM messages WHERE text LIKE ? ESCAPE '\\' AND id>?"
        values = ["%" + needle + "%", after]
        if room is not None:
            sql += " AND room=?"
            values.append(room)
        sql += " ORDER BY id LIMIT ?"
        values.append(limit)
        return [dict(row) for row in self.db.execute(sql, values)]

    def label(self, message_id, label):
        if not label.strip() or len(label) > 50:
            raise ValueError("Label must contain 1 to 50 characters")
        with self.db:
            if not self.db.execute("SELECT id FROM messages WHERE id=?", (message_id,)).fetchone():
                raise KeyError(message_id)
            changed = self.db.execute("INSERT OR IGNORE INTO labels VALUES(?,?)", (message_id, label)).rowcount
            if changed:
                self.db.execute("INSERT INTO activity(message_id,action,detail) VALUES(?,?,?)",
                                (message_id, "label", label))
        return bool(changed)

    def activity(self, message_id):
        return [dict(row) for row in self.db.execute(
            "SELECT id,action,detail FROM activity WHERE message_id=? ORDER BY id", (message_id,))]
