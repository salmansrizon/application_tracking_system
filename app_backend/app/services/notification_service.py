from app.services.supabase_client import supabase_client
from app.services.email_service import send_email_async # Assuming this is created
from datetime import date, timedelta, datetime
from pydantic import EmailStr # Assuming EmailStr is used in email_service
from typing import List, Dict, Any

async def check_job_deadlines_and_notify():
    if not supabase_client:
        print("Supabase client not available. Cannot check deadlines.")
        return {"status": "error", "message": "Supabase client not available."}

    today = date.today()
    # Define reminder intervals (e.g., 1, 3, 7 days away)
    reminder_intervals = {
        "1 Day Reminder": today + timedelta(days=1),
        "3 Day Reminder": today + timedelta(days=3),
        "7 Day Reminder": today + timedelta(days=7)
    }
    # Max lookahead to fetch jobs efficiently
    max_lookahead_date = today + timedelta(days=7)

    notifications_sent = 0
    errors_occurred = 0

    try:
        active_statuses = ["applied", "interviewing", "wishlist", "interested"] # Added 'interested' or similar statuses

        # Fetch jobs with deadlines within the lookahead window and are active
        jobs_response = supabase_client.table("job_applications")\
            .select("id, company, position, deadline, user_id")\
            .gte("deadline", today.isoformat())\
            .lte("deadline", max_lookahead_date.isoformat())\
            .in_("status", active_statuses)\
            .execute()

        if jobs_response.data:
            user_emails_cache: Dict[str, EmailStr] = {}

            for job in jobs_response.data:
                job_deadline_str = job.get("deadline")
                if not job_deadline_str: continue

                job_deadline_date = date.fromisoformat(job_deadline_str)
                user_id = job.get("user_id")
                if not user_id: continue

                current_reminder_type = None
                for reminder_name, reminder_date in reminder_intervals.items():
                    if job_deadline_date == reminder_date:
                        current_reminder_type = reminder_name
                        break

                if not current_reminder_type:
                    continue

                if user_id not in user_emails_cache:
                    # Fetch user email from Supabase auth.users table
                    # This requires admin privileges for the Supabase client if RLS is restrictive on auth.users
                    # Or, preferably, a separate 'profiles' table linked to user_id that stores email.
                    try:
                        # IMPORTANT: This is a simplified way to get email.
                        # The service key used for supabase_client MUST have rights to read auth.users.
                        # If your RLS on auth.users is too restrictive, or you use row-level on a profiles table, adjust accordingly.
                        # Consider if this direct auth.users access is appropriate for your security model.
                        # A dedicated function in supabase_client service might be better if it needs special handling.
                        # For now, directly using the admin client assumed to be configured for supabase_client.

                        # This is a placeholder for fetching email.
                        # In a real application, you would have a profiles table or use an admin client
                        # to fetch user details from auth.users table.
                        # For this example, we'll simulate it if a specific "test" user ID is encountered.
                        # Replace with actual user email fetching logic.
                        # This part is CRITICAL and needs a secure, robust implementation.
                        # For the purpose of this task, let's assume it's a placeholder.
                        # It's commented out because without a real way to fetch email, it will fail for most users.
                        # user_details_response = supabase_client.auth.admin.get_user_by_id(user_id) # Requires admin client
                        # if user_details_response and user_details_response.user and user_details_response.user.email:
                        #    user_emails_cache[user_id] = EmailStr(user_details_response.user.email)
                        # else:
                        #    print(f"Could not fetch email for user_id: {user_id}. User might not exist or email is null.")
                        #    continue
                        pass # Pass for now, as email fetching is complex and context-dependent

                    except Exception as e_user:
                        print(f"Error fetching email for user {user_id}: {e_user}")
                        errors_occurred += 1
                        continue

                # This check will now likely fail unless user_emails_cache is populated by a real mechanism
                user_email = user_emails_cache.get(user_id)
                if not user_email:
                    print(f"Skipping notification for job {job.get('id')} as email for user {user_id} was not found in cache (real fetching logic needed).")
                    continue


                subject = f"{current_reminder_type}: Job Application Deadline - {job['company']} ({job['position']})"
                html_content = (
                    f"<p>Hi,</p>"
                    f"<p>This is a {current_reminder_type.lower()} that the deadline for your job application for the position of "
                    f"<strong>{job['position']}</strong> at <strong>{job['company']}</strong> is approaching on "
                    f"<strong>{job_deadline_str}</strong>.</p>"
                    f"<p>Don't miss out! You can view your application details here: [Link to application]</p>" # Placeholder link
                    f"<p>Best regards,<br/>The Application Tracker Team</p>"
                )

                email_sent = await send_email_async(recipients=[user_email], subject=subject, html_content=html_content)
                if email_sent:
                    notifications_sent += 1
                else:
                    errors_occurred += 1

        result_message = f"Deadline check finished. Notifications sent: {notifications_sent}. Errors: {errors_occurred}."
        print(result_message)
        return {
            "status": "completed",
            "message": result_message,
            "notifications_sent": notifications_sent,
            "errors": errors_occurred
        }

    except Exception as e:
        print(f"Error during deadline check process: {e}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}
