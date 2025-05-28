"""Package initialization file for data pipeline seeders."""

import importlib
import pkgutil
from pathlib import Path

_seeders_initialized = False


def initialize_seeders() -> None:
    """
    Auto-discover and import all seeder modules in the seeders package.
    This ensures all decorated seeders are registered.
    """
    global _seeders_initialized
    if _seeders_initialized:
        return

    package_dir = Path(__file__).parent
    for _, name, ispkg in pkgutil.iter_modules([str(package_dir)]):
        if not ispkg and name != "cli":  # Skip the CLI module and any subpackages
            importlib.import_module(f"data_pipeline.seeders.{name}")

    _seeders_initialized = True


# Export the function to be used elsewhere
__all__ = ["initialize_seeders"]
