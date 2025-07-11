import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from inboxbridge.telegram import Telegram, DeliveryError


class TransportTests(unittest.TestCase):
    def test_real_http_request(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"ok": true, "result": {"message_id": 7}}')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            sender = Telegram("test-token", "http://127.0.0.1:" + str(server.server_port))
            self.assertEqual(sender.send("alerts", {"text": "hello"}), {"message_id": 7})
            self.assertEqual(received, [("/bottest-token/sendMessage", {"chat_id": "alerts", "text": "hello"})])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_length_guard(self):
        with self.assertRaises(DeliveryError):
            Telegram("test").send("room", {"text": "x" * 4097})
