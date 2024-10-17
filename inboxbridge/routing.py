from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    name: str
    contains: str
    destination: str
    room: str = ""

    def validate(self):
        if not self.name.strip() or not self.contains.strip() or not self.destination.strip():
            raise ValueError("Rules need a name, search text and destination")
        return self

    def matches(self, message):
        return (not self.room or self.room == message.room) and self.contains.casefold() in message.text.casefold()


def route(message, rules):
    return sorted({rule.validate().destination for rule in rules if rule.matches(message)})
