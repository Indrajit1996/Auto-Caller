from factory.base import Factory

from app.core.db import SessionLocal


class SQLModelFactory(Factory):
    """Base Factory class for SQLModel instead of Django models."""

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create an instance of the model, but don't save it to the database."""
        return model_class(**kwargs)

    @classmethod
    def create_batch(cls, size, **kwargs):
        """Create a batch of models."""
        return [cls.create(**kwargs) for _ in range(size)]

    @classmethod
    def create_and_save(cls, **kwargs):
        """Create and save an instance to the database."""
        instance = cls.create(**kwargs)
        db = SessionLocal()
        try:
            db.add(instance)
            db.commit()
            db.refresh(instance)
            return instance
        finally:
            db.close()

    @classmethod
    def create_batch_and_save(cls, size, **kwargs):
        """Create and save a batch of instances to the database."""
        instances = cls.create_batch(size, **kwargs)
        db = SessionLocal()
        try:
            db.add_all(instances)
            db.commit()
            for instance in instances:
                db.refresh(instance)
            return instances
        finally:
            db.close()
