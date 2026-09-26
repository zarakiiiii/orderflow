
from sqlalchemy import select

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


def test_list_products(client):
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_product_requires_admin(client):
    token = get_token(
        client,
        "product_customer@orderflow.com",
        "testpassword123",
    )

    response = client.post(
        "/api/v1/products",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Test Keyboard",
            "description": "Mechanical keyboard",
            "sku": "TEST-KB-001",
            "price": "4999.00",
        },
    )

    assert response.status_code == 403


def test_admin_can_create_product(client, db):
    token = get_token(
        client,
        "product_admin@orderflow.com",
        "testpassword123",
    )

    user = db.scalar(
        select(__import__("app.models.user", fromlist=["User"]).User).where(
            __import__("app.models.user", fromlist=["User"]).User.email
            == "product_admin@orderflow.com"
        )
    )

    user.role = "admin"
    db.commit()

    response = client.post(
        "/api/v1/products",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Test Keyboard",
            "description": "Mechanical keyboard",
            "sku": "TEST-KB-001",
            "price": "4999.00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Keyboard"
    assert data["sku"] == "TEST-KB-001"


def test_duplicate_sku_rejected(client, db):
    token = get_token(
        client,
        "product_admin_2@orderflow.com",
        "testpassword123",
    )

    from app.models.user import User

    user = db.scalar(
        select(User).where(
            User.email == "product_admin_2@orderflow.com"
        )
    )

    user.role = "admin"
    db.commit()

    product = Product(
        name="Existing Product",
        description="Existing",
        sku="DUPLICATE-SKU",
        price=100,
        is_active=True,
    )

    db.add(product)
    db.commit()

    response = client.post(
        "/api/v1/products",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Another Product",
            "description": "Another",
            "sku": "DUPLICATE-SKU",
            "price": "200.00",
        },
    )

    assert response.status_code == 409


def test_get_product(client, db):
    product = Product(
        name="Test Mouse",
        description="Wireless mouse",
        sku="TEST-MOUSE-001",
        price=999,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    response = client.get(
        f"/api/v1/products/{product.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product.id
    assert data["name"] == "Test Mouse"
    assert data["sku"] == "TEST-MOUSE-001"

