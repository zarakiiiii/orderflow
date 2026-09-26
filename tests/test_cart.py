
from sqlalchemy import select

from app.models.product import Product
import uuid


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


def create_product(db):
    product = Product(
        name="Cart Test Product",
        description="Product for cart tests",
        sku=f"CART-TEST-{uuid.uuid4().hex[:8]}",
        price=999,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def test_add_to_cart(client, db):
    token = get_token(
        client,
        "cart_user_001@orderflow.com",
        "testpassword123",
    )

    product = create_product(db)

    response = client.post(
        "/api/v1/cart/items",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "product_id": product.id,
            "quantity": 2,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == product.id
    assert data["quantity"] == 2


def test_add_same_product_increases_quantity(client, db):
    token = get_token(
        client,
        "cart_user_002@orderflow.com",
        "testpassword123",
    )

    product = Product(
        name="Cart Quantity Product",
        description="Quantity test",
        sku="CART-TEST-002",
        price=500,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={
            "product_id": product.id,
            "quantity": 2,
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={
            "product_id": product.id,
            "quantity": 3,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == product.id
    assert data["quantity"] == 5


def test_get_cart(client, db):
    token = get_token(
        client,
        "cart_user_003@orderflow.com",
        "testpassword123",
    )

    product = create_product(db)

    response = client.post(
        "/api/v1/cart/items",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "product_id": product.id,
            "quantity": 3,
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/cart",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == product.id
    assert data["items"][0]["quantity"] == 3


def test_update_cart_item(client, db):
    token = get_token(
        client,
        "cart_user_004@orderflow.com",
        "testpassword123",
    )

    product = create_product(db)

    headers = {
        "Authorization": f"Bearer {token}",
    }

    client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={
            "product_id": product.id,
            "quantity": 2,
        },
    )

    response = client.patch(
        f"/api/v1/cart/items/{product.id}",
        headers=headers,
        json={
            "quantity": 7,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product.id
    assert data["quantity"] == 7


def test_remove_cart_item(client, db):
    token = get_token(
        client,
        "cart_user_005@orderflow.com",
        "testpassword123",
    )

    product = create_product(db)

    headers = {
        "Authorization": f"Bearer {token}",
    }

    client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={
            "product_id": product.id,
            "quantity": 2,
        },
    )

    response = client.delete(
        f"/api/v1/cart/items/{product.id}",
        headers=headers,
    )

    assert response.status_code == 204

    response = client.get(
        "/api/v1/cart",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_add_invalid_product(client):
    token = get_token(
        client,
        "cart_user_006@orderflow.com",
        "testpassword123",
    )

    response = client.post(
        "/api/v1/cart/items",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "product_id": 999999,
            "quantity": 1,
        },
    )

    assert response.status_code == 404

