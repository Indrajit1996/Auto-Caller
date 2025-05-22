from unittest.mock import Mock

from fastapi.testclient import TestClient


def test_health_check(unauthorized_client: TestClient):
    """Test the health check endpoint."""
    response = unauthorized_client.get("/utils/health-check/")

    assert response.status_code == 200
    assert response.json() is True


def test_test_email_unauthorized(unauthorized_client: TestClient):
    """Test that unauthorized users cannot access the test email endpoint."""
    response = unauthorized_client.post(
        "/utils/test-email/", json={"email_to": "test@example.com"}
    )

    assert response.status_code == 401


def test_test_email_normal_user(authorized_client: TestClient):
    """Test that normal users cannot access the test email endpoint."""
    response = authorized_client.post(
        "/utils/test-email/", json={"email_to": "test@example.com"}
    )

    assert response.status_code == 403


def test_test_email(superuser_client: TestClient, mock_send_email: Mock):
    """Test the test email endpoint."""
    email = "test@example.com"
    response = superuser_client.post("/utils/test-email/", params={"email_to": email})

    assert response.status_code == 201
    assert response.json() == {"message": "Test email sent"}

    # Verify the mock was called correctly
    mock_send_email.assert_called_once()
    call_args = mock_send_email.call_args[1]
    assert call_args["email_to"] == email
    assert "subject" in call_args
    assert "html_content" in call_args
