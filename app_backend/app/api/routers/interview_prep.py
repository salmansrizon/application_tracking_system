from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.schemas.auth_schemas import UserResponse # For current_user
from app.api.deps import get_current_user # Dependency
from app.services.supabase_client import supabase_client # To fetch resume text
from app.services.llm_service import generate_interview_questions_with_llm # The new LLM function
# Ensure InterviewPrepResult is not needed here if response model is InterviewQuestionResponse
from app.schemas.interview_prep_schemas import InterviewQuestionRequest, InterviewQuestionResponse # Schemas for this endpoint

router = APIRouter()

@router.post("/generate-questions", response_model=Optional[InterviewQuestionResponse], status_code=status.HTTP_200_OK)
async def generate_interview_questions_endpoint(
    request_data: InterviewQuestionRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    if supabase_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client not available")

    resume_text_to_use = ""
    if request_data.resume_text:
        resume_text_to_use = request_data.resume_text
    elif request_data.resume_id: # resume_id must be present if resume_text is not, due to Pydantic validator
        user_id_str = str(current_user.id)
        try:
            # Fetch the raw_text of the resume
            response = supabase_client.table("resumes").select("raw_text").eq("id", str(request_data.resume_id)).eq("user_id", user_id_str).maybe_single().execute()

            if response.data and "raw_text" in response.data and response.data["raw_text"] is not None:
                resume_text_to_use = response.data["raw_text"]
            else:
                # This case covers: no record found, or record found but raw_text is null/missing.
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resume with id {request_data.resume_id} not found, has no text, or access denied.")
        except Exception as e:
            # Log the actual error e for debugging
            print(f"Database error while fetching resume {request_data.resume_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error fetching resume.")

    # This check is after attempting to load/use provided text.
    if not resume_text_to_use.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume text for analysis is empty.")
    if not request_data.job_description_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text is empty.")

    # Call the LLM service function
    interview_prep_result = await generate_interview_questions_with_llm(resume_text_to_use, request_data.job_description_text)

    if interview_prep_result is None:
        # This means the LLM service had an issue (OpenAI API error, parsing error, etc.)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate interview questions from LLM service.")

    return interview_prep_result
