from datetime import datetime, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.invitation import Invitation, InvitationRegistration, InvitationType


@pytest.fixture(scope="function")
def create_test_invitations(test_db, test_superuser, test_normal_user):
    """Create various test invitations for filtering tests."""
    # Create an active email invitation
    active_email = Invitation(
        type=InvitationType.EMAIL,
        email="active_email@example.com",
        created_by_user_id=test_superuser.id,
        expires_at=datetime.now() + timedelta(days=7),
    )

    # Create an expired email invitation
    expired_email = Invitation(
        type=InvitationType.EMAIL,
        email="expired_email@example.com",
        created_by_user_id=test_superuser.id,
        expires_at=datetime.now() - timedelta(days=1),
    )

    # Create a link invitation
    link_invite = Invitation(
        type=InvitationType.LINK,
        created_by_user_id=test_superuser.id,
        expires_at=datetime.now() + timedelta(days=7),
    )

    # Create a registered invitation
    registered_invite = Invitation(
        type=InvitationType.EMAIL,
        email="registered@example.com",
        created_by_user_id=test_superuser.id,
        expires_at=datetime.now() + timedelta(days=7),
    )

    test_db.add_all([active_email, expired_email, link_invite, registered_invite])
    test_db.commit()

    # Create a registration for the registered invitation
    registration = InvitationRegistration(
        invitation_id=registered_invite.id, user_id=test_normal_user.id
    )
    test_db.add(registration)
    test_db.commit()

    return {
        "active_email": active_email,
        "expired_email": expired_email,
        "link_invite": link_invite,
        "registered_invite": registered_invite,
    }


def test_invitation_status_filters(
    superuser_client: TestClient, create_test_invitations
):
    """Test invitation filtering by status to ensure correct filtering behavior."""

    # Test active filter
    active_request = {
        "offset": 0,
        "limit": 10,
        "search": "",
        "filters": {
            "type": "all",
            "status": "active",
        },
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/invitations/datatable", json=active_request)
    assert response.status_code == status.HTTP_200_OK
    active_data = response.json()

    # Check that only active invitations are returned
    if active_data["data"]:
        for invitation in active_data["data"]:
            assert invitation["active"] is True

    # Test inactive filter
    inactive_request = {
        "offset": 0,
        "limit": 10,
        "search": "",
        "filters": {
            "type": "all",
            "status": "inactive",
        },
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/invitations/datatable", json=inactive_request)
    assert response.status_code == status.HTTP_200_OK
    inactive_data = response.json()

    # Check that only inactive invitations are returned
    if inactive_data["data"]:
        for invitation in inactive_data["data"]:
            assert invitation["active"] is False

    # Test registered filter
    registered_request = {
        "offset": 0,
        "limit": 10,
        "search": "",
        "filters": {
            "type": "all",
            "status": "registered",
        },
        "order_by": "created_at",
        "order": "desc",
    }

    response = superuser_client.post("/invitations/datatable", json=registered_request)
    assert response.status_code == status.HTTP_200_OK
    registered_data = response.json()

    # Check that invitations with registered users are returned
    if registered_data["data"]:
        registered_ids = [invite["id"] for invite in registered_data["data"]]
        assert create_test_invitations["registered_invite"].id in registered_ids
