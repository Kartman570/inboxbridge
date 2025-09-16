import json
import sqlite3
import time
import uuid


class Outbox:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS outgoing (
                id INTEGER PRIMARY KEY, dedupe_key TEXT NOT NULL UNIQUE,
                destination TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                available REAL NOT NULL DEFAULT 0, lease TEXT, lease_until REAL,
                error TEXT NOT NULL DEFAULT ''
            );
        """)

    def close(self):
        self.db.close()

    def enqueue(self, key, destination, payload):
        if not key or not destination:
            raise ValueError("A key and destination are required")
        with self.db:
            cursor = self.db.execute(
                "INSERT OR IGNORE INTO outgoing(dedupe_key,destination,payload) VALUES(?,?,?)",
                (key, destination, json.dumps(payload)))
        return bool(cursor.rowcount)

    def claim(self, now=None, lease_seconds=60):
        now = time.time() if now is None else now
        token = uuid.uuid4().hex
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("""SELECT * FROM outgoing WHERE
                (status='pending' AND available<=?) OR (status='sending' AND lease_until<=?)
                ORDER BY id LIMIT 1""", (now, now)).fetchone()
            if row is None:
                return None
            self.db.execute("""UPDATE outgoing SET status='sending', lease=?, lease_until=?,
                attempts=attempts+1 WHERE id=?""", (token, now + lease_seconds, row['id']))
        return dict(row, lease=token, attempts=row['attempts'] + 1, payload=json.loads(row['payload']))

    def finish(self, item, error=None, now=None, max_attempts=5):
        now = time.time() if now is None else now
        status = "sent" if error is None else ("dead" if item['attempts'] >= max_attempts else "pending")
        delay = min(3600, 2 ** item['attempts'])
        with self.db:
            cursor = self.db.execute("""UPDATE outgoing SET status=?, error=?, available=?,
                lease=NULL, lease_until=NULL WHERE id=? AND lease=? AND status='sending'""",
                (status, str(error or '')[:200], now + delay, item['id'], item['lease']))
        return bool(cursor.rowcount)

    def list(self):
        return [dict(row) for row in self.db.execute("SELECT id,destination,status,attempts,error FROM outgoing ORDER BY id")]

    def replay(self, item_id):
        with self.db:
            cursor = self.db.execute("""UPDATE outgoing SET status='pending', attempts=0,
                available=0, error='', lease=NULL, lease_until=NULL WHERE id=? AND status='dead'""", (item_id,))
        return bool(cursor.rowcount)

    def stats(self):
        counts = {status: 0 for status in ("pending", "sending", "sent", "dead")}
        counts.update({row["status"]: row["count"] for row in self.db.execute(
            "SELECT status, COUNT(*) AS count FROM outgoing GROUP BY status")})
        return counts
