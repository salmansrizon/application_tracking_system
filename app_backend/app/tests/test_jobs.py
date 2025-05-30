import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4, UUID
import datetime

from app.main import app # Your FastAPI app
from app.schemas.auth_schemas import UserResponse
from app.schemas.job_schemas import JobApplicationRead # For constructing mock return data

# Mock current_user for all tests in this file
MOCK_USER_ID_STR = str(uuid4())
MOCK_USER_EMAIL = "dbtestuser@example.com"

@pytest.fixture(autouse=True)
def mock_get_current_user_fixture():
    with patch("app.api.routers.jobs.get_current_user") as mock_get_user:
        mock_user = UserResponse(id=MOCK_USER_ID_STR, email=MOCK_USER_EMAIL)
        # get_current_user is an async function, so its mock should also be async if it's directly awaited
        # However, Depends() handles it. If we were calling it directly, it'd need AsyncMock.
        # Here, return_value is fine as Depends unwraps it.
        mock_get_user.return_value = mock_user
        yield mock_get_user

# Fixture to mock the supabase_client
@pytest.fixture
def mock_supabase_client_fixture():
    # Patch where supabase_client is imported and used by the jobs router
    with patch("app.api.routers.jobs.supabase_client") as mock_client:
        yield mock_client


# Helper to create mock Supabase PostgrestAPIResponse
def create_mock_response(data, error=None, count=None):
    mock_res = MagicMock() # Use regular MagicMock for the response object itself
    mock_res.data = data
    mock_res.error = error
    mock_res.count = count
    return mock_res

# Helper to create a sample job dict as Supabase would return
def sample_job_dict(job_id=None, user_id=None, company="Test Corp", position="Tester", status="applied", deadline=None, notes=None, **kwargs):
    now = datetime.datetime.now(datetime.timezone.utc)
    # Ensure deadline is a string if not None, as DB would store it
    deadline_str = deadline.isoformat() if isinstance(deadline, datetime.date) else None
    return {
        "id": str(job_id or uuid4()),
        "user_id": str(user_id or MOCK_USER_ID_STR),
        "company": company,
        "position": position,
        "status": status,
        "deadline": deadline_str,
        "notes": notes,
        "created_at": now.isoformat(), # Supabase returns ISO strings
        "updated_at": now.isoformat(), # Supabase returns ISO strings
        **kwargs
    }


@pytest.mark.asyncio
async def test_create_job_application(mock_supabase_client_fixture):
    job_data_in = {"company": "Test Corp", "position": "Tester", "status": "applied", "deadline": datetime.date.today().isoformat()}

    mock_created_job_dict = sample_job_dict(
        company=job_data_in["company"],
        position=job_data_in["position"],
        status=job_data_in["status"],
        deadline=datetime.date.today() # Pass as date object, sample_job_dict handles conversion
    )

    # Use AsyncMock for the execute method since it's awaited
    mock_supabase_client_fixture.table.return_value.insert.return_value.execute = AsyncMock(
        return_value=create_mock_response(data=[mock_created_job_dict])
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/jobs/", json=job_data_in, headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == 201
    data = response.json()
    assert data["company"] == "Test Corp"
    assert data["position"] == "Tester"
    assert data["user_id"] == MOCK_USER_ID_STR
    assert data["id"] == mock_created_job_dict["id"]
    assert data["deadline"] == datetime.date.today().isoformat()

    expected_insert_data = job_data_in.copy()
    expected_insert_data['user_id'] = MOCK_USER_ID_STR
    mock_supabase_client_fixture.table.return_value.insert.assert_called_once_with(expected_insert_data)


@pytest.mark.asyncio
async def test_read_job_applications(mock_supabase_client_fixture):
    mock_job_list = [
        sample_job_dict(company="Job 1", deadline=datetime.date(2023,1,1)),
        sample_job_dict(company="Job 2", deadline=datetime.date(2023,1,2))
    ]
    mock_supabase_client_fixture.table.return_value.select.return_value.eq.return_value.range.return_value.execute = AsyncMock(
        return_value=create_mock_response(data=mock_job_list)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/jobs/", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["company"] == "Job 1"
    assert data[1]["company"] == "Job 2"
    assert data[0]["user_id"] == MOCK_USER_ID_STR

    mock_supabase_client_fixture.table.assert_called_with("job_applications")
    mock_supabase_client_fixture.table.return_value.select.assert_called_with("*")
    mock_supabase_client_fixture.table.return_value.select.return_value.eq.assert_called_with("user_id", MOCK_USER_ID_STR)
    mock_supabase_client_fixture.table.return_value.select.return_value.eq.return_value.range.assert_called_with(0, 99)


@pytest.mark.asyncio
async def test_read_single_job_application_found(mock_supabase_client_fixture):
    job_id_to_fetch = uuid4()
    mock_job_dict = sample_job_dict(id=job_id_to_fetch, company="Specific Job")

    mock_supabase_client_fixture.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=create_mock_response(data=mock_job_dict)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/jobs/{job_id_to_fetch}", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "Specific Job"
    assert data["id"] == str(job_id_to_fetch)

    mock_supabase_client_fixture.table.assert_called_with("job_applications")
    mock_supabase_client_fixture.table.return_value.select.assert_called_with("*")

    # Check the .eq calls were made correctly. Order might vary.
    eq_calls = mock_supabase_client_fixture.table.return_value.select.return_value.eq.call_args_list
    assert any(call[0] == ("id", str(job_id_to_fetch)) for call in eq_calls)
    assert any(call[0] == ("user_id", MOCK_USER_ID_STR) for call in eq_calls)


@pytest.mark.asyncio
async def test_read_single_job_application_not_found(mock_supabase_client_fixture):
    job_id_to_fetch = uuid4()
    mock_supabase_client_fixture.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=create_mock_response(data=None)
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/jobs/{job_id_to_fetch}", headers={"Authorization": "Bearer faketoken"})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_job_application(mock_supabase_client_fixture):
    job_id_to_update = uuid4()
    update_payload = {"company": "Updated Corp", "status": "interview", "deadline": datetime.date(2024,1,1).isoformat()}

    original_job_dict = sample_job_dict(id=job_id_to_update, company="Original Corp", status="applied")
    updated_db_response_job_dict = sample_job_dict(
        id=job_id_to_update,
        company=update_payload["company"],
        status=update_payload["status"],
        deadline=datetime.date(2024,1,1)
    )

    # Mock for the check_response (the initial select)
    mock_check_execute = AsyncMock(return_value=create_mock_response(data=original_job_dict))
    mock_supabase_client_fixture.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = mock_check_execute

    # Mock for the actual update response
    mock_update_execute = AsyncMock(return_value=create_mock_response(data=[updated_db_response_job_dict]))
    mock_supabase_client_fixture.table.return_value.update.return_value.eq.return_value.eq.return_value.execute = mock_update_execute

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(f"/jobs/{job_id_to_update}", json=update_payload, headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "Updated Corp"
    assert data["status"] == "interview"
    assert data["id"] == str(job_id_to_update)
    assert data["deadline"] == "2024-01-01"

    mock_supabase_client_fixture.table.return_value.update.assert_called_once_with(update_payload)


@pytest.mark.asyncio
async def test_update_job_application_not_found(mock_supabase_client_fixture):
    job_id_to_update = uuid4()
    update_payload = {"company": "Ghost Corp"}

    mock_supabase_client_fixture.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=create_mock_response(data=None)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(f"/jobs/{job_id_to_update}", json=update_payload, headers={"Authorization": "Bearer faketoken"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_application(mock_supabase_client_fixture):
    job_id_to_delete = uuid4()
    deleted_job_item = sample_job_dict(id=job_id_to_delete)

    # Mock for the check_response (select)
    mock_check_execute = AsyncMock(return_value=create_mock_response(data=deleted_job_item))
    mock_supabase_client_fixture.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = mock_check_execute

    # Mock for the delete response
    mock_delete_execute = AsyncMock(return_value=create_mock_response(data=[deleted_job_item])) # Supabase delete returns deleted items
    mock_supabase_client_fixture.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute = mock_delete_execute

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(f"/jobs/{job_id_to_delete}", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == 204
    mock_supabase_client_fixture.table.return_value.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_job_application_not_found(mock_supabase_client_fixture):
    job_id_to_delete = uuid4()
    mock_supabase_client_fixture.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=create_mock_response(data=None)
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(f"/jobs/{job_id_to_delete}", headers={"Authorization": "Bearer faketoken"})
    assert response.status_code == 404
