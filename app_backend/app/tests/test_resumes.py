import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from uuid import uuid4, UUID
import datetime
import io

from app.main import app # Your FastAPI app
from app.schemas.auth_schemas import UserResponse

MOCK_USER_ID_STR = str(uuid4())
MOCK_USER_EMAIL = "resumetest@example.com"

@pytest.fixture(autouse=True)
def mock_get_current_user_fixture():
    with patch("app.api.routers.resumes.get_current_user") as mock_get_user: # Target where get_current_user is used
        mock_user = UserResponse(id=MOCK_USER_ID_STR, email=MOCK_USER_EMAIL)
        mock_get_user.return_value = mock_user
        yield mock_get_user

@pytest.fixture
def mock_supabase_client():
    with patch("app.api.routers.resumes.supabase_client") as mock_client:
        yield mock_client

# Helper to create mock Supabase PostgrestAPIResponse
def create_mock_supabase_api_response(data=None, error=None, count=None):
    mock_res = MagicMock()
    mock_res.data = data
    mock_res.error = error
    mock_res.count = count
    return mock_res

# Sample resume data as Supabase would return
def sample_resume_db_dict(resume_id=None, user_id=None, **kwargs):
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "id": str(resume_id or uuid4()),
        "user_id": str(user_id or MOCK_USER_ID_STR),
        "filename": "test_resume.pdf",
        "content_hash": "fake_hash_value",
        "raw_text": "This is some resume text.",
        "storage_path": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        **kwargs
    }

@pytest.mark.asyncio
async def test_upload_resume_pdf_success(mock_supabase_client):
    mock_pdf_content = b"%PDF-1.4 fake PDF content"
    mock_resume_id = uuid4()

    # Mock file parser service functions
    with patch("app.api.routers.resumes.parse_pdf", return_value="Parsed PDF text") as mock_parse_pdf, \
         patch("app.api.routers.resumes.calculate_sha256_hash", return_value="testhash123") as mock_hash:

        # Mock Supabase responses
        # 1. For checking existing hash (return no existing data)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
            return_value=create_mock_supabase_api_response(data=None)
        )
        # 2. For insert new resume
        inserted_resume_data = sample_resume_db_dict(id=mock_resume_id, raw_text="Parsed PDF text", content_hash="testhash123", filename="test.pdf")
        mock_supabase_client.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=create_mock_supabase_api_response(data=[inserted_resume_data])
        )

        files = {"file": ("test.pdf", io.BytesIO(mock_pdf_content), "application/pdf")}
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/resumes/upload", files=files, headers={"Authorization": "Bearer faketoken"})

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["raw_text"] == "Parsed PDF text"
        assert data["content_hash"] == "testhash123"
        assert data["user_id"] == MOCK_USER_ID_STR
        mock_parse_pdf.assert_called_once_with(mock_pdf_content)
        mock_hash.assert_called_once_with(mock_pdf_content)
        mock_supabase_client.table.return_value.insert.assert_called_once()


@pytest.mark.asyncio
async def test_upload_resume_duplicate_hash_for_user(mock_supabase_client):
    mock_pdf_content = b"duplicate content"
    existing_resume_data = sample_resume_db_dict(content_hash="duplicatehash", raw_text="Existing text")

    with patch("app.api.routers.resumes.parse_pdf", return_value="Parsed text"), \
         patch("app.api.routers.resumes.calculate_sha256_hash", return_value="duplicatehash"):

        # Mock Supabase to return existing resume on hash check
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
            return_value=create_mock_supabase_api_response(data=existing_resume_data)
        )

        files = {"file": ("resume.pdf", io.BytesIO(mock_pdf_content), "application/pdf")}
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/resumes/upload", files=files, headers={"Authorization": "Bearer faketoken"})

        assert response.status_code == 201 # Returns existing record
        data = response.json()
        assert data["id"] == existing_resume_data["id"]
        assert data["content_hash"] == "duplicatehash"
        # Ensure insert was NOT called
        mock_supabase_client.table.return_value.insert.return_value.execute.assert_not_called()


@pytest.mark.asyncio
async def test_upload_resume_file_too_large():
    # Content larger than MAX_FILE_SIZE (default 5MB in router)
    # Create a dummy file content that is too large
    large_content = b"a" * (6 * 1024 * 1024)
    files = {"file": ("large_resume.pdf", io.BytesIO(large_content), "application/pdf")}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/resumes/upload", files=files, headers={"Authorization": "Bearer faketoken"})
    assert response.status_code == 413 # Request Entity Too Large


@pytest.mark.asyncio
async def test_upload_resume_unsupported_file_type():
    files = {"file": ("image.png", io.BytesIO(b"fakeimage"), "image/png")}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/resumes/upload", files=files, headers={"Authorization": "Bearer faketoken"})
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_resumes(mock_supabase_client):
    mock_resume_list_meta = [
        {k: v for k, v in sample_resume_db_dict(filename="resume1.pdf").items() if k != "raw_text"}, # Simulate metadata
        {k: v for k, v in sample_resume_db_dict(filename="resume2.docx").items() if k != "raw_text"}
    ]
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute = AsyncMock(
        return_value=create_mock_supabase_api_response(data=mock_resume_list_meta)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/resumes/", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["filename"] == "resume1.pdf"
    assert "raw_text" not in data[0] # Ensure metadata schema is used

    mock_supabase_client.table.return_value.select.assert_called_once_with("id, filename, content_hash, storage_path, created_at, updated_at")


@pytest.mark.asyncio
async def test_get_resume_details_found(mock_supabase_client):
    resume_id_to_fetch = uuid4()
    mock_resume_data = sample_resume_db_dict(id=resume_id_to_fetch, raw_text="Detailed resume text.")

    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=create_mock_supabase_api_response(data=mock_resume_data)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/resumes/{resume_id_to_fetch}", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(resume_id_to_fetch)
    assert data["raw_text"] == "Detailed resume text."
    mock_supabase_client.table.return_value.select.assert_called_once_with("*")


@pytest.mark.asyncio
async def test_get_resume_details_not_found(mock_supabase_client):
    resume_id_to_fetch = uuid4()
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=create_mock_supabase_api_response(data=None) # Simulate not found
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/resumes/{resume_id_to_fetch}", headers={"Authorization": "Bearer faketoken"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_resume_success(mock_supabase_client):
    resume_id_to_delete = uuid4()
    # Mock the delete call
    # Supabase delete often returns the deleted items, or an empty list if RLS prevented/nothing matched.
    # For a 204, the content doesn't matter as much as the status.
    mock_supabase_client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute = AsyncMock(
        return_value=create_mock_supabase_api_response(data=[sample_resume_db_dict(id=resume_id_to_delete)]) # Simulate one item deleted
    )

    # Optional: Mock storage deletion if that part is implemented and tested
    # with patch("app.api.routers.resumes.supabase_client.storage.from_") as mock_storage_from:
    #    mock_storage_from.return_value.remove = AsyncMock()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(f"/resumes/{resume_id_to_delete}", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == 204
    mock_supabase_client.table.return_value.delete.return_value.eq.return_value.eq.assert_called_once()


@pytest.mark.asyncio
async def test_delete_resume_not_found_or_rls_prevents(mock_supabase_client):
    resume_id_to_delete = uuid4()
    # Simulate Supabase delete affecting 0 rows (e.g. RLS prevents or ID doesn't exist for user)
    mock_supabase_client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute = AsyncMock(
        return_value=create_mock_supabase_api_response(data=[]) # No data returned means nothing deleted that matched criteria
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(f"/resumes/{resume_id_to_delete}", headers={"Authorization": "Bearer faketoken"})
    # The endpoint currently doesn't raise 404 on delete if RLS prevents or item not found, it just returns 204.
    # This is often acceptable for DELETE operations. If a 404 is desired, the router logic would need a pre-check.
    assert response.status_code == 204
