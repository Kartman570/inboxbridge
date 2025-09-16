import tempfile
import unittest
from pathlib import Path
from inboxbridge.outbox import Outbox
from inboxbridge.telegram import DeliveryError
from inboxbridge.worker import deliver_one


class FailingTransport:
    def send(self, destination, payload):
        raise DeliveryError("receiver unavailable")


class WorkerTests(unittest.TestCase):
    def test_failure_is_retried_then_replayed(self):
        with tempfile.TemporaryDirectory() as directory:
            box = Outbox(Path(directory) / "queue.sqlite3")
            try:
                box.enqueue("one", "room", {"text": "hello"})
                for step in range(5):
                    self.assertTrue(deliver_one(box, FailingTransport(), now=step * 100))
                self.assertEqual(box.stats()["dead"], 1)
                self.assertFalse(box.replay(999))
                self.assertTrue(box.replay(1))
                self.assertEqual(box.stats()["pending"], 1)
                self.assertEqual(box.claim(now=1000)["attempts"], 1)
            finally:
                box.close()
