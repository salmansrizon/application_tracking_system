from fastapi import FastAPI
from app.api.routers import auth as auth_router
from app.api.routers import jobs as jobs_router

app = FastAPI(title="Application Tracker Backend")
app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(jobs_router.router, prefix="/jobs", tags=["Job Applications"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
