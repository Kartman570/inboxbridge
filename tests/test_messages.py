import tempfile
import unittest
from pathlib import Path

from inboxbridge.messages import Message, from_telegram
from inboxbridge.store import Store


class InboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "inbox.sqlite3")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_duplicate_survives_reopen(self):
        message = Message("telegram", "9", "4", "7", "hello")
        self.assertTrue(self.store.ingest(message))
        self.store.close()
        self.store = Store(Path(self.tmp.name) / "inbox.sqlite3")
        self.assertFalse(self.store.ingest(message))
        self.assertEqual(len(self.store.messages()), 1)

    def test_non_text_is_ignored(self):
        self.assertIsNone(from_telegram({"update_id": 1, "message": {"photo": []}}))

    def test_validation(self):
        with self.assertRaises(ValueError):
            Message("telegram", "1", "2", "3", " ").validate()
