from pydantic import BaseModel, model_validator as pydantic_model_validator_v2
from typing import Optional
from uuid import UUID
# Assuming LLMAnalysisResult will be imported correctly in the router or defined/imported here
from app.services.llm_service import LLMAnalysisResult

class ResumeAnalysisRequest(BaseModel):
    resume_id: Optional[UUID] = None
    resume_text: Optional[str] = None
    job_description_text: str

    @pydantic_model_validator_v2(mode='before') # Use 'before' for Pydantic v2 if needed, or just 'pre=True' in Pydantic v1 validator
    @classmethod # model_validator in Pydantic v2 should be a classmethod if used with mode='before'
    def check_resume_source(cls, data):
        if isinstance(data, dict): # Ensure data is a dict before accessing .get
            resume_id = data.get('resume_id')
            resume_text = data.get('resume_text')

            # Convert empty strings for optional fields to None to avoid issues with mutually exclusive check
            if resume_text == "":
                resume_text = None
                data['resume_text'] = None # Update data if modifying

            if resume_id is None and resume_text is None:
                raise ValueError('Either resume_id or resume_text must be provided')
            if resume_id is not None and resume_text is not None:
                raise ValueError('Provide resume_id or resume_text, not both')
        return data

class ResumeAnalysisResponse(LLMAnalysisResult): # Inherits from the one in llm_service
    pass
