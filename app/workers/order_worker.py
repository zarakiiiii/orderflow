from redis.exceptions import ResponseError

from app.core.queue import ORDER_EVENTS_STREAM
from app.core.redis import redis_client

import logging
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


CONSUMER_GROUP = "order_workers"
CONSUMER_NAME = "worker-1"


def create_consumer_group():
    try:
        redis_client.xgroup_create(
            name=ORDER_EVENTS_STREAM,
            groupname=CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )

        logger.info("Created consumer group: %s", CONSUMER_GROUP)

    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def process_event(message_id, data):
    event_type = data.get("event")

    if event_type == "order.created":
        logger.info(
    "Processing order.created | order_id=%s | user_id=%s",
    data.get("order_id"),
    data.get("user_id"),
)
    else:
        logger.warning("Unknown event: %s", event_type)


def main():
    create_consumer_group()

    logger.info("Order worker started")

    while True:
        messages = redis_client.xreadgroup(
            groupname=CONSUMER_GROUP,
            consumername=CONSUMER_NAME,
            streams={
                ORDER_EVENTS_STREAM: ">"
            },
            count=1,
            block=5000,
        )

        if not messages:
            continue

        for _, entries in messages:
            for message_id, data in entries:

                try:
                    process_event(message_id, data)

                    redis_client.xack(
                        ORDER_EVENTS_STREAM,
                        CONSUMER_GROUP,
                        message_id,
                    )

                except Exception as exc:
                    logger.exception(
    "Failed to process message %s",
    message_id,
)


if __name__ == "__main__":
    main()