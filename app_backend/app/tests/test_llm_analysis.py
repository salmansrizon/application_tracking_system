import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
import json

from app.main import app
from app.schemas.auth_schemas import UserResponse
from app.services.llm_service import LLMAnalysisResult

MOCK_USER_ID_STR = str(uuid4())

@pytest.fixture(autouse=True)
def current_user_mock_fixture(): # Renamed fixture
    with patch("app.api.routers.resumes.get_current_user") as mock: # Patched in resumes router
        mock.return_value = UserResponse(id=MOCK_USER_ID_STR, email="test@example.com")
        yield mock

@pytest.fixture
def supabase_mock_fixture(): # Renamed fixture
    with patch("app.api.routers.resumes.supabase_client") as mock: # Patched in resumes router
        yield mock

@pytest.fixture
def openai_llm_mock_fixture(): # Renamed fixture
    # Patching where AsyncOpenAI is instantiated in llm_service.py
    with patch("app.services.llm_service.openai.AsyncOpenAI") as mock_constructor:
        mock_client = AsyncMock() # The client instance
        mock_constructor.return_value = mock_client # Constructor returns our mock client

        # Mock the chain of calls on the client instance
        mock_chat_completions = AsyncMock() # Mock for the 'chat.completions' attribute
        mock_client.chat.completions = mock_chat_completions

        mock_create_method = AsyncMock() # Mock for the 'create' method
        mock_chat_completions.create = mock_create_method # Assign to the 'create' attribute

        yield mock_create_method # This is what the test will use to set return_value for .create()

@pytest.mark.asyncio
async def test_llm_service_direct_call(openai_llm_mock_fixture): # Use renamed fixture
    from app.services.llm_service import analyze_resume_with_llm # Direct import for service test

    mock_response_data = {
        "match_score": 80,
        "missing_keywords": ["python", "fastapi"],
        "strength_summary": "Good experience in related fields.",
        "improvement_suggestions": ["Highlight teamwork skills."],
        "ats_compatibility_check": "Generally compatible, minor formatting tweaks recommended."
    }
    # Mocking the structure of the OpenAI completion object
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(mock_response_data)

    mock_completion_object = MagicMock()
    mock_completion_object.choices = [mock_choice]

    openai_llm_mock_fixture.return_value = mock_completion_object # .create() returns this

    result = await analyze_resume_with_llm("sample resume text", "sample job description")

    assert result is not None
    assert result.match_score == 80
    assert result.missing_keywords == ["python", "fastapi"]

@pytest.mark.asyncio
async def test_endpoint_with_text(openai_llm_mock_fixture): # Use renamed fixture
    mock_response_data = {"match_score": 70, "missing_keywords": [], "strength_summary": "S", "improvement_suggestions": [], "ats_compatibility_check": "A"}
    mock_choice = MagicMock(); mock_choice.message.content = json.dumps(mock_response_data)
    mock_completion_object = MagicMock(); mock_completion_object.choices = [mock_choice]
    openai_llm_mock_fixture.return_value = mock_completion_object

    payload = {"resume_text": "text", "job_description_text": "jd"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/resumes/analyze", json=payload)
    assert response.status_code == 200
    assert response.json()["match_score"] == 70

@pytest.mark.asyncio
async def test_endpoint_with_id(supabase_mock_fixture, openai_llm_mock_fixture): # Use renamed fixtures
    resume_id = str(uuid4())
    # Mock for Supabase client response
    mock_db_response = MagicMock()
    mock_db_response.data = {"raw_text": "database resume text"} # Supabase response structure
    supabase_mock_fixture.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=mock_db_response)

    mock_llm_response_data = {"match_score": 60, "missing_keywords": ["specific_skill"], "strength_summary": "Analysis based on DB text", "improvement_suggestions": [], "ats_compatibility_check": "OK"}
    mock_llm_choice = MagicMock(); mock_llm_choice.message.content = json.dumps(mock_llm_response_data)
    mock_llm_completion_object = MagicMock(); mock_llm_completion_object.choices = [mock_llm_choice]
    openai_llm_mock_fixture.return_value = mock_llm_completion_object

    payload = {"resume_id": resume_id, "job_description_text": "jd"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/resumes/analyze", json=payload)
    assert response.status_code == 200
    assert response.json()["match_score"] == 60
    assert response.json()["missing_keywords"] == ["specific_skill"]

@pytest.mark.asyncio
async def test_endpoint_no_source():
    payload = {"job_description_text": "jd"} # Missing resume_id and resume_text
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/resumes/analyze", json=payload)
    assert response.status_code == 422 # Pydantic validation error (Unprocessable Entity)
    assert "Either resume_id or resume_text must be provided" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_endpoint_resume_id_not_found(supabase_mock_fixture):
    resume_id = str(uuid4())
    # Mock Supabase client to return no data for the given resume_id
    mock_db_response_not_found = MagicMock()
    mock_db_response_not_found.data = None # Simulate resume not found
    supabase_mock_fixture.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=mock_db_response_not_found)

    payload = {"resume_id": resume_id, "job_description_text": "some job description"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/resumes/analyze", json=payload)

    assert response.status_code == 404
    assert f"Resume with id {resume_id} not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_llm_service_failure(openai_llm_mock_fixture):
    openai_llm_mock_fixture.side_effect = Exception("LLM API Error") # Simulate LLM call failing

    payload = {"resume_text": "some resume", "job_description_text": "some jd"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/resumes/analyze", json=payload)

    assert response.status_code == 500
    assert "LLM analysis failed" in response.json()["detail"]
