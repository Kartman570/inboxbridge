from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    name: str
    contains: str
    destination: str
    room: str = ""

    def validate(self):
        if any(not isinstance(value, str) for value in (self.name, self.contains, self.destination, self.room)):
            raise ValueError("Rule fields must be strings; quote numeric chat IDs")
        if not self.name.strip() or not self.contains.strip() or not self.destination.strip():
            raise ValueError("Rules need a name, search text and destination")
        return self

    def matches(self, message):
        return (not self.room or self.room == message.room) and self.contains.casefold() in message.text.casefold()


def route(message, rules):
    destinations = set()
    for rule in rules:
        rule.validate()
        if rule.matches(message):
            destinations.add(rule.destination)
    return sorted(destinations)
