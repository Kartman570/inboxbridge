import io
import json
import tempfile
import unittest
from pathlib import Path
from inboxbridge.export import export_messages
from inboxbridge.messages import Message
from inboxbridge.store import Store


class ActionTests(unittest.TestCase):
    def test_archive_labels_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "inbox.sqlite3")
            try:
                for i in range(501):
                    store.ingest(Message("file", str(i), "room", "me", "text " + str(i)))
                self.assertTrue(store.label(1, "todo"))
                self.assertFalse(store.label(1, "todo"))
                self.assertTrue(store.archive(1))
                self.assertEqual(store.unread(limit=1)[0]["id"], 2)
                self.assertTrue(store.archive(1, False))
                self.assertEqual(store.unread(limit=1)[0]["id"], 1)
                self.assertEqual(len(store.activity(1)), 3)
                with self.assertRaises(KeyError):
                    store.archive(999)
                output = io.StringIO()
                self.assertEqual(export_messages(store, output), 501)
                self.assertEqual(json.loads(output.getvalue().splitlines()[-1])["id"], 501)
            finally:
                store.close()
