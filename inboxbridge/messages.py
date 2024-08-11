from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    source: str
    external_id: str
    room: str
    sender: str
    text: str

    def validate(self):
        for name in ("source", "external_id", "room", "sender"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 200:
                raise ValueError("Invalid " + name)
        if not isinstance(self.text, str) or not self.text.strip() or len(self.text) > 16000:
            raise ValueError("Text must contain between 1 and 16000 characters")
        return self


def from_telegram(update):
    message = update.get("message")
    if not isinstance(message, dict) or "text" not in message:
        return None
    return Message("telegram", str(update["update_id"]), str(message["chat"]["id"]),
                   str(message.get("from", {}).get("id", "unknown")), message["text"]).validate()
