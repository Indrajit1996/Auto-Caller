"""Package initialization file for data pipeline importers."""

import importlib
import pkgutil
from pathlib import Path

_importers_initialized = False


def initialize_importers() -> None:
    """
    Auto-discover and import all importer modules in the importers package.
    This ensures all decorated importers are registered.
    """
    global _importers_initialized
    if _importers_initialized:
        return

    package_dir = Path(__file__).parent
    for _, name, ispkg in pkgutil.iter_modules([str(package_dir)]):
        if not ispkg and name != "cli":  # Skip the CLI module and any subpackages
            importlib.import_module(f"data_pipeline.importers.{name}")

    _importers_initialized = True


# Export the function to be used elsewhere
__all__ = ["initialize_importers"]
