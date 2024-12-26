import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class DeliveryError(Exception):
    pass


class Telegram:
    def __init__(self, token, base_url="https://api.telegram.org"):
        if not token:
            raise ValueError("A bot token is required")
        self.url = base_url.rstrip("/") + "/bot" + token + "/sendMessage"

    def send(self, destination, payload):
        text = payload["text"]
        if not isinstance(text, str) or not 1 <= len(text) <= 4096:
            raise DeliveryError("Message exceeds the Telegram text limit")
        data = json.dumps({"chat_id": destination, "text": text}).encode()
        request = Request(self.url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=10) as response:
                result = json.load(response)
        except HTTPError as exc:
            raise DeliveryError("Telegram HTTP " + str(exc.code)) from None
        except (URLError, OSError, ValueError):
            raise DeliveryError("Telegram transport failed") from None
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise DeliveryError("Telegram rejected the message")
        return result.get("result", {})
