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
    if not isinstance(update, dict):
        raise ValueError("Update must be an object")
    message = update.get("message")
    if not isinstance(message, dict) or "text" not in message:
        return None
    chat = message.get("chat")
    sender = message.get("from", {})
    if not isinstance(chat, dict) or not isinstance(sender, dict):
        raise ValueError("Invalid chat or sender")
    if type(update.get("update_id")) is not int or type(chat.get("id")) is not int:
        raise ValueError("Update and chat IDs must be integers")
    return Message("telegram", str(update["update_id"]), str(chat["id"]),
                   str(sender.get("id", "unknown")), message["text"]).validate()
