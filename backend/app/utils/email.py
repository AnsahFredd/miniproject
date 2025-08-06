import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException
from app.core.config import settings
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Thread pool for sending emails
executor = ThreadPoolExecutor(max_workers=5)


def send_confirmation_email(email: str, token: str) -> bool:
    if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
        logger.error("SMTP configuration incomplete")
        return False
    
    confirm_link = f"{settings.CORS_ORIGINS}/confirm-email?token={token}"
    subject="Confirm your LawLens account"

    # Create HTML version
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Confirm Your Account</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
            <h2 style="color: #333; text-align: center;">Welcome to LawLens!</h2>
            
            <p style="color: #666; font-size: 16px; line-height: 1.5;">
                Hello,
            </p>
            
            <p style="color: #666; font-size: 16px; line-height: 1.5;">
                Thank you for signing up for LawLens. Please confirm your email address by clicking the button below:
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{confirm_link}" 
                   style="background-color: #007bff; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;
                          font-weight: bold;">
                    Confirm Email Address
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px; line-height: 1.5;">
                Or copy and paste this link in your browser:
            </p>
            <p style="color: #007bff; font-size: 14px; word-break: break-all;">
                {confirm_link}
            </p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; line-height: 1.5;">
                <strong>Important:</strong>
                <br>• This link will expire in 24 hours
                <br>• If you didn't sign up for LawLens, please ignore this email
            </p>
            
            <p style="color: #999; font-size: 12px;">
                Best regards,<br>
                LawLens Team
            </p>
        </div>
    </body>
    </html>
    """

    # Plain text version
    text_body = f"""
    Welcome to LawLens!

    Thank you for signing up. Please confirm your email address by clicking the link below:

    {confirm_link}

    This link will expire in 24 hours.
    
    If you didn't sign up for LawLens, please ignore this email.

    Best regards,
    LawLens Team
    """
    

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_FROM
        msg['To'] = email

        # Attach both version
        msg.attach(MIMEText(text_body.strip(), 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authenticatin failed: {e}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Invlid recipient email {email}: {e}")
        return False
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"SMTP server diconnected: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")
        return False

async def send_confirmation_email_async(email: str, token: str) -> bool:
    """Async wrapper for send_confirmation_email"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, send_confirmation_email, email, token)


async def send_confirmation_email_with_retry(email: str, token: str, max_retries: int = 3) -> bool:
    """Send confirmation email with retry logic"""
    for attempt in range(max_retries):
        try:
            success = await send_confirmation_email_async(email, token)
            if success:
                logger.info(f"Confirmation email sent to {email} on attempt {attempt + 1}")
                return True
        except Exception as e:
            logger.warning(f"Email attempt {attempt + 1} failed for {email}: {str(e)}")
            
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)
    
    logger.error(f"Failed to send confirmation email to {email} after {max_retries} attempts")
    return False


def create_reset_email_body(reset_token: str, user_email: str) -> str:
    """Create HTML body for password reset email """
    reset_link = f"{settings.CORS_ORIGINS}/password-reset?token={reset_token}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Password Reset Request</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
            <h2 style="color: #333; text-align: center;">Password Reset Request</h2>
            
            <p style="color: #666; font-size: 16px; line-height: 1.5;">
                Hello,
            </p>
            
            <p style="color: #666; font-size: 16px; line-height: 1.5;">
                You have requested to reset your password for your account. 
                Click the button below to reset your password:
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" 
                   style="background-color: #007bff; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;
                          font-weight: bold;">
                    Reset Password
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px; line-height: 1.5;">
                Or copy and paste this link in your browser:
            </p>
            <p style="color: #007bff; font-size: 14px; word-break: break-all;">
                {reset_link}
            </p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; line-height: 1.5;">
                <strong>Important:</strong>
                <br>• This link will expire in {settings.RESET_TOKEN_EXPIRE_HOURS} hour(s)
                <br>• If you did not request this password reset, please ignore this email
                <br>• For security reasons, never share this link with anyone
            </p>
            
            <p style="color: #999; font-size: 12px;">
                Best regards,<br>
                Your App Team
            </p>
        </div>
    </body>
    </html>
    """
    return html_body


def create_reset_email_text(reset_token: str, user_email: str) -> str:
    """"Create plain text body for password reset email """
    reset_link = f"{settings.CORS_ORIGINS}/password-reset?token={reset_token}"

    text_body = f"""
        Password Reset Request

        Hello,

        You have requested to reset your password for your account.
        Click the link below to reset your password:

        {reset_link}

        IMPORTANT:
        - This link will expire in {settings.RESET_TOKEN_EXPIRE_HOURS} hour(s)
        - If you did not request this password reset, please ignore this email
        - For security reasons, never share this link with anyone

        Best regards,
        LawLens Team
            """
    return text_body.strip()

async def send_reset_email(email: str, reset_token: str) -> bool:
    """
    Send password reset email to user
    """
#    Check if email configuration is available
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning(f"Email not configured")
        return False
    
    try:
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "Password Reset Request"

        # Create both plain text and HTML versions
        text_only = create_reset_email_text(reset_token, email)
        html_body = create_reset_email_body(reset_token, email)

        # Creat MIMEText objects
        text_part = MIMEText(text_only, 'plain')
        html_part = MIMEText(html_body, 'html')

        # Attach parts to message
        msg.attach(text_part)
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

            logger.info(f"Password reset email sent to {email}")
            return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        raise HTTPException(status_code=500, detail="Email service authenticatin failed")

    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Invalid recipient email: {e}") 
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        raise HTTPException(status_code=500, detail="Email service temporary unavailable")
    

def send_password_changed_notification(email: str) -> bool:
    """Send notification email after password is successfully changed """
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning(f"Would send password changed notification to {email}")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.SMTP_FROM
        msg['To'] = email
        msg['Subject'] = "Password Changed Successfully"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h2 style="color: #28a745; text-align: center;">Password Successfully Changed</h2>
                
                <p style="color: #666; font-size: 16px; line-height: 1.5;">
                    Hello,
                </p>
                
                <p style="color: #666; font-size: 16px; line-height: 1.5;">
                    Your password has been successfully changed. If you did not make this change, 
                    please contact our support team immediately.
                </p>
                
                <p style="color: #999; font-size: 12px;">
                    Best regards,<br>
                    LawLens Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = """
            Password Successfully Changed

            Hello,

            Your password has been successfully changed. If you did not make this change, 
            please contact our support team immediately.

            Best regards,
            Your App Team
        """
        
        msg.attach(MIMEText(text_body.strip(), 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

            logger.info(f"Password reset notification sent to {email}")
            return True
    
    except Exception as e:
        logger.error(f"Failed to send password changed notification: {e}") 
        return False
        
    