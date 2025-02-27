import sqlite3
import tempfile
import unittest
from pathlib import Path
from inboxbridge.messages import Message
from inboxbridge.routing import Rule
from inboxbridge.store import Store
from inboxbridge.outbox import Outbox


class AtomicTests(unittest.TestCase):
    def test_duplicate_update_does_not_resend(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inbox.sqlite3"
            store, outbox = Store(path), Outbox(path)
            try:
                message = Message("telegram", "1", "ops", "me", "failed")
                rules = [Rule("failures", "failed", "alerts")]
                self.assertTrue(store.ingest_routed(message, rules))
                self.assertFalse(store.ingest_routed(message, rules))
                self.assertEqual(len(outbox.list()), 1)
            finally:
                store.close()
                outbox.close()

    def test_failed_queue_insert_rolls_back_message(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "inbox.sqlite3")
            try:
                store.db.execute("""CREATE TRIGGER reject_outgoing BEFORE INSERT ON outgoing
                    BEGIN SELECT RAISE(ABORT, 'queue unavailable'); END""")
                with self.assertRaises(sqlite3.IntegrityError):
                    store.ingest_routed(Message("telegram", "1", "ops", "me", "failed"),
                                        [Rule("failures", "failed", "alerts")])
                self.assertEqual(store.messages(), [])
            finally:
                store.close()
