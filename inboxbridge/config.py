import json
from pathlib import Path

from inboxbridge.routing import Rule


def load_rules(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("Rules must be a list")
    rules = [Rule(**item).validate() for item in value]
    if len({rule.name for rule in rules}) != len(rules):
        raise ValueError("Rule names must be unique")
    return rules
