
from sqlalchemy import select

from app.models.cart import Cart, CartItem
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.product import Product


def get_token(client, email, password):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    return response.json()["access_token"]


def create_product_with_inventory(
    db,
    sku,
    price=1000,
    quantity=10,
):
    product = Product(
        name="Order Test Product",
        description="Product for order tests",
        sku=sku,
        price=price,
        is_active=True,
    )

    db.add(product)
    db.flush()

    inventory = Inventory(
        product_id=product.id,
        quantity=quantity,
    )

    db.add(inventory)
    db.commit()
    db.refresh(product)
    db.refresh(inventory)

    return product, inventory


def add_product_to_cart(
    client,
    token,
    product_id,
    quantity,
):
    return client.post(
        "/api/v1/cart/items",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "product_id": product_id,
            "quantity": quantity,
        },
    )


def test_successful_checkout(client, db):
    token = get_token(
        client,
        "order_user_001@orderflow.com",
        "testpassword123",
    )

    product, inventory = create_product_with_inventory(
        db,
        "ORDER-TEST-001",
        price=1000,
        quantity=10,
    )

    response = add_product_to_cart(
        client,
        token,
        product.id,
        2,
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/orders/checkout",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "order-test-001",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "confirmed"
    assert data["total_amount"] == "2000.00"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == product.id
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price"] == "1000.00"


def test_checkout_deducts_inventory(client, db):
    token = get_token(
        client,
        "order_user_002@orderflow.com",
        "testpassword123",
    )

    product, inventory = create_product_with_inventory(
        db,
        "ORDER-TEST-002",
        price=500,
        quantity=10,
    )

    add_product_to_cart(
        client,
        token,
        product.id,
        3,
    )

    response = client.post(
        "/api/v1/orders/checkout",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "order-test-002",
        },
    )

    assert response.status_code == 201

    db.refresh(inventory)

    assert inventory.quantity == 7


def test_checkout_clears_cart(client, db):
    token = get_token(
        client,
        "order_user_003@orderflow.com",
        "testpassword123",
    )

    product, _ = create_product_with_inventory(
        db,
        "ORDER-TEST-003",
        quantity=10,
    )

    add_product_to_cart(
        client,
        token,
        product.id,
        2,
    )

    response = client.post(
        "/api/v1/orders/checkout",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "order-test-003",
        },
    )

    assert response.status_code == 201

    cart_response = client.get(
        "/api/v1/cart",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []


def test_insufficient_inventory_rejected(client, db):
    token = get_token(
        client,
        "order_user_004@orderflow.com",
        "testpassword123",
    )

    product, inventory = create_product_with_inventory(
        db,
        "ORDER-TEST-004",
        quantity=2,
    )

    add_product_to_cart(
        client,
        token,
        product.id,
        5,
    )

    response = client.post(
        "/api/v1/orders/checkout",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "order-test-004",
        },
    )

    assert response.status_code == 409

    db.refresh(inventory)

    assert inventory.quantity == 2


def test_checkout_requires_idempotency_key(client, db):
    token = get_token(
        client,
        "order_user_005@orderflow.com",
        "testpassword123",
    )

    product, _ = create_product_with_inventory(
        db,
        "ORDER-TEST-005",
        quantity=10,
    )

    add_product_to_cart(
        client,
        token,
        product.id,
        1,
    )

    response = client.post(
        "/api/v1/orders/checkout",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


def test_idempotency_prevents_duplicate_order(client, db):
    token = get_token(
        client,
        "order_user_006@orderflow.com",
        "testpassword123",
    )

    product, inventory = create_product_with_inventory(
        db,
        "ORDER-TEST-006",
        price=750,
        quantity=10,
    )

    add_product_to_cart(
        client,
        token,
        product.id,
        2,
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "order-test-006",
    }

    first_response = client.post(
        "/api/v1/orders/checkout",
        headers=headers,
    )

    assert first_response.status_code == 201

    first_order = first_response.json()

    second_response = client.post(
        "/api/v1/orders/checkout",
        headers=headers,
    )

    assert second_response.status_code == 201

    second_order = second_response.json()

    assert second_order["id"] == first_order["id"]
    assert second_order["total_amount"] == first_order["total_amount"]

    orders = db.scalars(
        select(Order).where(
            Order.user_id
            == db.scalar(
                select(Order.user_id).where(
                    Order.id == first_order["id"]
                )
            )
        )
    ).all()

    assert len(orders) == 1

    db.refresh(inventory)

    assert inventory.quantity == 8




