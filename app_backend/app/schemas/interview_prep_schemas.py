from pydantic import BaseModel, model_validator as pydantic_model_validator_v2
from typing import Optional, List # Ensure List is imported if InterviewPrepResult uses it directly here
from uuid import UUID
from app.services.llm_service import InterviewPrepResult # Import the structure

class InterviewQuestionRequest(BaseModel):
    resume_id: Optional[UUID] = None
    resume_text: Optional[str] = None
    job_description_text: str

    @pydantic_model_validator_v2(mode='before')
    @classmethod # Pydantic v2 model_validator with mode='before' should be a classmethod
    def check_resume_source(cls, data): # data is a dict here
        if not isinstance(data, dict): # Should be a dict from request
             raise ValueError('Request data must be a dictionary')

        resume_id = data.get('resume_id')
        resume_text = data.get('resume_text')

        # Convert empty string for resume_text to None for validation logic
        if resume_text == "":
            resume_text = None
            data['resume_text'] = None # Update data if modifying

        if resume_id is None and resume_text is None: # Neither provided
            raise ValueError('Either resume_id or resume_text must be provided')
        if resume_id is not None and resume_text is not None: # Both provided
            raise ValueError('Provide either resume_id or resume_text, not both')
        return data

class InterviewQuestionResponse(InterviewPrepResult): # Inherits from the one in llm_service
    pass
