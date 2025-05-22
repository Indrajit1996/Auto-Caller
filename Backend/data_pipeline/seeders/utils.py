import random
from collections.abc import Callable
from typing import Any

from sqlmodel import SQLModel

from app.core.db import SessionLocal
from data_pipeline.seeders.base_seeder import BaseSeeder
from data_pipeline.seeders.sqlmodel_factory import SQLModelFactory


def seed_data(
    factory_class: type[SQLModelFactory],
    count: int,
    attributes: dict[str, Any] | None = None,
    unique_fields: list[str] | None = None,
    batch_size: int = 100,
    post_save_hook: Callable | None = None,
) -> list[SQLModel]:
    """
    Utility function to seed data using a factory.

    Args:
        factory_class: The factory class to use for generating objects
        count: Number of records to create
        attributes: Fixed attributes to set on all created objects
        unique_fields: Fields that should be unique across all objects
        batch_size: Number of records to create in each batch
        post_save_hook: Function to run on each object after saving

    Returns:
        List of created model instances
    """
    seeder = BaseSeeder(factory_class=factory_class, batch_size=batch_size)
    return seeder.seed(
        count=count,
        attributes=attributes,
        unique_fields=unique_fields,
        post_save_hook=post_save_hook,
    )


def create_relationships(
    parent_objects: list[SQLModel],
    child_factory: type[SQLModelFactory],
    relationship_field: str,
    count_generator: Callable[[SQLModel], int] | None = None,
    attributes_generator: Callable[[SQLModel], list[dict[str, Any]]] | None = None,
    batch_size: int = 100,
) -> list[SQLModel]:
    """
    Create related objects for a list of parent objects.

    Args:
        parent_objects: List of parent model instances
        child_factory: Factory class for child objects
        relationship_field: Field name on child that references parent
        count_generator: Function that returns number of children for each parent
        attributes_generator: Function that returns a list of attribute dictionaries for children
        batch_size: Batch size for database operations

    Returns:
        List of created child objects
    """
    if count_generator is None:

        def default_count_generator(_):
            return random.randint(1, 5)

    all_child_objects = []
    current_batch = []

    for parent in parent_objects:
        # If attributes_generator is provided, use it to get all attributes for this parent
        if attributes_generator:
            attributes_list = attributes_generator(parent)
            for attrs in attributes_list:
                child = child_factory(**attrs)
                current_batch.append(child)
                all_child_objects.append(child)
        else:
            # Original behavior: create count children with relationship_field set
            count = default_count_generator(parent)
            for _ in range(count):
                child = child_factory(
                    **{relationship_field: getattr(parent, "id", parent)}
                )
                current_batch.append(child)
                all_child_objects.append(child)

        # Save in batches
        if len(current_batch) >= batch_size:
            db = SessionLocal()
            try:
                db.add_all(current_batch)
                db.commit()
                for obj in current_batch:
                    db.refresh(obj)
                current_batch = []
            finally:
                db.close()

    # Save any remaining objects
    if current_batch:
        db = SessionLocal()
        try:
            db.add_all(current_batch)
            db.commit()
            for obj in current_batch:
                db.refresh(obj)
        finally:
            db.close()

    return all_child_objects
