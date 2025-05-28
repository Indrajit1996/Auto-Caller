import random
from typing import Any

from factory.declarations import LazyFunction
from loguru import logger

from app.models.notification import Notification, NotificationChannel, NotificationType
from app.models.user import User, UserStatus
from data_pipeline.decorators import seeder
from data_pipeline.seeders.sqlmodel_factory import SQLModelFactory
from data_pipeline.seeders.utils import seed_data


class NotificationFactory(SQLModelFactory):
    """Factory for creating Notification instances with fake data."""

    class Meta:
        model = Notification

    message = LazyFunction(lambda: f"Test notification {random.randint(1, 1000)}")
    type = LazyFunction(lambda: random.choice(list(NotificationType)))
    channel = LazyFunction(lambda: random.choice(list(NotificationChannel)))
    is_read = LazyFunction(lambda: random.choice([True, False]))
    meta_data = LazyFunction(
        lambda: {"test_key": f"test_value_{random.randint(1, 1000)}"}
    )


def seed_notifications(
    count: int = 10,
    attributes: dict[str, Any] | None = None,
    read_ratio: float = 0.5,
    users: list[User] | None = None,
) -> list[Notification]:
    attr = attributes or {}

    # If users are provided, randomly assign user_id to notifications
    if users and len(users) > 0:
        user_ids = [user.id for user in users]

        # If user_id wasn't explicitly set in attributes
        if "user_id" not in attr:
            # For each notification we'll create, assign a random user
            attr_with_user = lambda: {**attr, "user_id": random.choice(user_ids)}
        else:
            attr_with_user = lambda: attr
    else:
        attr_with_user = lambda: attr

    read_count = int(count * read_ratio)
    unread_count = count - read_count

    # Create unread notifications
    notifications = list(
        seed_data(
            factory_class=NotificationFactory,
            count=unread_count,
            attributes={**attr_with_user(), "is_read": False},
        )
    )

    # Create read notifications
    if read_count > 0:
        read_notifications = list(
            seed_data(
                factory_class=NotificationFactory,
                count=read_count,
                attributes={**attr_with_user(), "is_read": True},
            )
        )
        notifications.extend(read_notifications)

    return notifications


@seeder(name="notification_seeder")
def run(count: int = 10) -> None:
    logger.info("Seeding notifications...")

    # First check for existing active users
    from sqlmodel import select

    from app.api.deps import get_db
    from app.models.user import User
    from data_pipeline.seeders.user_seeder import seed_users

    db = next(get_db())
    existing_users = db.exec(
        select(User).where(User.status == UserStatus.ACTIVE).limit(5)
    ).all()

    if existing_users:
        logger.info(
            f"Found {len(existing_users)} existing users to use for notifications"
        )
        users = existing_users
    else:
        logger.info("No existing users found. Creating new users...")
        users = seed_users(count=5)  # Create users only if none exist

    notifications = seed_notifications(count=count, read_ratio=0.3, users=users)
    logger.info(f"Created {len(notifications)} notifications for {len(users)} users.")
