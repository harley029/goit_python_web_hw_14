from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from src.entity.models import User
from tests.conftest import TestingSessionLocal

from src.services.auth import auth_serviсe
from src.repository import users as repositories_users
from sqlalchemy.ext.asyncio import AsyncEngine

# from src.conf import messages

user_data = {
    "username": "testuser",
    "email": "testuser@mail.com",
    "password": "qwerty",
}


def test_signup(client):
    with patch("fastapi.Request.client", create=True) as mock_client:
        mock_client.host = "127.0.0.1"
        response = client.post("/api/auth/signup", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "password" not in data
        assert "avatar" in data


@pytest.mark.asyncio
async def test_successful_login(client: TestClient):
    with patch("fastapi.Request.client", create=True) as mock_client:
        mock_client.host = "127.0.0.1"
        mock_user = User(
            email="testuser@mail.com",
            username="testuser",
            password=auth_serviсe.get_password_hash("qwerty"),
            confirmed=True,
        )
        repositories_users.get_user_by_email = AsyncMock(return_value=mock_user)
        repositories_users.update_token = AsyncMock()
        # Mocking authentication service functions
        auth_serviсe.verify_password = AsyncMock(return_value=True)
        auth_serviсe.create_access_token = AsyncMock(return_value="access_token")
        auth_serviсe.create_refresh_token = AsyncMock(return_value="refresh_token")
        # Make the request
        response = client.post("/api/auth/login", data={"username": "testuser@mail.com", "password": "qwerty"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

