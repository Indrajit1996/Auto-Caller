import uuid
from typing import Any

from factory.declarations import LazyFunction
from faker import Faker
from loguru import logger
from sqlmodel import select

from app.api.deps import get_db
from app.models.group import Group, UserGroup
from app.models.user import User, UserStatus
from data_pipeline.decorators import seeder
from data_pipeline.seeders.sqlmodel_factory import SQLModelFactory
from data_pipeline.seeders.utils import create_relationships, seed_data

faker = Faker()


class GroupFactory(SQLModelFactory):
    """Factory for creating Group instances with fake data."""

    class Meta:
        model = Group

    name = LazyFunction(lambda: faker.company())
    description = LazyFunction(lambda: faker.catch_phrase())
    created_by_user_id = None  # Will be set dynamically


class UserGroupFactory(SQLModelFactory):
    """Factory for creating UserGroup relationship instances."""

    class Meta:
        model = UserGroup

    user_id = None  # Will be set dynamically
    group_id = None  # Will be set dynamically


def seed_groups(
    count: int = 5,
    attributes: dict[str, Any] | None = None,
    with_users: bool = False,
    users: list[User] | None = None,
    users_per_group_range: tuple[int, int] = (1, 5),
    created_by_user_id: uuid.UUID | None = None,
) -> list[Group]:
    """
    Seeds groups and optionally associates them with users.

    Args:
        count: Number of groups to create
        attributes: Additional attributes for groups
        with_users: Whether to add users to groups
        users: List of existing users to use (if None, new users will be created)
        users_per_group: Number of users to add per group
        created_by_user_id: UUID of user who created the groups

    Returns:
        List of created Group instances
    """
    attr = attributes or {}

    # If no creator is provided, create or select one
    if not created_by_user_id and (not attr or "created_by_user_id" not in attr):
        if not users:
            from data_pipeline.seeders.user_seeder import seed_users

            creator = seed_users(count=1)[0]
        else:
            creator = users[0]

        attr["created_by_user_id"] = creator.id

    # Use provided created_by_user_id if given
    if created_by_user_id and "created_by_user_id" not in attr:
        attr["created_by_user_id"] = created_by_user_id

    # Create groups
    groups = list(
        seed_data(
            factory_class=GroupFactory,
            count=count,
            attributes=attr,
            unique_fields=["name"],
        )
    )

    # Add users to groups if requested
    if with_users:
        import random

        if not users:
            # Check for existing users first
            db = next(get_db())
            estimated_user_count = count * random.randint(*users_per_group_range)
            existing_users = db.exec(
                select(User)
                .where(User.status == UserStatus.ACTIVE)
                .limit(estimated_user_count)
            ).all()

            if existing_users:
                logger.info(
                    f"Found {len(existing_users)} existing users to use for groups"
                )

                # If we don't have enough existing users, create more
                if len(existing_users) < estimated_user_count:
                    logger.info(
                        f"Creating {estimated_user_count - len(existing_users)} additional users..."
                    )
                    from data_pipeline.seeders.user_seeder import seed_users

                    additional_users = seed_users(
                        count=estimated_user_count - len(existing_users)
                    )
                    users = existing_users + additional_users
                else:
                    users = existing_users
            else:
                logger.info("No existing users found. Creating new users...")
                from data_pipeline.seeders.user_seeder import seed_users

                users = seed_users(count=estimated_user_count)

        # Define attribute generator for create_relationships function
        def attr_generator(group):
            random_users = random.sample(
                users, min(random.randint(*users_per_group_range), len(users))
            )
            user_groups = []

            for user in random_users:
                user_groups.append({"user_id": user.id, "group_id": group.id})

            return user_groups

        # Create UserGroup relationships using the fixed create_relationships
        create_relationships(
            parent_objects=groups,
            child_factory=UserGroupFactory,
            relationship_field="group_id",  # Not used when attributes_generator provides all fields
            attributes_generator=attr_generator,
        )

    return groups


@seeder(name="group_seeder")
def run(count: int = 5) -> None:
    logger.info("Seeding groups...")
    groups = seed_groups(count=count, with_users=True)
    logger.info(f"Created {len(groups)} groups.")
