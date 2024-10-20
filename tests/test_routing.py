import unittest
from inboxbridge.messages import Message
from inboxbridge.routing import Rule, route


class RoutingTests(unittest.TestCase):
    def test_room_and_case(self):
        message = Message("telegram", "1", "ops", "me", "BUILD failed")
        rules = [Rule("failures", "failed", "alerts"), Rule("builds", "build", "alerts"),
                 Rule("other", "failed", "elsewhere", "other-room")]
        self.assertEqual(route(message, rules), ["alerts"])

    def test_no_match(self):
        self.assertEqual(route(Message("telegram", "2", "ops", "me", "hello"),
                               [Rule("builds", "build", "alerts")]), [])
