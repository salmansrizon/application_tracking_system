from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from app.services.notification_service import check_job_deadlines_and_notify
from app.core.config import settings # To get BACKGROUND_TASK_ADMIN_SECRET
from typing import Annotated # For Header type hint

router = APIRouter()

# Dependency to check for the admin secret
async def verify_admin_secret(x_admin_secret: Annotated[str, Header(description="Admin secret key to authorize this operation.")]):
    # Ensure settings.BACKGROUND_TASK_ADMIN_SECRET is not None or empty for comparison
    if not settings.BACKGROUND_TASK_ADMIN_SECRET or x_admin_secret != settings.BACKGROUND_TASK_ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this admin task.")
    return True


@router.post("/trigger-deadline-check",
             summary="Manually trigger job deadline check and notifications",
             dependencies=[Depends(verify_admin_secret)])
async def trigger_deadline_check_endpoint(background_tasks: BackgroundTasks):
    print("Triggering deadline check in background via admin endpoint...")
    # The check_job_deadlines_and_notify function is async, background_tasks.add_task handles it.
    background_tasks.add_task(check_job_deadlines_and_notify)
    return {"message": "Job deadline check process initiated in the background. Check server logs for details and results."}
