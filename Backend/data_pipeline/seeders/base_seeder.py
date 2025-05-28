from collections.abc import Callable
from typing import Any

from sqlmodel import SQLModel

from app.core.db import SessionLocal
from data_pipeline.seeders.sqlmodel_factory import SQLModelFactory


class BaseSeeder:
    """Base class for seeding data using SQLModel-compatible factories."""

    def __init__(self, factory_class: type[SQLModelFactory], batch_size: int = 100):
        self.factory_class = factory_class
        self.batch_size = batch_size

    def seed(
        self,
        count: int,
        attributes: dict[str, Any] | None = None,
        unique_fields: list[str] | None = None,
        post_save_hook: Callable | None = None,
    ) -> list[SQLModel]:
        """
        Seed the database with generated data.

        Args:
            count: Number of records to create
            attributes: Fixed attributes to set on all created objects
            unique_fields: Fields that should be unique across all objects
            post_save_hook: Function to run on each object after saving

        Returns:
            List of created model instances
        """
        created_objects = []
        attributes = attributes or {}

        # Process in batches
        for i in range(0, count, self.batch_size):
            batch_size = min(self.batch_size, count - i)

            # Create batch of objects
            batch = self._create_batch(
                batch_size, attributes=attributes, unique_fields=unique_fields
            )

            # Save batch to database
            self._save_batch(batch)

            # Apply post-save hook if provided
            if post_save_hook:
                for obj in batch:
                    post_save_hook(obj)

            created_objects.extend(batch)

        return created_objects

    def _create_batch(
        self,
        size: int,
        attributes: dict[str, Any] = None,
        unique_fields: list[str] = None,
    ) -> list[SQLModel]:
        """Create a batch of objects with the factory."""
        objects = []
        attributes = attributes or {}

        # Create objects one by one to handle unique constraints
        for _ in range(size):
            # Generate object with the factory
            obj = self.factory_class(**attributes)

            # Check uniqueness if required
            if unique_fields and objects:
                while not self._is_unique(obj, objects, unique_fields):
                    # Regenerate with same params if not unique
                    obj = self.factory_class(**attributes)

            objects.append(obj)

        return objects

    def _is_unique(
        self, obj: SQLModel, existing_objects: list[SQLModel], unique_fields: list[str]
    ) -> bool:
        """Check if object is unique compared to existing objects."""
        for existing in existing_objects:
            match = True
            for field in unique_fields:
                if getattr(obj, field) != getattr(existing, field):
                    match = False
                    break
            if match:
                return False

        # Also check database for uniqueness
        db = SessionLocal()
        try:
            model_class = obj.__class__
            query = db.query(model_class)

            for field in unique_fields:
                query = query.filter(getattr(model_class, field) == getattr(obj, field))

            existing_record = query.first()
            return existing_record is None
        finally:
            db.close()

    def _save_batch(self, objects: list[SQLModel]) -> None:
        """Save a batch of objects to the database."""
        if not objects:
            return

        db = SessionLocal()
        try:
            db.add_all(objects)
            db.commit()
            for obj in objects:
                db.refresh(obj)
        finally:
            db.close()
