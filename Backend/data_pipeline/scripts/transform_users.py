import pandas as pd
from loguru import logger

from data_pipeline.config import data_pipeline_config as dp_config
from data_pipeline.decorators import script


@script(name="transform_users")
def transform_users_csv(
    src: str = f"{dp_config.SOURCE_DIR}/users.csv",
    output: str = f"{dp_config.READY_FOR_IMPORT_DIR}/users_transformed.csv",
) -> None:
    logger.info(f"Transforming users data from {src}")
    df = pd.read_csv(src, low_memory=False)

    # Remove 'id' and 'created_at' columns
    if "id" in df.columns and "created_at" in df.columns:
        df = df.drop(columns=["id", "created_at"])

    # Save the transformed data
    df.to_csv(output, index=False)

    logger.info(f"Transformed users data saved to {output}")
