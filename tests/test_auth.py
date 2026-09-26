
def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "pytest_user_001@orderflow.com",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "pytest_user_001@orderflow.com"
    assert data["role"] == "customer"
    assert data["is_active"] is True


def test_login_user(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "pytest_user_002@orderflow.com",
            "password": "testpassword123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "pytest_user_002@orderflow.com",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_login(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "pytest_user_003@orderflow.com",
            "password": "testpassword123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "pytest_user_003@orderflow.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401

