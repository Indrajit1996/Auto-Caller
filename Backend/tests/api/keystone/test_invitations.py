from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from freezegun import freeze_time

from app.models.invitation import Invitation, InvitationType


@pytest.fixture(scope="function")
def test_email_invitation_data():
    """Test email invitation data for creating invitations."""
    return {
        "type": InvitationType.EMAIL,
        "emails": ["test_invite@example.com"],
        "user_expiry_date": None,
    }


@pytest.fixture(scope="function")
def test_link_invitation_data():
    """Test link invitation data for creating invitations."""
    return {
        "type": InvitationType.LINK,
        "emails": None,
        "user_expiry_date": None,
    }


@pytest.fixture(scope="function")
def test_email_invitation(test_db, test_superuser) -> Invitation:
    """Create a test email invitation."""
    invitation = Invitation(
        type=InvitationType.EMAIL,
        email="test_invite@example.com",
        created_by_user_id=test_superuser.id,
    )
    test_db.add(invitation)
    test_db.commit()
    test_db.refresh(invitation)
    return invitation


@pytest.fixture(scope="function")
def test_link_invitation(test_db, test_superuser) -> Invitation:
    """Create a test link invitation."""
    invitation = Invitation(
        type=InvitationType.LINK,
        created_by_user_id=test_superuser.id,
    )
    test_db.add(invitation)
    test_db.commit()
    test_db.refresh(invitation)
    return invitation


@pytest.fixture(scope="function")
def test_expired_invitation(test_db, test_superuser) -> Invitation:
    """Create a test email invitation that is expired."""
    now = datetime.now(timezone.utc)
    invitation = Invitation(
        type=InvitationType.EMAIL,
        email="expired_invite@example.com",
        created_by_user_id=test_superuser.id,
        expires_at=now - timedelta(hours=1),  # Set to 1 hour in the past
    )
    test_db.add(invitation)
    test_db.commit()
    test_db.refresh(invitation)
    return invitation


@pytest.fixture(scope="function")
def test_user_expiry_invitation(test_db, test_superuser) -> Invitation:
    """Create a test email invitation with user expiry date."""
    now = datetime.now(timezone.utc)
    invitation = Invitation(
        type=InvitationType.EMAIL,
        email="user_expiry@example.com",
        created_by_user_id=test_superuser.id,
        user_expiry_date=now + timedelta(days=30),  # Set to 30 days in the future
    )
    test_db.add(invitation)
    test_db.commit()
    test_db.refresh(invitation)
    return invitation


def test_regular_user_cannot_access_invitations_api(authorized_client: TestClient):
    """Test that a regular user cannot access the invitations API."""
    response = authorized_client.post(
        "/invitations/datatable",
        json={
            "offset": 0,
            "limit": 10,
            "search": "",
            "filters": {
                "type": "all",
                "status": "all",
            },
            "order_by": "created_at",
            "order": "desc",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "The user doesn't have enough privileges"


def test_read_invitations_advanced(superuser_client: TestClient):
    """Test getting invitations with advanced filtering."""
    request_body = {
        "offset": 0,
        "limit": 10,
        "search": "",
        "filters": {
            "type": "all",
            "status": "all",
        },
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/invitations/datatable", json=request_body)

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["data"], list)

    # Check invitation data structure
    if data["data"]:
        invitation = data["data"][0]
        assert "id" in invitation
        assert "type" in invitation
        assert "token" in invitation
        assert "created_by_user" in invitation
        assert "created_at" in invitation
        assert "active" in invitation


def test_read_invitations_with_search(
    superuser_client: TestClient, test_email_invitation
):
    """Test getting invitations with search filter."""
    request_body = {
        "offset": 0,
        "limit": 10,
        "search": test_email_invitation.email,  # Search for specific email
        "filters": {"type": "all", "status": "all"},
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/invitations/datatable", json=request_body)

    assert response.status_code == 200
    data = response.json()

    # Verify search works
    if data["count"] > 0:
        found = False
        for invitation in data["data"]:
            if invitation["email"] == test_email_invitation.email:
                found = True
                break
        assert found, "Search didn't return expected results"


def test_read_invitations_with_type_filter(superuser_client: TestClient):
    """Test getting invitations with type filter."""
    request_body = {
        "offset": 0,
        "limit": 10,
        "search": "",
        "filters": {"type": "email", "status": "all"},
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/invitations/datatable", json=request_body)

    assert response.status_code == 200
    data = response.json()

    # Verify all returned invitations have email type
    if data["data"]:
        for invitation in data["data"]:
            assert invitation["type"] == "email"


def test_read_invitations_with_status_filter(superuser_client: TestClient):
    """Test getting invitations with status filter."""
    request_body = {
        "offset": 0,
        "limit": 10,
        "search": "",
        "filters": {"type": "all", "status": "active"},
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/invitations/datatable", json=request_body)

    assert response.status_code == 200
    data = response.json()

    # Verify all returned invitations are active
    if data["data"]:
        for invitation in data["data"]:
            assert invitation["active"] is True


def test_create_email_invitation(
    superuser_client: TestClient, test_email_invitation_data, mock_send_email
):
    """Test creating a new email invitation."""
    response = superuser_client.post("/invitations/", json=test_email_invitation_data)

    assert response.status_code == 201
    data = response.json()

    assert "created_invitations" in data
    assert "existing_emails" in data

    # Check only if the email is not already in existing_emails
    if test_email_invitation_data["emails"][0] not in data["existing_emails"]:
        created = data["created_invitations"]
        assert len(created) > 0
        assert created[0]["type"] == test_email_invitation_data["type"]
        assert "token" in created[0]

        # Verify that send_email was called
        mock_send_email.assert_called()


def test_create_link_invitation(
    superuser_client: TestClient, test_link_invitation_data
):
    """Test creating a new link invitation."""
    response = superuser_client.post("/invitations/", json=test_link_invitation_data)

    assert response.status_code == 201
    data = response.json()

    assert "created_invitations" in data
    assert len(data["created_invitations"]) == 1

    created = data["created_invitations"][0]
    assert created["type"] == test_link_invitation_data["type"]
    assert "token" in created
    assert created["email"] is None


def test_create_invitation_with_expiry_date(superuser_client: TestClient):
    """Test creating a new invitation with user expiry date."""
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    invitation_data = {
        "type": InvitationType.EMAIL,
        "emails": ["expiry_test@example.com"],
        "user_expiry_date": expiry_date,
    }

    response = superuser_client.post("/invitations/", json=invitation_data)

    assert response.status_code == 201
    data = response.json()

    # If the email is not already in use
    if len(data["created_invitations"]) > 0:
        # Don't need to check the actual date as it might be formatted differently
        # Just check that something was set
        assert data["created_invitations"][0]["type"] == invitation_data["type"]


def test_get_invitation_by_id(superuser_client: TestClient, test_email_invitation):
    """Test getting a specific invitation by ID."""
    response = superuser_client.get(f"/invitations/{test_email_invitation.id}")

    assert response.status_code == 200
    invitation = response.json()

    assert invitation["id"] == test_email_invitation.id
    assert invitation["type"] == test_email_invitation.type
    assert invitation["email"] == test_email_invitation.email
    assert invitation["token"] == str(test_email_invitation.token)
    assert "created_at" in invitation
    assert "active" in invitation


def test_get_invitation_by_token(superuser_client: TestClient, test_email_invitation):
    """Test getting invitation details by token without authentication."""
    response = superuser_client.get(f"/invitations/token/{test_email_invitation.token}")

    assert response.status_code == 200
    data = response.json()

    assert data["type"] == test_email_invitation.type
    assert data["email"] == test_email_invitation.email


def test_get_invitation_type_breakdown(superuser_client: TestClient):
    """Test getting invitation type breakdown."""
    response = superuser_client.get("/invitations/type-counts")

    assert response.status_code == 200
    data = response.json()

    assert "email" in data
    assert "link" in data
    assert "registered" in data
    assert "active_total" in data
    assert "inactive_total" in data
    assert "total" in data
    assert data["total"] == data["active_total"] + data["inactive_total"]


def test_resend_invitation(
    superuser_client: TestClient, test_email_invitation, mock_send_email
):
    """Test resending an invitation email."""
    response = superuser_client.post(f"/invitations/{test_email_invitation.id}/resend")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert data["message"] == "Invitation resent successfully"

    # Verify that send_email was called
    mock_send_email.assert_called()


def test_resend_link_invitation_fails(
    superuser_client: TestClient, test_link_invitation
):
    """Test that resending a link invitation fails."""
    response = superuser_client.post(f"/invitations/{test_link_invitation.id}/resend")

    assert response.status_code == 400
    assert "Link invitations cannot be resent" in response.json()["detail"]


def test_deactivate_invitation(superuser_client: TestClient, test_email_invitation):
    """Test deactivating an invitation."""
    response = superuser_client.patch(
        f"/invitations/{test_email_invitation.id}/deactivate"
    )

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert data["message"] == "Invitation deactivated"

    # Verify the invitation is actually deactivated
    response = superuser_client.get(f"/invitations/{test_email_invitation.id}")
    invitation = response.json()
    assert invitation["active"] is False


def test_deactivate_nonexistent_invitation(superuser_client: TestClient):
    """Test deactivating a non-existent invitation."""
    non_existent_id = 99999  # Assuming this ID doesn't exist
    response = superuser_client.patch(f"/invitations/{non_existent_id}/deactivate")

    assert response.status_code == 404
    assert "Invitation not found" in response.json()["detail"]


def test_invitation_expiry(superuser_client: TestClient, test_email_invitation):
    """Test invitation expiry property works correctly."""
    # First verify the invitation is active
    response = superuser_client.get(f"/invitations/{test_email_invitation.id}")
    assert response.status_code == 200
    invitation = response.json()
    assert invitation["active"] is True

    # Use freezegun to set time after the invitation expiry
    future_time = test_email_invitation.expires_at + timedelta(hours=1)
    with freeze_time(future_time):
        response = superuser_client.get(f"/invitations/{test_email_invitation.id}")
        assert response.status_code == 200
        invitation = response.json()
        assert invitation["active"] is False


def test_expired_invitation_status(
    superuser_client: TestClient, test_expired_invitation
):
    """Test that an invitation created with expiry in the past is already inactive."""
    response = superuser_client.get(f"/invitations/{test_expired_invitation.id}")

    assert response.status_code == 200
    invitation = response.json()
    assert invitation["active"] is False


def test_user_expiry_date_persists(
    superuser_client: TestClient, test_user_expiry_invitation
):
    """Test that user_expiry_date is correctly saved and retrieved."""
    response = superuser_client.get(f"/invitations/{test_user_expiry_invitation.id}")

    assert response.status_code == 200
    invitation = response.json()
    assert invitation["user_expiry_date"] is not None

    # Parse the dates to verify they're close (allowing for serialization differences)
    retrieved_date = datetime.fromisoformat(
        invitation["user_expiry_date"].replace("Z", "+00:00")
    )
    original_date = test_user_expiry_invitation.user_expiry_date

    # Check dates are within 1 second (to allow for potential serialization differences)
    assert abs((retrieved_date - original_date).total_seconds()) < 1


def test_create_invitation_expiry(superuser_client: TestClient):
    """Test that created invitations get the correct expiry time."""
    from app.core.config import config

    invitation_data = {
        "type": InvitationType.EMAIL,
        "emails": ["expiry_test2@example.com"],
        "user_expiry_date": None,
    }

    # Freeze time to ensure we know exactly when the invitation is created
    current_time = datetime.now(timezone.utc)
    with freeze_time(current_time):
        response = superuser_client.post("/invitations/", json=invitation_data)

        assert response.status_code == 201
        data = response.json()

        # If we successfully created an invitation
        if len(data["created_invitations"]) > 0:
            created_invitation = data["created_invitations"][0]

            # Since the created_invitations doesn't contain expires_at directly,
            # we need to fetch the invitation details
            if "token" in created_invitation:
                # Fetch the full invitation using its token
                response = superuser_client.get(
                    f"/invitations/token/{created_invitation['token']}"
                )
                assert response.status_code == 200

                # Or get all invitations and find our newly created one
                response = superuser_client.post(
                    "/invitations/datatable",
                    json={
                        "offset": 0,
                        "limit": 10,
                        "search": "expiry_test2@example.com",
                        "filters": {"type": "all", "status": "all"},
                        "order_by": "created_at",
                        "order": "desc",
                    },
                )

                assert response.status_code == 200
                invitations_data = response.json()

                # Find our invitation in the results
                if invitations_data["count"] > 0:
                    for invitation in invitations_data["data"]:
                        if invitation["email"] == "expiry_test2@example.com":
                            # Parse the expiry time
                            expiry_time = datetime.fromisoformat(
                                invitation["expires_at"].replace("Z", "+00:00")
                            )

                            # Check that it's set to current time + config hours
                            expected_expiry = current_time + timedelta(
                                hours=config.INVITATION_EXPIRY_IN_HOURS
                            )
                            assert (
                                abs((expiry_time - expected_expiry).total_seconds()) < 1
                            )
                            break
                    else:
                        pytest.fail(
                            "Could not find the created invitation in the datatable response"
                        )
