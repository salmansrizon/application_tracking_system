# Backend Requirements

## 1. Purpose
To provide a scalable backend for:
- Tracking job applications (including status, deadlines, and company information).
- Performing resume analysis against job descriptions using Large Language Models (LLMs).
- Offering interview preparation tools.
- Managing user authentication and ensuring data persistence.

## 2. Key Features
- **Job Application Management:** Implement full CRUD (Create, Read, Update, Delete) operations for job applications.
- **Resume Analysis Endpoint:** Provide an endpoint for LLM-powered resume analysis, focusing on keyword/skill matching against job descriptions.
- **Job Description Parser:** Develop a utility to parse relevant information from job descriptions.
- **Status Change Notifications:** Alert users to updates in their application statuses.
- **User-Specific Data Isolation:** Ensure that each user's data is kept separate and private.

## 3. API Endpoints
The backend will expose the following REST API endpoints:

| Endpoint                   | Method   | Description                                         |
|----------------------------|----------|-----------------------------------------------------|
| `/jobs`                    | GET, POST| Manage job applications (list all, create new)      |
| `/jobs/{id}`               | GET, PUT, DELETE | Manage a specific job application (view, update, delete) |
| `/resume/analyze`          | POST     | Analyze a resume against a job description          |
| `/applications/{id}/status`| PUT      | Update the status of a specific job application     |
| `/auth/login`              | POST     | Handle user authentication (Supabase integration)   |
| `/auth/register`           | POST     | Handle user registration (Supabase integration)  |
| `/auth/logout`             | POST     | Handle user logout                                  |

*(Note: Specific details for request/response bodies for each endpoint will be defined in a separate API documentation.)*

## 4. LLM Integration for Resume Analysis
- **Service:** `resume.analyze_resume(resume_text: str, job_description: str)`
- **Functionality:** Utilizes an OpenAI model to compare the provided resume text against the job description.
- **Output Metrics:**
    - Relevance Score (0-10)
    - List of Missing Keywords/Skills
    - Recommended Improvements for the resume

## 5. Database Models
The following ORM models will be used (e.g., with SQLModel or SQLAlchemy):

### Job
- `id`: Integer (Primary Key) or UUID
- `user_id`: UUID (Foreign Key to User model)
- `company`: String
- `position`: String
- `deadline`: Date
- `status`: String (e.g., "applied", "interview", "offer", "rejected")
- `notes`: Text (Optional)
- `job_description_url`: String (Optional)
- `created_at`: DateTime
- `updated_at`: DateTime

### Resume
- `id`: Integer (Primary Key) or UUID
- `user_id`: UUID (Foreign Key to User model)
- `content`: Text (raw text of the resume) or URL to PDF/DOCX
- `original_filename`: String (Optional, if uploaded)
- `last_analyzed`: DateTime (Timestamp of the last analysis)
- `created_at`: DateTime
- `updated_at`: DateTime

### User (Managed primarily by Supabase Auth, but may need a local representation)
- `id`: UUID (Primary Key, typically from Supabase Auth)
- `email`: String
- `created_at`: DateTime
- `updated_at`: DateTime

## 6. Technology Stack
- **Framework:** FastAPI (Python 3.10+)
- **LLM:** OpenAI GPT-4 (or specified alternative like Anthropic Claude)
- **Database:** PostgreSQL (managed via Supabase)
- **Authentication:** Supabase Auth
- **Vector Database:** Qdrant (for semantic resume embeddings and similarity search)
- **File Handling:** Libraries like `PyPDF2` for PDF parsing and `python-docx` for DOCX parsing.
- **Task Queue (Recommended):** Celery with a message broker (e.g., RabbitMQ/Redis) for handling asynchronous tasks like resume analysis.

## 7. Environment Variables
The backend will require the following environment variables for configuration:
- `OPENAI_API_KEY`: API key for the LLM service.
- `SUPABASE_URL`: URL for the Supabase project.
- `SUPABASE_KEY`: Anon key for Supabase.
- `QDRANT_HOST`: Hostname for the Qdrant vector database.
- `DATABASE_URL`: Connection string for the PostgreSQL database (if accessed directly, otherwise managed by Supabase SDK).
- `JWT_SECRET_KEY`: Secret key for JWT token generation/validation (if custom JWT logic is implemented alongside Supabase).
- `CELERY_BROKER_URL` (if Celery is used)
- `CELERY_RESULT_BACKEND` (if Celery is used)

## 8. Integrations
- **Supabase:** For user authentication and PostgreSQL database storage.
- **OpenAI/Anthropic:** For LLM-powered resume analysis and other AI features.
- **Qdrant:** For storing and searching resume and job description embeddings.

This document outlines the core backend requirements. Further details, such as specific data validation rules, error handling procedures, and detailed API request/response schemas, will be specified in subsequent documentation (e.g., API design documents, detailed design specifications).
