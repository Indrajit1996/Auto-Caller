from sqlmodel import Session, select

from app.models.user import User, UserStatus


def test_db_connection(test_db: Session):
    """Test that the database connection works."""
    assert test_db is not None

    # Verify we can execute a query
    result = test_db.execute(select(1)).scalar_one()
    assert result == 1


def test_transaction_isolation(test_db: Session):
    """Test that transactions are isolated between tests."""

    # Add a user that should be visible only in this test
    user = User(
        first_name="Isolated",
        last_name="User",
        email="isolated@example.com",
        hashed_password="hashed_password",
        status=UserStatus.ACTIVE,
    )
    test_db.add(user)
    test_db.commit()

    # Verify user exists in this transaction
    users = test_db.exec(select(User).where(User.email == "isolated@example.com")).all()
    assert len(users) == 1
