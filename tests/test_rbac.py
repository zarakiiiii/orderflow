
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


def test_admin_endpoint_requires_authentication(client):
    response = client.get("/api/v1/admin/test")

    assert response.status_code == 401


def test_customer_cannot_access_admin_endpoint(client):
    token = get_token(
        client,
        "pytest_customer@orderflow.com",
        "testpassword123",
    )

    response = client.get(
        "/api/v1/admin/test",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_admin_can_access_admin_endpoint(client, db):
    token = get_token(
        client,
        "pytest_admin@orderflow.com",
        "testpassword123",
    )

    # Promote the test user to admin.
    from sqlalchemy import select
    from app.models.user import User

    user = db.scalar(
        select(User).where(
            User.email == "pytest_admin@orderflow.com"
        )
    )

    user.role = "admin"
    db.commit()

    response = client.get(
        "/api/v1/admin/test",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Welcome, admin"
    assert data["email"] == "pytest_admin@orderflow.com"

