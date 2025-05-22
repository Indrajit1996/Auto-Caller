import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models.invitation import Invitation, InvitationRegistration, InvitationType
from app.models.user import User, UserStatus
from data_pipeline.seeders.user_seeder import UserFactory


@pytest.fixture(scope="function")
def test_register_data():
    """Test data for user registration."""
    user = UserFactory.create()
    return {
        "email": user.email,
        "password": "password",
        "first_name": user.first_name,
        "last_name": user.last_name,
        "invitation_token": None,
    }


@pytest.fixture(scope="function")
def test_password_reset_data():
    """Test data for password reset."""
    return {
        "token": str(uuid.uuid4()),
        "new_password": "newpassword123",
    }


@pytest.fixture(scope="function")
def pending_verification_user(test_db: Session):
    """Create a user with pending email verification using UserFactory."""
    user = UserFactory.build(
        status=UserStatus.PENDING_EMAIL_VERIFICATION,
        hashed_password=get_password_hash("password"),
        email_verification_token=uuid.uuid4(),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def deactivated_user(test_db: Session):
    """Create a deactivated user using UserFactory."""
    user = UserFactory.build(
        status=UserStatus.DEACTIVATED,
        hashed_password=get_password_hash("password"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_invitation(test_db: Session, test_superuser: User):
    """Create a test invitation."""
    invitation = Invitation(
        email="invited@example.com",
        token=uuid.uuid4(),
        expires_at=datetime.now() + timedelta(days=7),
        type=InvitationType.EMAIL,
        created_by_user_id=test_superuser.id,
    )
    test_db.add(invitation)
    test_db.commit()
    test_db.refresh(invitation)
    return invitation


@pytest.fixture(scope="function")
def inactive_test_invitation(test_db: Session, test_superuser: User):
    """Create an inactive test invitation."""
    invitation = Invitation(
        email="inactive-invite@example.com",
        token=uuid.uuid4(),
        expires_at=datetime.now() - timedelta(days=1),  # Already expired
        type=InvitationType.EMAIL,
        created_by_user_id=test_superuser.id,
    )
    test_db.add(invitation)
    test_db.commit()
    test_db.refresh(invitation)
    return invitation


# Module-level test functions instead of class-based tests
def test_login_success(unauthorized_client: TestClient, test_normal_user: User):
    """Test successful login with valid credentials."""
    response = unauthorized_client.post(
        "/login/access-token",
        data={
            "username": test_normal_user.email,
            "password": "password",  # This is the password set in the fixture
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["access_token"]


def test_login_invalid_credentials(unauthorized_client: TestClient):
    """Test login with invalid credentials."""
    response = unauthorized_client.post(
        "/login/access-token",
        data={
            "username": "OKnonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "status" in data["detail"]
    assert data["detail"]["status"] == "INVALID_CREDENTIALS"


def test_login_inactive_user(unauthorized_client: TestClient, deactivated_user: User):
    """Test login attempt with deactivated user."""
    response = unauthorized_client.post(
        "/login/access-token",
        data={
            "username": deactivated_user.email,
            "password": "password",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "status" in data["detail"]
    assert data["detail"]["status"] == "DEACTIVATED"


def test_login_pending_verification(
    unauthorized_client: TestClient, pending_verification_user: User
):
    """Test login attempt with pending verification user."""

    response = unauthorized_client.post(
        "/login/access-token",
        data={
            "username": pending_verification_user.email,
            "password": "password",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_case_insensitive_email(
    unauthorized_client: TestClient, test_normal_user: User
):
    """Test that login works with different case versions of the same email."""
    # Get the original email and convert to uppercase
    uppercase_email = test_normal_user.email.upper()

    # Try logging in with uppercase email
    response = unauthorized_client.post(
        "/login/access-token",
        data={
            "username": uppercase_email,
            "password": "password",  # This is the password set in the fixture
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["access_token"]


def test_test_token(authorized_client: TestClient, test_normal_user: User):
    """Test token validation endpoint."""
    response = authorized_client.post("/login/test-token")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_normal_user.email
    assert data["id"] == str(test_normal_user.id)


def test_test_token_unauthorized(unauthorized_client: TestClient):
    """Test token validation without token."""
    response = unauthorized_client.post("/login/test-token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_user_success(
    mock_send_email,
    unauthorized_client: TestClient,
    test_register_data,
    test_db: Session,
):
    """Test successful user registration."""
    response = unauthorized_client.post("/register", json=test_register_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data

    # Verify user was created in DB
    user = select(User).where(User.email == test_register_data["email"])
    user = test_db.exec(user).first()

    assert user is not None
    assert user.email == test_register_data["email"]
    assert user.first_name == test_register_data["first_name"]
    assert user.last_name == test_register_data["last_name"]
    assert verify_password(test_register_data["password"], user.hashed_password)

    mock_send_email.assert_called_once()


def test_register_existing_user(unauthorized_client: TestClient, test_db: Session):
    """Test registration with existing email."""
    # Create user with UserFactory instead of relying on fixture
    existing_user = UserFactory.create(
        email="existing@example.com",
        password="password",
        status=UserStatus.ACTIVE,
    )
    test_db.add(existing_user)
    test_db.commit()
    test_db.refresh(existing_user)

    response = unauthorized_client.post(
        "/register",
        json={
            "email": existing_user.email,  # Using existing email
            "password": "password",
            "first_name": "Another",
            "last_name": "User",
            "invitation_token": None,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "message" in data["detail"]


def test_register_with_uppercase_email(
    mock_send_email,
    unauthorized_client: TestClient,
    test_db: Session,
):
    """Test that registration stores email in lowercase regardless of input case."""
    # Create registration data with uppercase email
    original_email = "MixedCase.User@Example.COM"
    lowercase_email = original_email.lower()

    register_data = {
        "email": original_email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "invitation_token": None,
    }

    response = unauthorized_client.post("/register", json=register_data)
    assert response.status_code == status.HTTP_200_OK

    # Verify user was created with lowercase email
    user = select(User).where(User.email == lowercase_email)
    user = test_db.exec(user).first()

    assert user is not None
    assert user.email == lowercase_email
    assert user.email != original_email  # Ensure it's not the original casing

    # Verify email verification was sent
    mock_send_email.assert_called_once()


def test_register_case_insensitive_duplicate_detection(
    unauthorized_client: TestClient, test_db: Session
):
    """Test that registration detects duplicate emails regardless of case."""
    # Create a user with lowercase email
    existing_email = "duplicate@example.com"
    user = UserFactory.create(
        email=existing_email,
        password="password",
        status=UserStatus.ACTIVE,
    )
    test_db.add(user)
    test_db.commit()

    # Try to register with the same email but different case
    uppercase_email = existing_email.upper()
    register_data = {
        "email": uppercase_email,
        "password": "password123",
        "first_name": "Another",
        "last_name": "User",
        "invitation_token": None,
    }

    response = unauthorized_client.post("/register", json=register_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    # Check for error message indicating duplicate email
    assert "message" in data["detail"]


def test_register_with_invitation(
    mock_send_email,
    unauthorized_client: TestClient,
    test_invitation: Invitation,
    test_db: Session,
):
    """Test successful user registration with invitation token."""
    register_data = {
        "email": "different@example.com",  # Different email than invitation (should be overridden)
        "password": "password123",
        "first_name": "Invited",
        "last_name": "User",
        "invitation_token": str(test_invitation.token),
    }

    response = unauthorized_client.post("/register", json=register_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data

    # Verify user was created with the email from the invitation
    user = select(User).where(User.email == test_invitation.email)
    user = test_db.exec(user).first()

    assert user is not None
    assert user.email == test_invitation.email
    assert user.first_name == register_data["first_name"]
    assert user.last_name == register_data["last_name"]
    assert verify_password(register_data["password"], user.hashed_password)
    assert (
        user.status == UserStatus.ACTIVE
    )  # Should be active immediately for email invitations

    # Verify invitation registration record was created
    invitation_registration = select(InvitationRegistration).where(
        InvitationRegistration.user_id == user.id,
        InvitationRegistration.invitation_id == test_invitation.id,
    )
    invitation_registration = test_db.exec(invitation_registration).first()
    assert invitation_registration is not None

    # Verify the invitation was marked as used
    test_db.refresh(test_invitation)
    assert test_invitation.expires_at <= datetime.now(timezone.utc)

    # Email verification should not be sent for email invitations
    mock_send_email.assert_not_called()


def test_register_with_invalid_invitation(unauthorized_client: TestClient):
    """Test registration with invalid invitation token."""
    register_data = {
        "email": "user@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "invitation_token": str(uuid.uuid4()),  # Random non-existent token
    }

    response = unauthorized_client.post("/register", json=register_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Invalid invitation token" in data["detail"]


def test_register_with_inactive_invitation(
    unauthorized_client: TestClient,
    inactive_test_invitation: Invitation,
):
    """Test registration with inactive invitation token."""
    register_data = {
        "email": "some-user@example.com",
        "password": "password123",
        "first_name": "Invited",
        "last_name": "User",
        "invitation_token": str(inactive_test_invitation.token),
    }

    response = unauthorized_client.post("/register", json=register_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Invitation token expired" in data["detail"]


def test_password_recovery(
    mock_send_email, unauthorized_client: TestClient, test_db: Session
):
    """Test password recovery request."""
    # Create user with UserFactory
    user = UserFactory.create(
        email="recovery@example.com",
        password="password",
        status=UserStatus.ACTIVE,
    )
    test_db.add(user)
    test_db.commit()

    response = unauthorized_client.post(f"/password-recovery/{user.email}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "Password recovery email sent" in data["message"]

    # Verify email was sent
    mock_send_email.assert_called_once()


def test_password_recovery_nonexistent_user(unauthorized_client: TestClient):
    """Test password recovery for nonexistent user."""
    response = unauthorized_client.post("/password-recovery/nonexistent@example.com")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_reset_password(
    unauthorized_client: TestClient,
    test_password_reset_data,
    test_db: Session,
):
    """Test password reset with valid token."""
    # Create user with UserFactory
    user = UserFactory.create(
        email="reset@example.com",
        password="password",
        status=UserStatus.ACTIVE,
    )
    test_db.add(user)
    test_db.commit()

    # Create a real password reset record in the database
    from app.models.password_reset import PasswordReset

    # Use the token from test data to make it predictable
    reset_token = uuid.UUID(test_password_reset_data["token"])

    password_reset = PasswordReset(
        token=reset_token,
        user_id=user.id,
    )
    test_db.add(password_reset)
    test_db.commit()

    response = unauthorized_client.post(
        "/reset-password", json=test_password_reset_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "Password updated successfully" in data["message"]

    test_db.refresh(user)
    assert verify_password(
        test_password_reset_data["new_password"], user.hashed_password
    )


def test_reset_password_invalid_token(unauthorized_client: TestClient):
    """Test password reset with invalid token."""
    # Use a UUID that doesn't exist in the database
    non_existent_token = str(uuid.uuid4())

    response = unauthorized_client.post(
        "/reset-password",
        json={"token": non_existent_token, "new_password": "newpassword123"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Invalid token" in data["detail"]


def test_reset_password_expired_token(
    unauthorized_client: TestClient,
    test_db: Session,
):
    """Test password reset with expired token."""
    # Create user
    user = UserFactory.create(
        email="expired_reset@example.com",
        password="password",
        status=UserStatus.ACTIVE,
    )
    test_db.add(user)
    test_db.commit()

    # Create an expired password reset record
    from app.models.password_reset import PasswordReset

    reset_token = uuid.uuid4()

    password_reset = PasswordReset(
        token=reset_token,
        user_id=user.id,
        expires_at=datetime.now() - timedelta(hours=1),  # Expired 1 hour ago
    )
    test_db.add(password_reset)
    test_db.commit()

    response = unauthorized_client.post(
        "/reset-password",
        json={"token": str(reset_token), "new_password": "newpassword123"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Invalid token" in data["detail"]


def test_password_reset_token_expiration(test_db: Session):
    """Test that password reset token expires after the configured time."""
    import freezegun

    from app.core.config import config
    from app.models.password_reset import PasswordReset

    # Create user
    user = UserFactory.create(
        email="token_expiration@example.com",
        password="password",
        status=UserStatus.ACTIVE,
    )
    test_db.add(user)
    test_db.commit()

    # Create password reset token at current time
    current_time = datetime.now(timezone.utc)
    reset_token = uuid.uuid4()
    password_reset = PasswordReset(
        token=reset_token,
        user_id=user.id,
    )
    test_db.add(password_reset)
    test_db.commit()
    test_db.refresh(password_reset)

    # Verify token is active at creation
    assert password_reset.is_active is True

    # Move time forward just before expiration
    with freezegun.freeze_time(
        current_time
        + timedelta(hours=config.PASSWORD_RESET_TOKEN_EXPIRY_IN_HOURS - 0.1)
    ):
        test_db.refresh(password_reset)
        assert (
            password_reset.is_active is True
        ), "Token should still be active just before expiration time"

    # Move time forward just after expiration
    with freezegun.freeze_time(
        current_time
        + timedelta(hours=config.PASSWORD_RESET_TOKEN_EXPIRY_IN_HOURS + 0.1)
    ):
        test_db.refresh(password_reset)
        assert (
            password_reset.is_active is False
        ), "Token should be expired after expiration time"


def test_resend_verification_email(
    mock_send_email, unauthorized_client: TestClient, pending_verification_user: User
):
    """Test resending verification email."""
    response = unauthorized_client.post(
        "/verify-email/resend",
        json={"email": pending_verification_user.email},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "Verification email sent successfully" in data["message"]

    # Verify email was sent
    mock_send_email.assert_called_once()


def test_verify_email(
    unauthorized_client: TestClient,
    pending_verification_user: User,
    test_db: Session,
):
    """Test email verification."""
    # Generate a real verification token and assign it to the user
    token = uuid.uuid4()
    pending_verification_user.email_verification_token = token
    test_db.add(pending_verification_user)
    test_db.commit()

    # Use the token to verify email
    response = unauthorized_client.get(f"/verify-email/{token}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "Email verified successfully" in data["message"]

    test_db.refresh(pending_verification_user)

    # Verify user status changed - fetch directly from database to ensure we get the latest state
    assert pending_verification_user is not None
    assert pending_verification_user.status == UserStatus.ACTIVE
    assert (
        pending_verification_user.email_verification_token is None
    )  # Token should be cleared


def test_verify_email_invalid_token(unauthorized_client: TestClient):
    """Test email verification with invalid token."""
    non_existent_token = uuid.uuid4()

    response = unauthorized_client.get(f"/verify-email/{non_existent_token}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert "Invalid verification token" in data["detail"]


def test_verify_email_already_verified(
    unauthorized_client: TestClient,
    test_db: Session,
    test_normal_user: User,
):
    """Test verification of an already verified user."""
    # Assign a token to an already active user
    token = uuid.uuid4()
    test_normal_user.email_verification_token = token
    test_db.add(test_normal_user)
    test_db.commit()

    response = unauthorized_client.get(f"/verify-email/{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Email already verified" in data["detail"]


def test_resend_verification_email_already_verified(
    unauthorized_client: TestClient, test_normal_user: User
):
    """Test resending verification email for already verified user."""

    response = unauthorized_client.post(
        "/verify-email/resend", json={"email": test_normal_user.email}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Email already verified" in data["detail"]


def test_get_me(authorized_client: TestClient, test_normal_user: User):
    """Test getting current user information."""
    # Keep using the existing fixture since it's tied to the authorized_client
    response = authorized_client.get("/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_normal_user.email
    assert data["id"] == str(test_normal_user.id)
    assert data["first_name"] == test_normal_user.first_name
    assert data["last_name"] == test_normal_user.last_name


def test_get_me_unauthorized(unauthorized_client: TestClient):
    """Test getting user info without authentication."""
    response = unauthorized_client.get("/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_user_me(authorized_client: TestClient, test_normal_user: User):
    """Test updating current user."""
    # Keep using the existing fixture since it's tied to the authorized_client
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
    }
    response = authorized_client.patch("/me", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]
    assert data["email"] == test_normal_user.email  # Email shouldn't change


def test_update_password_same_as_current(authorized_client: TestClient):
    """Test updating password to same value as current."""
    update_data = {
        "current_password": "password",  # Current password from fixture
        "new_password": "password",  # Same as current
    }
    response = authorized_client.patch("/me/password", json=update_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "New password cannot be the same as the current one" in data["detail"]


def test_update_password_me(
    authorized_client: TestClient, test_normal_user: User, test_db: Session
):
    update_data = {
        "current_password": "password",
        "new_password": "newpassword123",
    }
    response = authorized_client.patch("/me/password", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "Password updated successfully" in data["message"]

    test_db.refresh(test_normal_user)
    assert verify_password(
        update_data["new_password"], test_normal_user.hashed_password
    )


def test_update_password_incorrect_current(authorized_client: TestClient):
    """Test updating password with incorrect current password."""
    update_data = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123",
    }
    response = authorized_client.patch("/me/password", json=update_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Incorrect password" in data["detail"]


def test_superuser_cannot_deactivate_self(superuser_client: TestClient):
    """Test that superusers cannot deactivate their accounts."""
    response = superuser_client.patch("/me/deactivate")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert "Superusers cannot deactivate their own account" in data["detail"]


def test_deactivate_self(
    authorized_client: TestClient, test_normal_user: User, test_db: Session
):
    """Test deactivating own account."""
    # Keep using the existing fixture since it's tied to the authorized_client
    response = authorized_client.patch("/me/deactivate")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "Account successfully deactivated" in data["message"]

    # Verify user status changed
    test_db.refresh(test_normal_user)

    assert test_normal_user.status == UserStatus.DEACTIVATED
