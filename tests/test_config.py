import tempfile
import unittest
from pathlib import Path
from inboxbridge.config import load_rules


class ConfigTests(unittest.TestCase):
    def test_duplicate_names(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules.json"
            path.write_text('[{"name":"one","contains":"x","destination":"a"},'
                            '{"name":"one","contains":"y","destination":"b"}]')
            with self.assertRaises(ValueError):
                load_rules(path)
