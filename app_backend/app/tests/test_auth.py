import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from app.main import app # Your FastAPI app
from app.core.config import settings # To potentially override settings for tests
from app.schemas.auth_schemas import UserResponse

# This is a complex part because it involves mocking external Supabase calls.
# We'll mock the supabase_client directly for these tests.

@pytest.mark.asyncio
@patch("app.services.supabase_client.supabase_client")
async def test_register_user_success(mock_supabase_client):
    # Mock Supabase sign_up response
    mock_user_data = MagicMock()
    mock_user_data.id = "a_fake_user_id"  # Note: Supabase User object has id directly
    mock_user_data.email = "test@example.com"

    mock_session_response = MagicMock() # sign_up returns a Session object
    mock_session_response.user = mock_user_data
    mock_session_response.error = None
    mock_supabase_client.auth.sign_up.return_value = mock_session_response

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={"email": "test@example.com", "password": "password123"})

    assert response.status_code == 201
    # The UserResponse model expects 'id' and 'email'.
    # The router should extract these from session_response.user.id and session_response.user.email.
    assert response.json()["id"] == "a_fake_user_id"
    assert response.json()["email"] == "test@example.com"

@pytest.mark.asyncio
@patch("app.services.supabase_client.supabase_client")
async def test_register_user_failure(mock_supabase_client):
    # Mock Supabase sign_up error
    mock_error = MagicMock()
    mock_error.message = "User already registered"

    mock_session_response = MagicMock()
    mock_session_response.user = None
    mock_session_response.error = mock_error # Error is part of the session object
    mock_supabase_client.auth.sign_up.return_value = mock_session_response

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={"email": "test@example.com", "password": "password123"})

    assert response.status_code == 400
    assert "User already registered" in response.json()["detail"]


@pytest.mark.asyncio
@patch("app.services.supabase_client.supabase_client")
async def test_login_for_access_token_success(mock_supabase_client):
    mock_session_data = MagicMock()
    mock_session_data.access_token = "fake_access_token"

    # sign_in_with_password returns an AuthResponse object which has a session attribute
    mock_auth_response = MagicMock()
    mock_auth_response.session = mock_session_data
    mock_auth_response.error = None # No error
    mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    assert response.status_code == 200
    assert response.json()["access_token"] == "fake_access_token"
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
@patch("app.services.supabase_client.supabase_client")
async def test_login_for_access_token_failure(mock_supabase_client):
    mock_error = MagicMock()
    mock_error.message = "Invalid login credentials"

    mock_auth_response = MagicMock()
    mock_auth_response.session = None # No session on error
    mock_auth_response.error = mock_error # Error is part of the auth response object
    mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})

    assert response.status_code == 401
    assert "Invalid login credentials" in response.json()["detail"]

@pytest.mark.asyncio
@patch("app.api.deps.supabase_client") # Patch where it's used (in deps.py)
async def test_read_users_me(mock_supabase_deps_client): # Renamed mock to avoid confusion
    # Mock the behavior of supabase_client.auth.get_user(token)
    mock_user_instance = MagicMock()
    mock_user_instance.id = "test_user_id"
    mock_user_instance.email = "test@example.com"

    # supabase_client.auth.get_user returns a UserResponse object from supabase-py
    # which has a .user attribute containing the User object.
    mock_user_auth_response = MagicMock()
    mock_user_auth_response.user = mock_user_instance

    mock_supabase_deps_client.auth.get_user.return_value = mock_user_auth_response

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/auth/me", headers={"Authorization": "Bearer fake-token"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test_user_id"
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
@patch("app.api.deps.supabase_client") # Patch where it's used
async def test_read_users_me_unauthorized(mock_supabase_deps_client):
    # Mock Supabase client to raise an exception or return no user
    mock_supabase_deps_client.auth.get_user.side_effect = Exception("Invalid token or user not found")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]
