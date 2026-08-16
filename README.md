# Inboxbridge

A durable inbox for Telegram text updates. Keep incoming messages, route selected text to another chat, search the inbox, and track what has been processed.

## Run locally

Python 3.9 or later is enough for the CLI. The HTTP server needs the packages in `requirements.txt`.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python -m inboxbridge --db inbox.sqlite3 ingest examples/update.json --rules examples/rules.json
python -m inboxbridge --db inbox.sqlite3 list
python -m inboxbridge --db inbox.sqlite3 search failed
python -m inboxbridge --db inbox.sqlite3 label 1 todo
python -m inboxbridge --db inbox.sqlite3 archive 1
python -m inboxbridge --db inbox.sqlite3 activity 1
python -m inboxbridge --db inbox.sqlite3 export
python -m inboxbridge.delivery --db inbox.sqlite3 list
make test lint
```

The example destination is a placeholder. Set a real chat ID in your rules before enabling delivery.

## HTTP server

```sh
export INBOX_API_KEY=choose-a-long-private-key
export TELEGRAM_WEBHOOK_SECRET=choose-a-different-private-key
export INBOX_RULES=examples/rules.json
uvicorn inboxbridge.api:create_app --factory --host 127.0.0.1
```

`GET /messages` and `GET /search?q=failed` require `Authorization: Bearer <key>`. The inbox is a single trusted-user workspace, not a multi-tenant service. `POST /webhooks/telegram` requires Telegram's `X-Telegram-Bot-Api-Secret-Token` header. Configure that secret when registering the webhook with Telegram. Only text messages are handled; photos, edits and callback queries are ignored. Telegram webhook registration is a manual step.

`POST /messages/{id}/labels?label=todo`, `POST /messages/{id}/archive`, and `GET /messages/{id}/activity` provide the same actions as the CLI. Pass `archived=false` to restore a message.

`docker compose up --build` starts only the HTTP server with a named data volume. The port is bound to loopback. Public webhook hosting needs your own HTTPS reverse proxy and request-size limits.

## Delivery

The inbox and routed outbox rows commit in one SQLite transaction. A repeated Telegram update is ignored by its update ID. Workers claim a row under a write transaction, then release the database lock before performing the HTTP request. Leases permit recovery after a worker exits.

To send one queued message, explicitly set `TELEGRAM_BOT_TOKEN` and run:

```sh
python -m inboxbridge.delivery --db inbox.sqlite3 once
```

Run that command repeatedly from your preferred supervisor. Delivery is at least once: a crash after a remote send but before local acknowledgement can cause a duplicate. Telegram has no idempotency key for `sendMessage`. Long messages fail rather than being silently truncated. Failed sends back off and become dead after five attempts. No messages are sent by the import, test or server commands.

## Checks and limits

Tests use temporary SQLite databases and a loopback HTTP receiver. No Telegram credentials are required. `make coverage` reports executable line coverage; it is not a claim that a live Telegram account has been tested.

JSON lines exports contain message text and should be treated as private. Search uses SQLite LIKE with escaped wildcards, so matching is substring based and case folding depends on SQLite. This is intended for a personal inbox, not a large search cluster. There is no attachment storage, Instagram adapter, full-text ranking or user management.
