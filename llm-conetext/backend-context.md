# Application Tracker System - Backend Context

## Purpose
To provide a scalable backend for:
1. Tracking job applications (status, deadlines, companies)
2. Resume analysis against job descriptions (via LLMs)
3. Interview prep tools
4. User authentication and data persistence

## Key Features
- CRUD operations for job applications
- Resume analysis endpoint (LLM-powered keyword/skill matching)
- Job description parser
- Status change notifications
- User-specific data isolation

```
app/
├── api/ # REST API routes
│ ├── jobs/ # Job tracking endpoints
│ ├── resume/ # Resume analysis endpoints
│ ├── auth/ # User auth (Supabase integration)
│ └── utils/ # Helper functions
├── core/ # Core logic/config
├── models/ # ORM models (Job, Resume, User)
├── services/
│ ├── llm/ # LLM service for resume analysis
│ ├── supabase/ # Auth/data management
│ └── notification/ # Email/SMS alerts
```

## API Endpoints
| Endpoint | Method | Description |
|---------|--------|-------------|
| `/jobs` | GET/POST | Manage job applications |
| `/resume/analyze` | POST | Analyze resume vs job description |
| `/applications/{id}/status` | PUT | Update application status |
| `/auth/login` | POST | Supabase-powered auth |

## LLM Integration
- **Resume Analysis Service**:
  ```python
  def analyze_resume(resume_text: str, job_description: str):
      """Uses Openai  to compare resume against job requirements"""
      prompt = f"""
      Compare this resume:
      {resume_text}
      
      Against this job description:
      {job_description}
      
      Score:
      - Relevance (0-10)
      - Missing keywords
      - Recommended improvements
      """
      return openai_client.generate(prompt)
```

class Job(SQLModel):
    id: int
    company: str
    position: str
    deadline: date
    status: str  # "applied", "interview", "offer", etc.

class Resume(SQLModel):
    id: int
    user_id: str
    content: str  # Raw text/URL to PDF
    last_analyzed: datetime
 
## Environment Variables
OPENAI_API_KEY=your_key
SUPABASE_URL=your_project.supabase.co
SUPABASE_KEY=your_anon_key
QDRANT_HOST=localhost


## Integrations
- Supabase : Authentication and PostgreSQL storage
- OpenAI : Resume/job description analysis
- Qdrant : Vector storage for resume embeddings (for similarity search)



