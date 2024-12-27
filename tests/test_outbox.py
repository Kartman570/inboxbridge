import tempfile
import unittest
from pathlib import Path
from inboxbridge.outbox import Outbox


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "queue.sqlite3"
        self.box = Outbox(self.path)

    def tearDown(self):
        self.box.close()
        self.tmp.cleanup()

    def test_exclusive_claim_and_stale_completion(self):
        self.box.enqueue("one", "room", {"text": "hello"})
        other = Outbox(self.path)
        try:
            first = self.box.claim(now=10)
            self.assertIsNone(other.claim(now=11))
            recovered = other.claim(now=71)
            self.assertFalse(self.box.finish(first, now=72))
            self.assertTrue(other.finish(recovered, now=72))
            self.assertEqual(self.box.list()[0]["status"], "sent")
        finally:
            other.close()

    def test_retry_budget(self):
        self.assertTrue(self.box.enqueue("one", "room", {"text": "hello"}))
        self.assertFalse(self.box.enqueue("one", "room", {"text": "hello"}))
        for attempt in range(5):
            item = self.box.claim(now=attempt * 100)
            self.box.finish(item, error="unavailable", now=attempt * 100)
        self.assertEqual(self.box.list()[0]["status"], "dead")
        self.assertIsNone(self.box.claim(now=10000))
