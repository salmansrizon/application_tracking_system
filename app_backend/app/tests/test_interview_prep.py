import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
import json

from app.main import app # Your FastAPI app
from app.schemas.auth_schemas import UserResponse # For mocking current_user
from app.services.llm_service import InterviewPrepResult, InterviewQuestion # For test data

MOCK_USER_ID_STR = str(uuid4())

@pytest.fixture(autouse=True)
def mock_get_current_user_for_interview_router():
    # Patch where get_current_user is used by the interview_prep router
    with patch("app.api.routers.interview_prep.get_current_user") as mock_get_user:
        mock_user = UserResponse(id=MOCK_USER_ID_STR, email="interviewtest@example.com")
        mock_get_user.return_value = mock_user
        yield mock_get_user

@pytest.fixture
def mock_supabase_for_interview_router(): # For when the endpoint fetches resume by ID
    with patch("app.api.routers.interview_prep.supabase_client") as mock_client:
        yield mock_client

@pytest.fixture
def mock_openai_for_interview_llm_service(): # For testing the llm_service function directly
    # Patches openai.AsyncOpenAI where it's used in app.services.llm_service
    with patch("app.services.llm_service.openai.AsyncOpenAI") as mock_constructor:
        mock_client_instance = AsyncMock() # This is the instance of AsyncOpenAI
        mock_constructor.return_value = mock_client_instance # Constructor returns our mock client

        # The method we want to mock is on the instance
        mock_create_method = AsyncMock()
        mock_client_instance.chat.completions.create = mock_create_method
        yield mock_create_method # This is what the tests will use to set return_value/side_effect

# Test for the llm_service.generate_interview_questions_with_llm function
@pytest.mark.asyncio
async def test_llm_service_generate_questions_success(mock_openai_for_interview_llm_service):
    # Import the function locally to ensure the patch is effective for this test
    from app.services.llm_service import generate_interview_questions_with_llm

    mock_llm_response_data = {
        "generated_questions": [
            {"category": "Behavioral", "question": "Tell me about a time...?"},
            {"category": "Technical", "question": "Explain concept X."}
        ],
        "preparation_tips": ["Research the company.", "Prepare your own questions."]
    }
    # Simulate OpenAI's response structure
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(mock_llm_response_data)
    mock_completion_object = MagicMock()
    mock_completion_object.choices = [mock_choice]

    mock_openai_for_interview_llm_service.return_value = mock_completion_object

    result = await generate_interview_questions_with_llm("some resume text", "some job description text")

    assert result is not None
    assert len(result.generated_questions) == 2
    assert result.generated_questions[0].category == "Behavioral"
    assert result.generated_questions[0].question == "Tell me about a time...?"
    assert len(result.preparation_tips) == 2
    assert result.preparation_tips[0] == "Research the company."
    mock_openai_for_interview_llm_service.assert_called_once()

# Tests for the /interview/generate-questions endpoint
@pytest.mark.asyncio
# Patch the service function directly where it's called by the router
@patch("app.api.routers.interview_prep.generate_interview_questions_with_llm")
async def test_generate_questions_endpoint_with_text(mock_generate_questions_service_call):
    # Prepare the mock response from the service function
    mock_service_response = InterviewPrepResult(
        generated_questions=[InterviewQuestion(category="Technical", question="What is FastAPI?")],
        preparation_tips=["Review Python basics."]
    )
    mock_generate_questions_service_call.return_value = mock_service_response

    request_payload = {
        "resume_text": "My awesome resume.",
        "job_description_text": "Python developer role."
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # get_current_user is auto-mocked by the fixture for this router
        response = await ac.post("/interview/generate-questions", json=request_payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data["generated_questions"]) == 1
    assert data["generated_questions"][0]["question"] == "What is FastAPI?"
    assert data["preparation_tips"][0] == "Review Python basics."
    # Verify the service function was called with the correct arguments
    mock_generate_questions_service_call.assert_called_once_with("My awesome resume.", "Python developer role.")

@pytest.mark.asyncio
@patch("app.api.routers.interview_prep.generate_interview_questions_with_llm")
async def test_generate_questions_endpoint_with_resume_id(
    mock_generate_questions_service_call, mock_supabase_for_interview_router # Use the Supabase mock for this router
):
    resume_id_for_request = str(uuid4())

    # Mock Supabase client's response for fetching resume text
    mock_db_response_data = {"raw_text": "Resume text fetched from database."}
    # Simulate the structure of Supabase's PostgrestAPIResponse
    mock_supabase_api_response = MagicMock()
    mock_supabase_api_response.data = mock_db_response_data
    mock_supabase_for_interview_router.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=mock_supabase_api_response
    )

    # Mock the response from our LLM service function
    mock_service_response = InterviewPrepResult(
        generated_questions=[InterviewQuestion(category="Situational", question="Describe a challenge you faced.")],
        preparation_tips=["Use the STAR method for your answers."]
    )
    mock_generate_questions_service_call.return_value = mock_service_response

    request_payload = {
        "resume_id": resume_id_for_request,
        "job_description_text": "Challenging role description."
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/interview/generate-questions", json=request_payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data["generated_questions"]) == 1
    assert data["generated_questions"][0]["category"] == "Situational"
    # Verify the service function was called with text fetched from DB
    mock_generate_questions_service_call.assert_called_once_with("Resume text fetched from database.", "Challenging role description.")


@pytest.mark.asyncio
async def test_generate_questions_endpoint_no_resume_source_provided():
    # This request should be caught by Pydantic validation in InterviewQuestionRequest schema
    request_payload = {"job_description_text": "A job description."} # Missing resume_id and resume_text
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/interview/generate-questions", json=request_payload)
    assert response.status_code == 422 # Unprocessable Entity due to Pydantic validation error

@pytest.mark.asyncio
@patch("app.api.routers.interview_prep.generate_interview_questions_with_llm")
async def test_generate_questions_endpoint_llm_service_returns_none(mock_generate_questions_service_call):
    # Simulate a failure in the LLM service (e.g., OpenAI API error, parsing error)
    mock_generate_questions_service_call.return_value = None

    request_payload = {"resume_text": "some resume", "job_description_text": "some jd"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/interview/generate-questions", json=request_payload)

    assert response.status_code == 500
    assert "Failed to generate interview questions from LLM service" in response.json()["detail"]
