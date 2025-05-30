from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
import datetime

class ResumeBase(BaseModel):
    filename: Optional[str] = None
    # raw_text is usually not sent in create, but populated by parser

class ResumeCreate(ResumeBase):
    # Fields needed at creation time, if any, beyond what's auto-populated
    pass

class ResumeRead(ResumeBase):
    id: UUID
    user_id: UUID
    content_hash: Optional[str] = None
    storage_path: Optional[str] = None
    # raw_text can be large, consider if it should always be returned in list views
    # For now, including it. Could have a ResumeReadList without raw_text.
    raw_text: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

class ResumeMetadata(BaseModel): # For listing resumes without full text
    id: UUID
    filename: Optional[str] = None
    content_hash: Optional[str] = None
    storage_path: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class Config:
        orm_mode = True
