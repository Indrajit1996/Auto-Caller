from loguru import logger

from data_pipeline.importers.user_importer import import_users_from_csv  # noqa: F401


def initialize() -> None:
    """
    This function initializes the database with data and may utilize a combination of various importers, scripts, and seeders.
    It is designed to be run once during the initial setup of the application.
    """
    logger.info("Initializing data...")

    logger.info("Starting data import...")
    # import_users_from_csv()
    logger.info("Data import completed.")

    logger.info("Data initialization completed.")


if __name__ == "__main__":
    initialize()
