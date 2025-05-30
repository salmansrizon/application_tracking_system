import openai
from app.core.config import settings
import json
from pydantic import BaseModel, Field, validator as pydantic_validator_v1
from typing import List, Optional

# Basic check, actual client instantiation with key is done per call or globally
if not settings.OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not set. LLM service will not function.")

class LLMAnalysisResult(BaseModel):
    match_score: int = Field(..., description="Overall match score, 0-100.")
    missing_keywords: List[str] = Field(default_factory=list)
    strength_summary: str = Field(...)
    improvement_suggestions: List[str] = Field(default_factory=list)
    ats_compatibility_check: str = Field(...)

    @pydantic_validator_v1('match_score')
    def score_in_range(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Match score must be 0-100')
        return v

async def analyze_resume_with_llm(resume_text: str, job_description_text: str) -> Optional[LLMAnalysisResult]:
    if not settings.OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not configured. Cannot perform LLM analysis.")
        return None
    # Simplified prompt for subtask stability
    prompt = f"Analyze this resume: {resume_text} against this job description: {job_description_text}. Return JSON with keys: match_score, missing_keywords, strength_summary, improvement_suggestions, ats_compatibility_check."
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        completion = await client.chat.completions.create(
            model="gpt-3.5-turbo-0125", # Ensure this model is available
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an AI Resume Analyzer. Output ONLY JSON that strictly matches the requested schema."},
                {"role": "user", "content": prompt}
            ]
        )
        raw_response = completion.choices[0].message.content
        if not raw_response:
            print("LLM analysis error: Empty response from API.")
            return None

        # Attempt to parse the JSON, handling potential errors
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as e:
            print(f"LLM analysis error: Failed to decode JSON response: {e}")
            print(f"Raw response was: {raw_response}")
            return None # Or perhaps raise a specific error / return a default error structure

        # Validate with Pydantic model
        return LLMAnalysisResult(**data)
    except Exception as e:
        print(f"LLM analysis error: {e}")
        return None

# Added for Interview Prep
class InterviewQuestion(BaseModel):
    question: str
    category: str # e.g., "Behavioral", "Technical", "Situational"

class InterviewPrepResult(BaseModel):
    generated_questions: List[InterviewQuestion] = Field(default_factory=list)
    preparation_tips: List[str] = Field(default_factory=list, description="General tips based on the JD/resume.")

async def generate_interview_questions_with_llm(resume_text: str, job_description_text: str) -> Optional[InterviewPrepResult]:
    if not settings.OPENAI_API_KEY:
        print("OpenAI API key not configured. Cannot generate interview questions.")
        return None

    system_prompt = '''You are an AI Interview Coach. Your task is to generate insightful interview questions based on a candidate's resume and a specific job description.
Provide your output ONLY as a JSON object with the following structure:
{
  "generated_questions": [
    { "category": "Behavioral", "question": "<Generated behavioral question>" },
    { "category": "Technical", "question": "<Generated technical question relevant to skills in JD/resume>" },
    { "category": "Situational", "question": "<Generated situational question based on JD challenges>" }
  ],
  "preparation_tips": [
    "<General tip 1 for preparing for an interview for this role, based on JD/resume>",
    "<General tip 2...>"
  ]
}
Focus on questions that help the candidate showcase their experience relevant to the job.
For technical questions, ensure they relate to skills mentioned in the resume or required by the job description.
Aim for a mix of 5-7 good questions in total.
'''

    user_prompt = f'''Please generate interview questions and preparation tips based on the following resume and job description.

**Resume:**
---
{resume_text}
---

**Job Description:**
---
{job_description_text}
---

Provide your output in the specified JSON format.
'''

    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        completion = await client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=1800 # Increased token limit
        )

        raw_response_content = completion.choices[0].message.content
        if not raw_response_content:
            print("LLM returned empty content for interview questions.")
            return None

        parsed_json = json.loads(raw_response_content)
        return InterviewPrepResult(**parsed_json)

    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response for interview questions as JSON: {e}")
        raw_content_for_print = raw_response_content if 'raw_response_content' in locals() else 'N/A'
        print(f"Raw LLM response: {raw_content_for_print}")
        return None
    except openai.APIError as e: # Specific catch for OpenAI API errors
        print(f"OpenAI API error during interview question generation: {e.type if hasattr(e, 'type') else 'Unknown API Error'}") # More detailed error logging
        if hasattr(e, 'response') and e.response is not None:
            print(f"OpenAI API response status: {e.response.status_code}")
            try:
                print(f"OpenAI API response data: {e.response.json()}")
            except:
                print(f"OpenAI API response data (not JSON): {e.response.text}")

        return None
    except Exception as e:
        print(f"An unexpected error occurred during interview question generation: {e}")
        return None
