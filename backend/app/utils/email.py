import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=5)


def _get_smtp_connection():
    """Return an SMTP or SMTP_SSL connection based on settings"""
    if settings.EXTERNAL_SERVICES.SMTP_SSL:
        server = smtplib.SMTP_SSL(
            settings.EXTERNAL_SERVICES.SMTP_HOST,
            settings.EXTERNAL_SERVICES.SMTP_PORT
        )
    else:
        server = smtplib.SMTP(
            settings.EXTERNAL_SERVICES.SMTP_HOST,
            settings.EXTERNAL_SERVICES.SMTP_PORT
        )
        if settings.EXTERNAL_SERVICES.SMTP_TLS:
            server.starttls()
    server.login(
        settings.EXTERNAL_SERVICES.SMTP_USERNAME,
        settings.EXTERNAL_SERVICES.SMTP_PASSWORD
    )
    return server


def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    """Generic function to send email"""
    if not (settings.EXTERNAL_SERVICES.SMTP_HOST and
            settings.EXTERNAL_SERVICES.SMTP_USERNAME and
            settings.EXTERNAL_SERVICES.SMTP_PASSWORD):
        logger.error("SMTP configuration incomplete")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.EXTERNAL_SERVICES.SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(text_body.strip(), "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with _get_smtp_connection() as server:
            server.send_message(msg)

        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


#  Confirmation Email 

def send_confirmation_email(email: str, token: str) -> bool:
    confirm_link = f"{settings.FRONTEND_URL}/confirm-email?token={token}"
    subject = "Confirm your LawLens account"

    text_body = f"""
    Welcome to LawLens!

    Please confirm your email by clicking the link below:
    {confirm_link}

    This link will expire in 24 hours.
    """

    html_body = f"""
    <html><body>
    <h2>Welcome to LawLens!</h2>
    <p>Please confirm your email by clicking the button below:</p>
    <a href="{confirm_link}" style="background:#007bff;color:#fff;padding:10px 20px;text-decoration:none;">
        Confirm Email
    </a>
    <p>If the button doesn't work, use this link: {confirm_link}</p>
    </body></html>
    """

    return send_email(email, subject, text_body, html_body)


async def send_confirmation_email_with_retry(email: str, token: str, max_retries: int = 3) -> bool:
    """Send confirmation email with retry logic"""
    for attempt in range(max_retries):
        success = await asyncio.get_event_loop().run_in_executor(executor, send_confirmation_email, email, token)
        if success:
            logger.info(f"Confirmation email sent to {email} on attempt {attempt + 1}")
            return True
        await asyncio.sleep(2 ** attempt)
    logger.error(f"Failed to send confirmation email to {email} after {max_retries} attempts")
    return False


# Password Reset Email 

def create_reset_email_bodies(reset_token: str) -> tuple[str, str]:
    reset_link = f"{settings.FRONTEND_URL}/password-reset?token={reset_token}"

    text_body = f"""
    Password Reset Request

    Reset your password using this link:
    {reset_link}

    This link will expire in {settings.EXTERNAL_SERVICES.RESET_TOKEN_EXPIRE_HOURS} hour(s).
    """

    html_body = f"""
    <html><body>
    <h2>Password Reset Request</h2>
    <p>Click the button below to reset your password:</p>
    <a href="{reset_link}" style="background:#007bff;color:#fff;padding:10px 20px;text-decoration:none;">
        Reset Password
    </a>
    <p>If the button doesn’t work, use this link: {reset_link}</p>
    </body></html>
    """

    return text_body, html_body


async def send_reset_email(email: str, reset_token: str) -> bool:
    subject = "Password Reset Request"
    text_body, html_body = create_reset_email_bodies(reset_token)
    return await asyncio.get_event_loop().run_in_executor(executor, send_email, email, subject, text_body, html_body)



#  Password Changed Notification

def send_password_changed_notification(email: str) -> bool:
    subject = "Password Changed Successfully"

    text_body = """
    Password Changed Successfully

    Your password has been changed. If this wasn’t you, contact support immediately.
    """

    html_body = """
    <html><body>
    <h2 style="color:green;">Password Changed Successfully</h2>
    <p>Your password has been changed. If this wasn’t you, contact support immediately.</p>
    </body></html>
    """

    return send_email(email, subject, text_body, html_body)
