import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from inboxbridge.api import create_app
from inboxbridge.messages import from_telegram


class ValidationTests(unittest.TestCase):
    def test_malformed_chat_does_not_escape_validation(self):
        for chat in (None, [], {"id": None}, {"id": True}):
            with self.assertRaises(ValueError):
                from_telegram({"update_id": 1, "message": {"chat": chat, "text": "hello"}})

    def test_action_statuses(self):
        with tempfile.TemporaryDirectory() as directory:
            with TestClient(create_app(Path(directory) / "inbox.sqlite3", "key", "secret")) as client:
                headers = {"Authorization": "Bearer key"}
                self.assertEqual(client.post("/messages/1/archive", headers=headers).status_code, 404)
                self.assertEqual(client.post("/messages/1/labels?label=todo").status_code, 401)
                self.assertEqual(client.post("/messages/1/labels?label=todo", headers=headers).status_code, 404)
