"""Package initialization file for data pipeline scripts."""

import importlib
import pkgutil
from pathlib import Path

_scripts_initialized = False


def initialize_scripts() -> None:
    """
    Auto-discover and import all script modules in the scripts package.
    This ensures all decorated scripts are registered.
    """
    global _scripts_initialized
    if _scripts_initialized:
        return

    package_dir = Path(__file__).parent
    for _, name, ispkg in pkgutil.iter_modules([str(package_dir)]):
        if not ispkg and name != "cli":  # Skip the CLI module and any subpackages
            importlib.import_module(f"data_pipeline.scripts.{name}")

    _scripts_initialized = True


# Export the function to be used elsewhere
__all__ = ["initialize_scripts"]
