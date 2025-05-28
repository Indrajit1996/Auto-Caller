import random
import uuid
from typing import Any

from factory.declarations import LazyFunction
from faker import Faker
from loguru import logger
from passlib.context import CryptContext

from app.models.user import User, UserStatus
from data_pipeline.decorators import seeder
from data_pipeline.seeders.sqlmodel_factory import SQLModelFactory
from data_pipeline.seeders.utils import seed_data

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
faker = Faker()


class UserFactory(SQLModelFactory):
    """Factory for creating User instances with fake data."""

    class Meta:
        model = User

    id = LazyFunction(uuid.uuid4)
    first_name = LazyFunction(lambda: faker.first_name())
    last_name = LazyFunction(lambda: faker.last_name())
    email = LazyFunction(lambda: faker.email())
    hashed_password = LazyFunction(lambda: pwd_context.hash("password"))
    status = LazyFunction(lambda: random.choice(list(UserStatus)))
    is_superuser = False
    last_login = None


def seed_users(
    count: int = 10,
    attributes: dict[str, Any] | None = None,
    superuser_ratio: float = 0.1,
) -> list[User]:
    attr = attributes or {}

    superuser_count = int(count * superuser_ratio)
    regular_count = count - superuser_count

    # Create regular users
    users = list(
        seed_data(
            factory_class=UserFactory,
            count=regular_count,
            attributes=attr,
            unique_fields=["email"],
        )
    )

    # Create superusers
    if superuser_count > 0:
        superusers = list(
            seed_data(
                factory_class=UserFactory,
                count=superuser_count,
                attributes={**attr, "is_superuser": True},
                unique_fields=["email"],
            )
        )
        users.extend(superusers)

    return users


@seeder(name="user_seeder")
def run(count: int = 10) -> None:
    logger.info("Seeding users...")
    users = seed_users(count=count, superuser_ratio=0.2)
    logger.info(f"Created {len(users)} users.")
