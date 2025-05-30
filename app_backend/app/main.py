from fastapi import FastAPI
from app.api.routers import auth as auth_router
from app.api.routers import jobs as jobs_router
from app.api.routers import resumes as resumes_router
from app.api.routers import interview_prep as interview_prep_router
from app.api.routers import admin_tasks as admin_tasks_router # Added

app = FastAPI(title="Application Tracker Backend")
app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(jobs_router.router, prefix="/jobs", tags=["Job Applications"])
app.include_router(resumes_router.router, prefix="/resumes", tags=["Resumes"])
app.include_router(interview_prep_router.router, prefix="/interview", tags=["Interview Preparation"])
app.include_router(admin_tasks_router.router, prefix="/admin-tasks", tags=["Admin Tasks"]) # Added

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
