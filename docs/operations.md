# Operating the inbox

The API and delivery worker must use the same database. In Compose the database is `/data/inbox.sqlite3`; native commands default to the current directory. Verify the queue with `delivery list` before starting a worker.

Routing changes affect newly accepted updates only. Re-importing an already stored update does not apply new rules or enqueue another delivery. A rule's destination is a string, including numeric Telegram chat IDs. Rule matching is a case-insensitive substring check, not a regular expression.

Each CLI listing is one page. Continue from the last returned ID with `--after`; an empty page means there are no more rows at that moment. Concurrent inserts may appear on later pages. Export is suitable for a complete ordered text dump.

A single API key grants access to the entire inbox. Rotate both the API key and webhook secret by changing the process environment and restarting the service. The health endpoint does not reveal message contents.
