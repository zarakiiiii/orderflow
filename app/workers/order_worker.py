from redis.exceptions import ResponseError

from app.core.queue import ORDER_EVENTS_STREAM
from app.core.redis import redis_client


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

        print(f"Created consumer group: {CONSUMER_GROUP}")

    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def process_event(message_id, data):
    event_type = data.get("event")

    if event_type == "order.created":
        print(
            f"Processing order.created | "
            f"order_id={data.get('order_id')} | "
            f"user_id={data.get('user_id')}"
        )
    else:
        print(f"Unknown event: {event_type}")


def main():
    create_consumer_group()

    print("Order worker started...")

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
                    print(
                        f"Failed to process "
                        f"{message_id}: {exc}"
                    )


if __name__ == "__main__":
    main()