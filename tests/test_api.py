import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from inboxbridge.api import create_app
from inboxbridge.routing import Rule


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.client = TestClient(create_app(Path(self.tmp.name) / "inbox.sqlite3", "test-key", "secret",
                                           [Rule("alert", "failed", "alerts")]))
        self.auth = {"Authorization": "Bearer test-key"}

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def test_webhook_to_search(self):
        update = {"update_id": 1, "message": {"chat": {"id": 10}, "text": "Build failed at 50%"}}
        self.assertEqual(self.client.post("/webhooks/telegram", json=update).status_code, 401)
        headers = {"X-Telegram-Bot-Api-Secret-Token": "secret"}
        self.assertTrue(self.client.post("/webhooks/telegram", json=update, headers=headers).json()["accepted"])
        self.assertFalse(self.client.post("/webhooks/telegram", json=update, headers=headers).json()["accepted"])
        self.assertEqual(self.client.get("/messages").status_code, 401)
        results = self.client.get("/search", params={"q": "50%"}, headers=self.auth).json()
        self.assertEqual(len(results), 1)
        self.assertEqual(self.client.get("/search", params={"q": "_"}, headers=self.auth).json(), [])
        self.assertEqual(self.client.get("/messages", params={"limit": 0}, headers=self.auth).status_code, 422)

    def test_bad_update(self):
        response = self.client.post("/webhooks/telegram", json={"message": {"text": "hello"}},
                                    headers={"X-Telegram-Bot-Api-Secret-Token": "secret"})
        self.assertEqual(response.status_code, 422)
