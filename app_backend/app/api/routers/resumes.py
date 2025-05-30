from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from uuid import UUID
import mimetypes

from app.schemas.resume_schemas import ResumeCreate, ResumeRead, ResumeMetadata
from app.schemas.auth_schemas import UserResponse
from app.api.deps import get_current_user
from app.services.supabase_client import supabase_client
from app.services.file_parser_service import parse_pdf, parse_docx, calculate_sha256_hash
from app.services.llm_service import analyze_resume_with_llm
from app.schemas.analysis_schemas import ResumeAnalysisRequest, ResumeAnalysisResponse
from app.services.vector_service import upsert_resume_embedding, delete_resume_embedding # Added for Qdrant

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document" # for .docx
]


@router.post("/upload", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    if supabase_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client not available")

    user_id_str = str(current_user.id)

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File size exceeds limit of {MAX_FILE_SIZE / (1024*1024)}MB")

    mime_type = file.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        guessed_mime_type, _ = mimetypes.guess_type(file.filename or "")
        if guessed_mime_type not in ALLOWED_MIME_TYPES:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type: {mime_type or guessed_mime_type}. Allowed types: PDF, DOCX.")
        mime_type = guessed_mime_type

    content_hash = calculate_sha256_hash(file_content)

    try:
        existing_response = supabase_client.table("resumes").select("id, filename, content_hash, raw_text, storage_path, user_id, created_at, updated_at").eq("user_id", user_id_str).eq("content_hash", content_hash).maybe_single().execute()
        if existing_response.data:
            # If duplicate for this user, still good to ensure embedding exists
            try:
                existing_resume_id = UUID(existing_response.data["id"])
                existing_user_id = UUID(user_id_str)
                existing_raw_text = existing_response.data.get("raw_text", "")
                if existing_raw_text: # Only upsert if text exists
                     await upsert_resume_embedding(resume_id=existing_resume_id, user_id=existing_user_id, resume_text=existing_raw_text)
            except Exception as q_e:
                print(f"Qdrant upsert for existing resume {existing_response.data.get('id')} failed during re-upload: {q_e}")
            return ResumeRead(**existing_response.data)
    except Exception as e:
        print(f"Could not check for existing resume hash: {e}")

    raw_text = ""
    if mime_type == "application/pdf":
        raw_text = parse_pdf(file_content)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        raw_text = parse_docx(file_content)

    if not raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract text from the resume.")

    resume_data_to_insert = {
        "user_id": user_id_str,
        "filename": file.filename,
        "content_hash": content_hash,
        "raw_text": raw_text,
    }

    try:
        response = supabase_client.table("resumes").insert(resume_data_to_insert).execute()
        if response.data:
            saved_resume_data = response.data[0]
            # Upsert embedding to Qdrant
            try:
                resume_db_id = UUID(saved_resume_data["id"])
                user_db_id = UUID(user_id_str) # user_id_str is current_user.id as string
                await upsert_resume_embedding(resume_id=resume_db_id, user_id=user_db_id, resume_text=raw_text)
            except Exception as q_e:
                print(f"Qdrant upsert failed for new resume {saved_resume_data['id']}: {q_e}") # Log and continue

            return ResumeRead(**saved_resume_data)
        else:
            error_detail = "Failed to save resume metadata."
            if hasattr(response, 'error') and response.error:
                error_detail = f"Failed to save resume metadata: {response.error.message}"
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_detail)
    except Exception as e:
        if "unique constraint" in str(e).lower() and "resumes_content_hash_key" in str(e).lower():
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"This resume content has already been processed.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error while saving resume: {str(e)}")


@router.get("/", response_model=List[ResumeMetadata])
async def list_resumes(current_user: UserResponse = Depends(get_current_user)):
    # ... (rest of the function remains the same)
    if supabase_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client not available")
    user_id_str = str(current_user.id)
    try:
        response = supabase_client.table("resumes").select("id, filename, content_hash, storage_path, created_at, updated_at").eq("user_id", user_id_str).order("updated_at", desc=True).execute()
        if response.data:
            return [ResumeMetadata(**resume) for resume in response.data]
        return []
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")

@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume_details(resume_id: UUID, current_user: UserResponse = Depends(get_current_user)):
    # ... (rest of the function remains the same)
    if supabase_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client not available")
    user_id_str = str(current_user.id)
    try:
        response = supabase_client.table("resumes").select("*").eq("id", str(resume_id)).eq("user_id", user_id_str).maybe_single().execute()
        if response.data:
            return ResumeRead(**response.data)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found or access denied")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")

@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: UUID, current_user: UserResponse = Depends(get_current_user)):
    if supabase_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client not available")
    user_id_str = str(current_user.id)

    try:
        # First, verify the resume exists for the user (RLS also handles this)
        check_response = supabase_client.table("resumes").select("id").eq("id", str(resume_id)).eq("user_id", user_id_str).maybe_single().execute()
        if not check_response.data:
            # This ensures we don't try to delete from Qdrant if not found in DB or not owned.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found or access denied for delete")

        db_response = supabase_client.table("resumes").delete().eq("id", str(resume_id)).eq("user_id", user_id_str).execute()
        # No specific check on db_response.data needed if check_response passed and no exception from delete.

        # Delete from Qdrant
        try:
            await delete_resume_embedding(resume_id=resume_id)
        except Exception as q_e:
            print(f"Qdrant delete failed for resume {resume_id}: {q_e}") # Log and continue, DB record is deleted.

    except HTTPException as http_exc: # Re-raise HTTP exceptions from the check
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during delete: {str(e)}")

    return

@router.post("/analyze", response_model=Optional[ResumeAnalysisResponse], status_code=status.HTTP_200_OK)
async def analyze_resume_endpoint_route(request_data: ResumeAnalysisRequest, current_user: UserResponse = Depends(get_current_user)):
    # ... (rest of the function remains the same)
    if supabase_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client not available")

    resume_text_to_analyze = ""
    if request_data.resume_text:
        resume_text_to_analyze = request_data.resume_text
    elif request_data.resume_id:
        user_id_str = str(current_user.id)
        try:
            response = supabase_client.table("resumes").select("raw_text").eq("id", str(request_data.resume_id)).eq("user_id", user_id_str).maybe_single().execute()
            if response.data and "raw_text" in response.data and response.data["raw_text"] is not None:
                resume_text_to_analyze = response.data["raw_text"]
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resume with id {request_data.resume_id} not found, has no text, or access denied.")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")

    if not resume_text_to_analyze.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume text for analysis is empty.")
    if not request_data.job_description_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text is empty.")

    analysis_result = await analyze_resume_with_llm(resume_text_to_analyze, request_data.job_description_text)
    if analysis_result is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LLM analysis failed.")
    return analysis_result
