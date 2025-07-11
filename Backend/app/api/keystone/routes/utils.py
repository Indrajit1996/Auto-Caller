from fastapi import APIRouter
from pydantic.networks import EmailStr

from app.api.deps import IsSuperUser
from app.emails.utils import generate_test_email, send_email
from app.schemas.common import Message

router = APIRouter(
    prefix="/utils",
    tags=["utils"],
)


@router.post(
    "/test-email/",
    dependencies=[IsSuperUser],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True
