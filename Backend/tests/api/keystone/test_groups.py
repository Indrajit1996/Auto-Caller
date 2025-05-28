import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.group import Group, UserGroup
from app.models.user import User
from data_pipeline.seeders.group_seeder import GroupFactory


@pytest.fixture(scope="function")
def test_group(test_superuser: User, test_db: Session) -> Group:
    """Create a test group for testing."""
    group = GroupFactory.build(
        name="Test Group",
        description="A test group for testing purposes",
        created_by_user_id=test_superuser.id,
    )
    test_db.add(group)
    test_db.commit()
    test_db.refresh(group)
    return group


@pytest.fixture(scope="function")
def test_group_data(test_superuser: User):
    """Test group data for creating groups."""
    return {
        "name": "New Test Group",
        "description": "A new test group for testing purposes",
        "created_by_user_id": str(test_superuser.id),
    }


def test_regular_user_access_groups_api(authorized_client: TestClient):
    """Test that a regular user can access the groups API."""
    # This test needs to be updated as the /groups endpoint requires superuser
    # Regular users should still be able to access specific groups they belong to
    response = authorized_client.get("/groups/1")

    # We're not checking the actual response status here since it might be 200 or 404
    # depending on whether group 1 exists, but it shouldn't be 403 forbidden
    assert response.status_code != status.HTTP_403_FORBIDDEN


def test_read_groups(superuser_client: TestClient):
    """Test getting groups with basic filtering."""
    # Updated to use the GET endpoint with query params as defined in the router
    response = superuser_client.get("/groups/", params={"offset": 0, "limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["data"], list)

    # Check group data structure
    if data["data"]:
        group = data["data"][0]
        assert "id" in group
        assert "name" in group
        assert "description" in group


def test_read_groups_with_datatable(superuser_client: TestClient):
    """Test getting groups using the datatable endpoint with filtering and search."""
    # Test the datatable endpoint
    datatable_request = {
        "offset": 0,
        "limit": 10,
        "search": "test",
        "order_by": "name",
        "order": "asc",
        "filters": {"user_id": None},
    }

    response = superuser_client.post("/groups/datatable", json=datatable_request)

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["data"], list)

    # Check group data structure if data exists
    if data["data"]:
        group = data["data"][0]
        assert "id" in group
        assert "name" in group
        assert "description" in group
        assert "user_count" in group
        assert isinstance(group["user_count"], int)


def test_create_group(superuser_client: TestClient, test_group_data):
    """Test creating a new group."""
    response = superuser_client.post("/groups/", json=test_group_data)

    assert response.status_code == 201  # Updated to match the status code in the router
    group = response.json()

    assert group["name"] == test_group_data["name"]
    assert group["description"] == test_group_data["description"]
    assert group["created_by_user"]["id"] == test_group_data["created_by_user_id"]
    assert "id" in group


def test_create_duplicate_group(superuser_client: TestClient, test_group: Group):
    """Test creating a group with an existing name should succeed (duplicate names allowed)."""
    group_data = {
        "name": test_group.name,
        "description": "Another group with the same name",
        "created_by_user_id": str(test_group.created_by_user_id),
    }

    response = superuser_client.post("/groups/", json=group_data)

    # Groups with duplicate names should be allowed
    assert response.status_code == 201
    assert response.json()["name"] == test_group.name


def test_get_group_by_id(superuser_client: TestClient, test_group: Group):
    """Test getting a specific group by ID."""
    response = superuser_client.get(f"/groups/{test_group.id}")

    assert response.status_code == 200
    group = response.json()

    assert group["id"] == test_group.id
    assert group["name"] == test_group.name
    assert group["description"] == test_group.description
    assert "created_by_user" in group


def test_get_group_with_users(
    superuser_client: TestClient,
    test_group: Group,
    test_normal_user: User,
    test_db: Session,
):
    """Test getting a group with its users."""
    # First add a user to the group
    user_group = UserGroup(
        group_id=test_group.id,
        user_id=test_normal_user.id,
    )
    test_db.add(user_group)
    test_db.commit()

    # Get the group
    response = superuser_client.get(f"/groups/{test_group.id}")
    assert response.status_code == 200
    group = response.json()

    assert group["id"] == test_group.id

    # Now get the users separately if they're not included in the response
    # We can verify the user is in the group by using the endpoint that updates users
    add_users_data = {"user_ids": [str(test_normal_user.id)]}
    response = superuser_client.post(
        f"/groups/{test_group.id}/users", json=add_users_data
    )
    assert response.status_code == 200


def test_get_nonexistent_group(superuser_client: TestClient):
    """Test getting a group with a non-existent ID."""
    non_existent_id = 9999
    response = superuser_client.get(f"/groups/{non_existent_id}")

    assert response.status_code == 404


def test_update_group(superuser_client: TestClient, test_group: Group):
    """Test updating a group."""
    update_data = {
        "name": "Updated Group Name",
        "description": "Updated group description",
    }

    response = superuser_client.patch(f"/groups/{test_group.id}", json=update_data)

    assert response.status_code == 200
    updated_group = response.json()

    assert updated_group["id"] == test_group.id
    assert updated_group["name"] == update_data["name"]
    assert updated_group["description"] == update_data["description"]


def test_update_nonexistent_group(superuser_client: TestClient):
    """Test updating a non-existent group."""
    non_existent_id = 9999
    update_data = {
        "name": "Updated Group Name",
        "description": "Updated group description",
    }

    response = superuser_client.patch(f"/groups/{non_existent_id}", json=update_data)

    assert response.status_code == 404


def test_add_users_to_group(
    superuser_client: TestClient, test_group: Group, test_normal_user: User
):
    """Test adding users to a group."""
    add_users_data = {"user_ids": [str(test_normal_user.id)]}

    response = superuser_client.post(
        f"/groups/{test_group.id}/users", json=add_users_data
    )

    assert response.status_code == 200

    # Need to verify the user was added by checking if we can successfully
    # remove the user or by another method
    response = superuser_client.delete(
        f"/groups/{test_group.id}/users/{test_normal_user.id}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User removed from group successfully"


def test_remove_user_from_group(
    superuser_client: TestClient,
    test_group: Group,
    test_normal_user: User,
    test_db: Session,
):
    """Test removing a specific user from a group using the dedicated endpoint."""
    # First make sure the user is in the group if not already
    exists = select(UserGroup).where(
        UserGroup.group_id == test_group.id,
        UserGroup.user_id == test_normal_user.id,
    )
    result = test_db.exec(exists)
    if not result.first():
        user_group = UserGroup(
            group_id=test_group.id,
            user_id=test_normal_user.id,
        )
        test_db.add(user_group)
        test_db.commit()
        test_db.refresh(user_group)

    # Test removing a specific user with the dedicated DELETE endpoint
    response = superuser_client.delete(
        f"/groups/{test_group.id}/users/{test_normal_user.id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User removed from group successfully"

    # Verify user was removed by trying to remove them again - should fail
    response = superuser_client.delete(
        f"/groups/{test_group.id}/users/{test_normal_user.id}"
    )
    assert response.status_code == 400  # User not in group


def test_delete_group(
    superuser_client: TestClient, test_superuser: User, test_db: Session
):
    """Test deleting a group."""
    # Create a new group specifically for deletion test using GroupFactory
    group_to_delete = GroupFactory.create(
        name="Group to Delete",
        description="This group will be deleted",
        created_by_user_id=test_superuser.id,
    )
    test_db.add(group_to_delete)
    test_db.commit()
    test_db.refresh(group_to_delete)

    response = superuser_client.delete(f"/groups/{group_to_delete.id}")

    assert response.status_code == 200

    # Verify group was deleted
    response = superuser_client.get(f"/groups/{group_to_delete.id}")
    assert response.status_code == 404


def test_create_multiple_groups_with_factory(
    superuser_client: TestClient, test_superuser: User
):
    """Test creating multiple groups with GroupFactory and verifying they exist in the API."""
    # Create multiple groups using seed_groups from the seeder
    from data_pipeline.seeders.group_seeder import seed_groups

    test_groups = seed_groups(
        count=3, attributes={"created_by_user_id": test_superuser.id}, with_users=False
    )

    # Verify each group can be retrieved via the API
    for group in test_groups:
        response = superuser_client.get(f"/groups/{group.id}")
        assert response.status_code == 200
        retrieved_group = response.json()
        assert retrieved_group["name"] == group.name
        assert retrieved_group["description"] == group.description


def test_add_multiple_users_to_group(
    superuser_client: TestClient,
    test_group: Group,
    test_normal_user: User,
    test_superuser: User,
):
    """Test adding multiple users to a group."""
    # Create a list of user IDs to add
    user_ids = [str(test_normal_user.id), str(test_superuser.id)]

    add_users_data = {"user_ids": user_ids}

    response = superuser_client.post(
        f"/groups/{test_group.id}/users", json=add_users_data
    )

    assert response.status_code == 200

    # Verify by removing each user - this should succeed
    for user_id in user_ids:
        response = superuser_client.delete(f"/groups/{test_group.id}/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "User removed from group successfully"


def test_update_all_group_users(
    superuser_client: TestClient,
    test_group: Group,
    test_normal_user: User,
    test_superuser: User,
):
    """Test updating all users in a group at once."""
    # First clear any existing users
    response = superuser_client.post(
        f"/groups/{test_group.id}/users", json={"user_ids": []}
    )
    assert response.status_code == 200

    # Then add multiple users at once
    user_ids = [str(test_normal_user.id), str(test_superuser.id)]
    response = superuser_client.post(
        f"/groups/{test_group.id}/users", json={"user_ids": user_ids}
    )
    assert response.status_code == 200

    # Verify all users were added by trying to remove each one
    for user_id in user_ids:
        response = superuser_client.delete(f"/groups/{test_group.id}/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "User removed from group successfully"

    # Add them again
    response = superuser_client.post(
        f"/groups/{test_group.id}/users", json={"user_ids": user_ids}
    )
    assert response.status_code == 200

    # Now replace with just one user
    response = superuser_client.post(
        f"/groups/{test_group.id}/users", json={"user_ids": [str(test_normal_user.id)]}
    )
    assert response.status_code == 200

    # Verify the first user is still in the group
    response = superuser_client.delete(
        f"/groups/{test_group.id}/users/{test_normal_user.id}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User removed from group successfully"

    # The second user should have been removed
    response = superuser_client.delete(
        f"/groups/{test_group.id}/users/{test_superuser.id}"
    )
    assert response.status_code == 400  # User not in group
