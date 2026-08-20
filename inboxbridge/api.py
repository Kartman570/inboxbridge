import hmac
import os
from contextlib import contextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from inboxbridge.config import load_rules
from inboxbridge.messages import from_telegram
from inboxbridge.store import Store


def create_app(path=None, api_key=None, webhook_secret=None, rules=()):
    path = path or os.environ.get("INBOX_DB", "inbox.sqlite3")
    api_key = api_key or os.environ.get("INBOX_API_KEY", "")
    webhook_secret = webhook_secret or os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
    if not api_key or not webhook_secret:
        raise ValueError("INBOX_API_KEY and TELEGRAM_WEBHOOK_SECRET are required")
    if not rules and os.environ.get("INBOX_RULES"):
        rules = load_rules(os.environ["INBOX_RULES"])
    app = FastAPI(title="Inboxbridge")

    @contextmanager
    def inbox():
        store = Store(path)
        try:
            yield store
        finally:
            store.close()

    def authorize(authorization: str = Header(default="")):
        if not hmac.compare_digest(authorization.encode(), ("Bearer " + api_key).encode()):
            raise HTTPException(401, "Invalid API key")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/messages", dependencies=[Depends(authorize)])
    def messages(after: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
        with inbox() as store:
            return store.messages(after, limit)

    @app.get("/search", dependencies=[Depends(authorize)])
    def search(q: str = Query(min_length=1, max_length=500), room: str = None,
               after: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
        try:
            with inbox() as store:
                return store.search(q, room, after, limit)
        except ValueError as error:
            raise HTTPException(422, str(error)) from None

    @app.post("/webhooks/telegram")
    def receive(update: dict, x_telegram_bot_api_secret_token: str = Header(default="")):
        if not hmac.compare_digest(x_telegram_bot_api_secret_token.encode(), webhook_secret.encode()):
            raise HTTPException(401, "Invalid webhook secret")
        try:
            message = from_telegram(update)
            with inbox() as store:
                inserted = bool(message and store.ingest_routed(message, rules))
            return {"accepted": inserted}
        except (KeyError, TypeError, ValueError):
            raise HTTPException(422, "Invalid update") from None

    @app.post("/messages/{message_id}/archive", dependencies=[Depends(authorize)])
    def archive(message_id: int, archived: bool = True):
        with inbox() as store:
            try:
                return {"changed": store.archive(message_id, archived)}
            except KeyError:
                raise HTTPException(404, "Message not found") from None

    @app.post("/messages/{message_id}/labels", dependencies=[Depends(authorize)])
    def label(message_id: int, label: str = Query(min_length=1, max_length=50)):
        with inbox() as store:
            try:
                return {"changed": store.label(message_id, label)}
            except KeyError:
                raise HTTPException(404, "Message not found") from None
            except ValueError as error:
                raise HTTPException(422, str(error)) from None

    @app.get("/messages/{message_id}/activity", dependencies=[Depends(authorize)])
    def activity(message_id: int):
        with inbox() as store:
            return store.activity(message_id)

    return app
