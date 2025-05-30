from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4 # For job IDs and user IDs
import datetime

class JobApplicationBase(BaseModel):
    company: str
    position: str
    status: str = "applied" # Default status
    deadline: Optional[datetime.date] = None
    notes: Optional[str] = None

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationRead(JobApplicationBase):
    id: UUID
    user_id: UUID # To associate with the user who created it
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True # For SQLAlchemy or other ORMs later, good practice

class JobApplicationUpdate(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[datetime.date] = None
    notes: Optional[str] = None
