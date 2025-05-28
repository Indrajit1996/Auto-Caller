import uuid
from pathlib import Path

from loguru import logger

from app.core.security import get_password_hash
from app.models.user import User, UserStatus
from data_pipeline.config import data_pipeline_config as dp_config
from data_pipeline.decorators import importer
from data_pipeline.importers.csv_importer import CSVImporter


@importer(name="user_importer")
def import_users_from_csv(
    file_path: str = str(dp_config.READY_FOR_IMPORT_DIR / "users_transformed.csv"),
    unique_fields: list | None = None,
    truncate: bool = False,
    skip_empty_rows: bool = True,
) -> None:
    if unique_fields is None:
        unique_fields = ["email"]

    importer = CSVImporter[User](User)

    transform_functions = {
        "first_name": lambda row: row["first_name"].capitalize(),
        "last_name": lambda row: row["last_name"].capitalize(),
        # Add extra fields not present in the CSV
        "hashed_password": get_password_hash("Admin@1234"),
        "email_verification_token": lambda row: uuid.uuid4(),
        "status": lambda row: UserStatus.ACTIVE,
        "is_superuser": lambda row: False,
    }

    imported_count = importer.import_csv(
        Path(file_path),
        mapping={
            "email": "email",
        },
        transform_functions=transform_functions,
        unique_fields=unique_fields,
        truncate=truncate,
        skip_empty_rows=skip_empty_rows,
    )

    logger.info(
        f"Imported {imported_count} users from {file_path} with unique fields: {unique_fields}"
    )
