import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


class DataPipelineConfig(BaseSettings):
    """
    Configuration settings for the data pipeline.
    Defines source and output paths for data processing.
    """

    # Base directory paths
    BASE_DIR: Path = Path(__file__).parent

    SOURCE_DIR: Path = BASE_DIR / "data" / "src"
    READY_FOR_IMPORT_DIR: Path = BASE_DIR / "data" / "import_ready"

    @field_validator("*")
    @classmethod
    def create_directories(cls, v, info):
        """Ensure all directory paths exist by creating them if necessary."""
        if isinstance(v, Path):
            if not v.exists():
                os.makedirs(v, exist_ok=True)
        return v

    def get_path_dict(self) -> dict[str, Path]:
        """Return a dictionary of all configured paths."""
        return {
            "base_dir": self.BASE_DIR,
            "source_dir": self.SOURCE_DIR,
            "ready_for_import_dir": self.READY_FOR_IMPORT_DIR,
        }


# Create a singleton instance
data_pipeline_config = DataPipelineConfig()
