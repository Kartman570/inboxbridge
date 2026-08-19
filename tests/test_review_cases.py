import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from inboxbridge.api import create_app
from inboxbridge.messages import Message
from inboxbridge.routing import Rule, route
from inboxbridge.store import Store


class ReviewCases(unittest.TestCase):
    def test_non_ascii_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            with TestClient(create_app(Path(directory) / "inbox.sqlite3", "key", "secret")) as client:
                self.assertEqual(client.get('/messages', headers={b'Authorization': b'Bearer \xff'}).status_code, 401)
                self.assertEqual(client.post('/webhooks/telegram', json={},
                    headers={b'X-Telegram-Bot-Api-Secret-Token': b'\xff'}).status_code, 401)

    def test_rule_types_are_checked_before_matching(self):
        message = Message('telegram', '1', 'room', 'sender', 'hello')
        for rule in (Rule('one', 'hello', 123), Rule('one', 1, 'room')):
            with self.assertRaises(ValueError):
                route(message, [rule])

    def test_cli_later_page(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'inbox.sqlite3'
            store = Store(path)
            try:
                for number in range(101):
                    store.ingest(Message('file', str(number), 'room', 'sender', 'hello'))
            finally:
                store.close()
            for args in (['list'], ['unread'], ['search', 'hello']):
                result = subprocess.run([sys.executable, '-m', 'inboxbridge', '--db', str(path),
                    *args, '--after', '100', '--limit', '1'], capture_output=True, text=True, check=True)
                self.assertEqual(json.loads(result.stdout)[0]['id'], 101)
