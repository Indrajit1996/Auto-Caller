import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.user import User, UserStatus
from data_pipeline.seeders.user_seeder import UserFactory


def test_regular_user_cannot_access_users_api(authorized_client: TestClient):
    """Test that a regular user cannot access the users API."""
    response = authorized_client.get("/users/datatable")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "The user doesn't have enough privileges"


@pytest.fixture(scope="function")
def test_user_data():
    """Test user data for creating users."""
    user = UserFactory.build(
        status=UserStatus.ACTIVE,
        is_superuser=False,
    )
    return {
        "email": user.email,
        "password": "testpassword",
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_superuser": user.is_superuser,
    }


def test_read_users_advanced(superuser_client: TestClient):
    """Test getting users with advanced filtering."""
    request_body = {
        "offset": 0,
        "limit": 10,
        "search": "",
        "filters": {
            "status": "all",
            "role": "all",
            "group": "all",
            "exclude_group": None,
        },
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/users/datatable", json=request_body)

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["data"], list)

    # Check user data structure
    if data["data"]:
        user = data["data"][0]
        assert "id" in user
        assert "first_name" in user
        assert "last_name" in user
        assert "email" in user
        assert "status" in user
        assert "is_superuser" in user
        assert "is_active" in user
        assert "created_at" in user


def test_read_users_with_search(superuser_client: TestClient):
    """Test getting users with search filter."""
    request_body = {
        "offset": 0,
        "limit": 10,
        "search": "admin",  # Search for admin user
        "filters": {"status": "all", "role": "all", "group": "all"},
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/users/datatable", json=request_body)

    assert response.status_code == 200
    data = response.json()

    # Verify search works
    if data["count"] > 0:
        found = False
        for user in data["data"]:
            # Check if any user has "admin" in first_name, last_name, or email
            if (
                "admin" in user["first_name"].lower()
                or "admin" in user["last_name"].lower()
                or "admin" in user["email"].lower()
            ):
                found = True
                break
        assert found, "Search didn't return expected results"


def test_read_users_with_status_filter(superuser_client: TestClient):
    """Test getting users with status filter."""
    request_body = {
        "offset": 0,
        "limit": 10,
        "search": "",
        "filters": {"status": "active", "role": "all", "group": "all"},
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/users/datatable", json=request_body)

    assert response.status_code == 200
    data = response.json()

    # Verify all returned users have active status
    if data["data"]:
        for user in data["data"]:
            assert user["status"] == "active"


def test_create_user(superuser_client: TestClient, test_user_data):
    """Test creating a new user."""
    response = superuser_client.post("/users/", json=test_user_data)

    assert response.status_code == 200
    user = response.json()

    assert user["email"] == test_user_data["email"]
    assert user["first_name"] == test_user_data["first_name"]
    assert user["last_name"] == test_user_data["last_name"]
    assert user["is_superuser"] == test_user_data["is_superuser"]
    assert user["status"] == "active"
    assert "id" in user
    assert "created_at" in user


def test_create_duplicate_user(superuser_client: TestClient, test_normal_user: User):
    """Test creating a user with an existing email should fail."""
    user_data = {
        "email": test_normal_user.email,
        "password": "testpassword",
        "first_name": "Duplicate",
        "last_name": "User",
        "is_superuser": False,
    }

    response = superuser_client.post("/users/", json=user_data)

    assert response.status_code == 400
    assert "User with this email already exists" in response.json()["detail"]["message"]


def test_get_user_status_breakdown(superuser_client: TestClient):
    """Test getting user status breakdown."""
    response = superuser_client.get("/users/status-counts")

    assert response.status_code == 200
    data = response.json()

    assert "active" in data
    assert "pending_email_verification" in data
    assert "pending_admin_approval" in data
    assert "deactivated" in data
    assert "total" in data
    assert data["total"] == sum(
        [
            data["active"],
            data["pending_email_verification"],
            data["pending_admin_approval"],
            data["deactivated"],
        ]
    )


def test_export_user_data(superuser_client: TestClient):
    """Test exporting user data."""
    response = superuser_client.get("/users/export")

    # Check if the response is successful and is a CSV file
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"] == 'attachment; filename="users.csv"'

    # Check the content of the CSV file
    content = response.content.decode("utf-8")
    lines = content.strip().split("\n")

    # Check header
    header = lines[0].strip()
    assert "id" in header
    assert "first_name" in header
    assert "last_name" in header
    assert "email" in header
    assert "created_at" in header


def test_read_user_by_id(superuser_client: TestClient, test_normal_user: User):
    """Test getting a specific user by ID."""
    response = superuser_client.get(f"/users/{test_normal_user.id}")

    assert response.status_code == 200
    user = response.json()

    assert user["id"] == str(test_normal_user.id)
    assert "first_name" in user
    assert "last_name" in user
    assert "email" in user
    assert "status" in user
    assert "is_superuser" in user


def test_read_user_nonexistent_id(superuser_client: TestClient):
    """Test getting a user with a non-existent ID."""
    non_existent_id = uuid.uuid4()
    response = superuser_client.get(f"/users/{non_existent_id}")

    assert response.status_code == 404


def test_update_user(superuser_client: TestClient, test_normal_user: User):
    """Test updating a user."""
    user_id = test_normal_user.id
    update_data = {
        "id": str(user_id),
        "first_name": "Updated",
        "last_name": "Name",
        "email": f"updated_{test_normal_user.email}",
    }

    response = superuser_client.patch(f"/users/{user_id}", json=update_data)

    assert response.status_code == 200
    updated_user = response.json()

    assert updated_user["id"] == str(user_id)
    assert updated_user["first_name"] == update_data["first_name"]
    assert updated_user["last_name"] == update_data["last_name"]
    assert updated_user["email"] == update_data["email"]


def test_update_user_nonexistent_id(superuser_client: TestClient):
    """Test updating a non-existent user."""
    non_existent_id = uuid.uuid4()
    update_data = {
        "id": str(non_existent_id),
        "first_name": "Nonexistent",
        "last_name": "User",
        "email": "nonexistent@example.com",
    }

    response = superuser_client.patch(f"/users/{non_existent_id}", json=update_data)

    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_superuser_cannot_update_own_account(
    superuser_client: TestClient, test_superuser: User
):
    """Test that a superuser cannot update their own account."""
    update_data = {
        "id": str(test_superuser.id),
        "first_name": "Self",
        "last_name": "Update",
        "email": test_superuser.email,
    }

    response = superuser_client.patch(f"/users/{test_superuser.id}", json=update_data)

    assert response.status_code == 400
    assert "Superusers cannot update their own account" in response.json()["detail"]


def test_update_user_partial_fields(
    superuser_client: TestClient, test_normal_user: User
):
    """Test updating only some fields of a user."""
    user_id = test_normal_user.id
    # Only update first name
    update_data = {
        "id": str(user_id),
        "first_name": "PartiallyUpdated",
        "last_name": test_normal_user.last_name,  # Unchanged
    }

    response = superuser_client.patch(f"/users/{user_id}", json=update_data)

    assert response.status_code == 200
    updated_user = response.json()

    assert updated_user["id"] == str(user_id)
    assert updated_user["first_name"] == update_data["first_name"]
    assert updated_user["last_name"] == test_normal_user.last_name  # Unchanged
    assert updated_user["email"] == test_normal_user.email  # Unchanged


def test_update_user_with_existing_email(
    superuser_client: TestClient, test_normal_user: User, test_superuser: User
):
    """Test updating a user with an existing email should fail."""
    update_data = {
        "id": str(test_normal_user.id),
        "first_name": "Updated",
        "last_name": "Name",
        "email": test_superuser.email,  # Use superuser's email
    }

    response = superuser_client.patch(f"/users/{test_normal_user.id}", json=update_data)

    assert response.status_code == 409
    assert "User with this email already exists" in response.json()["detail"]


def test_update_user_status(superuser_client: TestClient, test_normal_user: User):
    """Test updating a user's status."""
    status_update = {"status": "deactivated"}

    response = superuser_client.patch(
        f"/users/{test_normal_user.id}/status", json=status_update
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "deactivated"

    # revert the status back to active
    revert_status = {"status": "active"}
    response = superuser_client.patch(
        f"/users/{test_normal_user.id}/status", json=revert_status
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


def test_update_own_status_forbidden(
    superuser_client: TestClient, test_superuser: User
):
    """Test that a superuser cannot update their own status."""
    status_update = {"status": "deactivated"}

    response = superuser_client.patch(
        f"/users/{test_superuser.id}/status", json=status_update
    )

    assert response.status_code == 403
    assert "Cannot change your own status" in response.json()["detail"]


def test_update_invalid_status(superuser_client: TestClient, test_normal_user: User):
    """Test updating a user with an invalid status."""
    # Try to set to a status that's not allowed in the status update endpoint
    status_update = {"status": "pending_email_verification"}

    response = superuser_client.patch(
        f"/users/{test_normal_user.id}/status", json=status_update
    )

    # Should get validation error
    assert response.status_code == 422
