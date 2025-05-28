from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.notification import Notification
from app.models.user import User
from data_pipeline.seeders.notification_seeder import (
    NotificationFactory,
)


@pytest.fixture(scope="module")
def test_notifications(
    session_db: Session, module_normal_user: User
) -> Generator[list[Notification], None, None]:
    """Create test notifications for a user and clean up after the test."""
    notifications = [
        NotificationFactory.build(user_id=module_normal_user.id, is_read=False)
        for _ in range(3)
    ]
    session_db.add_all(notifications)
    session_db.commit()

    for notification in notifications:
        session_db.refresh(notification)

    yield notifications


def test_get_notifications(
    module_authorized_client: TestClient, test_notifications: list[Notification]
):
    """Test getting all notifications for a user."""
    response = module_authorized_client.get("/notifications/")

    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] == 3
    assert len(data["data"]) == 3

    notifications = data["data"]
    for notification in notifications:
        assert "id" in notification
        assert "message" in notification
        assert "type" in notification
        assert "channel" in notification
        assert "is_read" in notification
        assert "user_id" in notification
        assert "meta_data" in notification


def test_get_single_notification(
    module_authorized_client: TestClient, test_notifications: list[Notification]
):
    """Test getting a single notification."""
    notification_id = test_notifications[0].id
    response = module_authorized_client.get(f"/notifications/{notification_id}")

    assert response.status_code == 200

    notification = response.json()
    assert notification["id"] == notification_id
    assert "message" in notification
    assert "type" in notification
    assert "channel" in notification
    assert "is_read" in notification
    assert "user_id" in notification
    assert "meta_data" in notification


def test_get_nonexistent_notification(module_authorized_client: TestClient):
    """Test getting a notification that doesn't exist."""
    response = module_authorized_client.get("/notifications/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"


def test_notifications_pagination(module_authorized_client: TestClient):
    """Test pagination for notifications endpoint."""
    # Test with limit
    response = module_authorized_client.get("/notifications/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3  # Total count should still be 3
    assert len(data["data"]) == 2  # But only 2 returned due to limit

    # Test with offset
    response = module_authorized_client.get("/notifications/?offset=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert len(data["data"]) == 1  # Only 1 left after offset of 2


def test_mark_notification_as_read(
    module_authorized_client: TestClient, test_notifications: list[Notification]
):
    """Test marking a notification as read."""
    notification_id = test_notifications[0].id
    assert not test_notifications[0].is_read

    response = module_authorized_client.patch(f"/notifications/{notification_id}/read")

    assert response.status_code == 200

    notification = response.json()
    assert notification["id"] == notification_id
    assert notification["is_read"] is True

    # Verify that the notification stays marked as read when retrieved again
    response = module_authorized_client.get(f"/notifications/{notification_id}")
    assert response.status_code == 200
    notification = response.json()
    assert notification["is_read"] is True


def test_mark_nonexistent_notification_as_read(module_authorized_client: TestClient):
    """Test marking a nonexistent notification as read."""
    response = module_authorized_client.patch("/notifications/9999/read")
    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"


@pytest.fixture(scope="function")
def other_user_notification(test_db: Session, test_normal_user: User) -> Notification:
    """Create a notification for a different user."""
    notification = NotificationFactory.create(user_id=test_normal_user.id)
    test_db.add(notification)
    test_db.commit()
    test_db.refresh(notification)
    return notification


def test_get_other_users_notification(
    module_authorized_client: TestClient, other_user_notification: Notification
):
    """Test trying to access another user's notification."""
    response = module_authorized_client.get(
        f"/notifications/{other_user_notification.id}"
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


def test_mark_other_users_notification_as_read(
    module_authorized_client: TestClient, other_user_notification: Notification
):
    """Test trying to mark another user's notification as read."""
    response = module_authorized_client.patch(
        f"/notifications/{other_user_notification.id}/read"
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


def test_mark_all_notifications_as_read(
    module_authorized_client: TestClient,
):
    """Test marking all notifications as read."""
    # First, get the current count of unread notifications via API
    initial_response = module_authorized_client.get("/notifications/")
    assert initial_response.status_code == 200
    initial_data = initial_response.json()
    unread_count = initial_data["count"]

    # Ensure we have unread notifications to test with
    assert unread_count > 0, "Test requires unread notifications"

    # Call the read-all endpoint
    response = module_authorized_client.patch("/notifications/read-all")

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["count"] == unread_count

    # Verify that all notifications are now marked as read through API
    get_response = module_authorized_client.get("/notifications/")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["count"] == 0
    assert len(data["data"]) == 0
