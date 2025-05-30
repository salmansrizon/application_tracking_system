from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr # EmailStr for type validation of email addresses
from typing import List, Dict, Any, Optional # Added Optional
from app.core.config import settings
import os # Not strictly needed here if Path is not used for template_folder based on current logic
from pathlib import Path # For potential template folder path construction

# Determine template directory
# template_folder = None # Initialize
# if settings.MAIL_TEMPLATES_DIR:
# # This assumes MAIL_TEMPLATES_DIR is a path relative to the project root or an absolute path.
# # FastAPI-Mail might have specific expectations for how this path is resolved,
# # often it's relative to the location of this config or the main app file.
# # For robust template discovery, ensure this path is correctly set and accessible.
# template_folder = Path(settings.MAIL_TEMPLATES_DIR)

conf = None
# Check for essential mail server settings before attempting to create ConnectionConfig
if settings.MAIL_SERVER and settings.MAIL_FROM:
    # Ensure MAIL_FROM is valid before passing to ConnectionConfig
    try:
        valid_mail_from = EmailStr(settings.MAIL_FROM) # Validate/convert MAIL_FROM
    except ValueError: # Pydantic's EmailStr validation error
        print(f"Warning: Invalid MAIL_FROM email address '{settings.MAIL_FROM}'. Email service may not function correctly.")
        valid_mail_from = "fallback@example.com" # Or handle as critical error

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=valid_mail_from,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True if settings.MAIL_USERNAME and settings.MAIL_PASSWORD else False,
        VALIDATE_CERTS=True, # Good practice for production, ensure your server cert is valid if True
        # TEMPLATE_FOLDER=template_folder if template_folder else None, # Set if using Jinja2 templates
    )
else:
    print("Warning: Email service is not fully configured. Essential settings (MAIL_SERVER, MAIL_FROM) are missing.")

# Initialize FastMail instance only if configuration is valid
fm: Optional[FastMail] = None
if conf:
    fm = FastMail(conf)
else:
    print("FastMail instance not created due to missing configuration.")


async def send_email_async(
    recipients: List[EmailStr],
    subject: str,
    html_content: str,
    # template_name: Optional[str] = None, # Uncomment if using templates
    # template_body: Optional[Dict[str, Any]] = None # Uncomment if using templates
):
    if not fm:
        print("Email service (FastMail) is not initialized or configured. Cannot send email.")
        return False # Indicate failure or raise an exception

    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=html_content,
        subtype=MessageType.html,
        # template_body=template_body, # Use if using template_name
    )

    try:
        # if template_name and fm.config.TEMPLATE_FOLDER: # Check if templates are configured
        #     await fm.send_message(message, template_name=template_name)
        # else:
        await fm.send_message(message) # Send non-template message

        print(f"Email sent to {', '.join(recipients)} with subject: '{subject}'")
        return True
    except Exception as e:
        print(f"Failed to send email. Error: {e}")
        # In a production app, log this error more formally (e.g., to Sentry, or a logging service)
        return False

# Example usage (not part of the service, just for illustration):
# async def send_test_email_example():
#     success = await send_email_async(
#         recipients=["test@example.com"],
#         subject="Test Email from FastAPI App",
#         html_content="<p>This is a <strong>test email</strong> sent from the application.</p>"
#     )
#     if success:
#         print("Test email sent successfully.")
#     else:
#         print("Failed to send test email.")
