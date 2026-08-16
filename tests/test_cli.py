import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def test_documented_inbox_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / "inbox.sqlite3")

            def command(*args):
                result = subprocess.run([sys.executable, "-m", "inboxbridge", "--db", db, *args],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            self.assertTrue(command("ingest", "examples/update.json", "--rules", "examples/rules.json")["inserted"])
            self.assertEqual(len(command("search", "failed")), 1)
            self.assertTrue(command("label", "1", "todo")["changed"])
            self.assertTrue(command("archive", "1")["changed"])
            self.assertEqual(command("unread"), [])
            self.assertEqual(command("export")["text"], "Build failed on the release branch")
            self.assertEqual(len(command("activity", "1")), 2)
