from app.core.redis import redis_client


ORDER_EVENTS_STREAM = "order_events"


def publish_order_created(
    order_id: int,
    user_id: int,
):
    redis_client.xadd(
        ORDER_EVENTS_STREAM,
        {
            "event": "order.created",
            "order_id": str(order_id),
            "user_id": str(user_id),
        },
    )