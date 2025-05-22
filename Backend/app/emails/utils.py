from dataclasses import dataclass
from pathlib import Path
from typing import Any

import emails  # type: ignore
from jinja2 import Template
from loguru import logger

from app.core.config import config


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent / "templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    # test = 1/0
    """Send email and update email status if provided"""
    assert config.emails_enabled, "no provided configuration for email variables"

    try:
        message = emails.Message(
            subject=subject,
            html=html_content,
            mail_from=(config.EMAILS_FROM_NAME, config.EMAILS_FROM_EMAIL),
        )

        smtp_options = {"host": config.SMTP_HOST, "port": config.SMTP_PORT}
        if config.SMTP_TLS:
            smtp_options["tls"] = True
        elif config.SMTP_SSL:
            smtp_options["ssl"] = True
        if config.SMTP_USER:
            smtp_options["user"] = config.SMTP_USER
        if config.SMTP_PASSWORD:
            smtp_options["password"] = config.SMTP_PASSWORD

        response = message.send(to=email_to, smtp=smtp_options)

        if response.status_code == 250:
            logger.info(f"Email sent to {email_to}")

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")


def generate_test_email(email_to: str) -> EmailData:
    project_name = config.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": config.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    project_name = config.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": config.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": config.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)
