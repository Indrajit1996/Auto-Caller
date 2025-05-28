import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def test_settings_update_data():
    """Test data for updating user settings."""
    return {"receive_email_notifications": True}


def test_settings_creation_on_first_read(authorized_client: TestClient):
    """Test that settings are created if they don't exist when first accessed."""
    # The first call to this endpoint should create settings if they don't exist
    response = authorized_client.get("/user-settings/me")

    assert response.status_code == status.HTTP_200_OK
    settings = response.json()

    # Default value for receive_email_notifications should be False
    assert settings["receive_email_notifications"] is False


def test_read_my_settings(authorized_client: TestClient, test_normal_user):
    """Test getting the current user's settings."""
    response = authorized_client.get("/user-settings/me")

    assert response.status_code == status.HTTP_200_OK

    settings = response.json()
    assert "user_id" in settings
    assert "receive_email_notifications" in settings
    assert "updated_at" in settings
    assert settings["user_id"] == str(test_normal_user.id)


def test_update_my_settings(
    authorized_client: TestClient, test_normal_user, test_settings_update_data
):
    """Test updating the current user's settings."""
    # First, get the current settings
    get_response = authorized_client.get("/user-settings/me")
    assert get_response.status_code == status.HTTP_200_OK

    original_settings = get_response.json()

    # Update settings
    update_response = authorized_client.patch(
        "/user-settings/me", json=test_settings_update_data
    )

    assert update_response.status_code == status.HTTP_200_OK

    updated_settings = update_response.json()
    assert updated_settings["user_id"] == str(test_normal_user.id)
    assert (
        updated_settings["receive_email_notifications"]
        == test_settings_update_data["receive_email_notifications"]
    )
    assert updated_settings["updated_at"] != original_settings["updated_at"]


def test_settings_partial_update(authorized_client: TestClient):
    """Test that settings can be partially updated."""
    # Set initial value
    initial_update = {"receive_email_notifications": False}
    authorized_client.patch("/user-settings/me", json=initial_update)

    # Update with new value
    update_data = {"receive_email_notifications": True}
    response = authorized_client.patch("/user-settings/me", json=update_data)

    assert response.status_code == status.HTTP_200_OK
    updated_settings = response.json()
    assert updated_settings["receive_email_notifications"] is True


def test_unauthenticated_access_forbidden(unauthorized_client: TestClient):
    """Test that unauthenticated users cannot access settings endpoints."""
    get_response = unauthorized_client.get("/user-settings/me")
    assert get_response.status_code == status.HTTP_401_UNAUTHORIZED

    update_response = unauthorized_client.patch(
        "/user-settings/me", json={"receive_email_notifications": True}
    )
    assert update_response.status_code == status.HTTP_401_UNAUTHORIZED
