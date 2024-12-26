from inboxbridge.telegram import DeliveryError


def deliver_one(outbox, transport, now=None):
    item = outbox.claim(now=now)
    if item is None:
        return False
    try:
        transport.send(item["destination"], item["payload"])
    except DeliveryError as error:
        outbox.finish(item, error=error, now=now)
    else:
        outbox.finish(item, now=now)
    return True
