# Data Pipeline CLI

A flexible command-line interface for managing data processing, import, and seeding operations within the larger project.

## Overview

The data pipeline CLI provides a standardized way to process, import, and seed data through the `kcli data` command. It follows a modular approach with three main components:

- **Data Processing**: Transform and prepare raw data for import
- **Data Import**: Load processed data into the database
- **Database Seeding**: Generate test data for development and testing

## Directory Structure

The data pipeline is organized into the following main directories:

- `data/` - Contains source and output data files
- `importers/` - Houses data importers for different entity types
- `scripts/` - Contains data transformation and processing scripts
- `seeders/` - Includes database seeders for generating test data

## Quick Start Guide

### For First-Time Users

If you have a CSV file that can be directly imported without much transformation:

1. Place your CSV file in the `data_pipeline/data/output` directory
2. Create a CSV importer for your model in the `importers` directory
3. Use the `@importer` decorator on your main import function
4. Run the importer using `kcli data import your_model_importer`

### Creating a Basic Importer

The data pipeline provides two main ways to create importers:

#### Method 1: Using the CSVImporter class with decorator

```python
# importers/user_importer.py
import uuid
from pathlib import Path
from loguru import logger
from app.core.security import get_password_hash
from app.models.user import User, UserStatus
from data_pipeline.config import data_pipeline_config as dp_config
from data_pipeline.importers.csv_importer import CSVImporter
from data_pipeline.decorators import importer

DEFAULT_FILE_PATH = str(dp_config.OUTPUT_DIR / "users_transformed.csv")

@importer
def import_users_from_csv(file_path: str) -> None:
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

    unique_fields = ["email"]

    imported_count = importer.import_csv(
        Path(file_path),
        mapping={
            "email": "email",
        },
        transform_functions=transform_functions,
        unique_fields=unique_fields,
    )

    logger.info(
        f"Imported {imported_count} users from {file_path} with unique fields: {unique_fields}"
    )
```

#### Method 2: Creating a subclass of CSVImporter with decorator

```python
# importers/example_importer.py
from data_pipeline.importers.csv_importer import CSVImporter
from your_app.models import ExampleModel
from data_pipeline.decorators import importer

class ExampleImporter(CSVImporter):
    def __init__(self, file_path=None):
        super().__init__(
            model=ExampleModel,
            file_path=file_path or "data/output/examples.csv",
            unique_fields=["id"]  # Fields to check for duplicates
        )

    def import_data(self):
        # Implementation details
        pass

@importer(name="example_importer")
def import_example_data(file_path: str = None):
    importer = ExampleImporter(file_path)
    importer.import_data()
```

## Usage

All commands use synchronous DB operations by default, which is the recommended approach.

### Basic Commands

```bash
# Show help for all data commands
kcli data -h

# Show overall status of data pipeline components
kcli data status
```

### Pipeline Commands

```bash
# Run the complete pipeline (process, import, seed)
kcli data run-pipeline

# Run with specific steps
kcli data run-pipeline --no-process --no-seed  # Import only
```

### Data Processing

```bash
# Run the data processing step
kcli data process

# List available processing scripts
kcli data list-scripts

# Run a specific script
kcli data run-script transform_users
```

### Data Import

```bash
# List available importers
kcli data list-importers

# Run a specific importer
kcli data import user_importer

# Run a specific importer with custom file path
kcli data import user_importer --file path/to/data.csv

# Run all importers (uses import_data.py as entrypoint)
kcli data import-all
```

### Database Seeding

In most cases, seeders won't be required for the project, but they're available for local development and testing.

```bash
# List available seeders
kcli data list-seeders

# Run a specific seeder
kcli data seed user_seeder

# Run a specific seeder with custom count
kcli data seed user_seeder --count 50

# Run all seeders
kcli data seed-all

# Run all seeders with custom count
kcli data seed-all --count 50

# Run using seed_data script instead of individual seeders
kcli data seed-all --script
```

## Advanced Features

### Data Transformations

The `CSVImporter` class supports transformation functions that can modify or add data during import:

```python
transform_functions = {
    # Transform existing fields
    "first_name": lambda row: row["first_name"].capitalize(),

    # Add fields not in the CSV
    "status": lambda row: UserStatus.ACTIVE,
    "created_at": lambda row: datetime.now(),

    # Generate unique values
    "uuid": lambda row: uuid.uuid4(),
}
```

### Field Mapping

You can map CSV column names to model field names:

```python
mapping = {
    "email": "email_address",  # Maps CSV column "email" to model field "email_address"
    "first": "first_name",     # Maps CSV column "first" to model field "first_name"
}
```

### Unique Field Validation

Prevent duplicate entries by specifying unique fields:

```python
unique_fields = ["email", "username"]  # Will check for existing records with these fields
```

## Extending the Pipeline with Decorators

The pipeline uses decorators to register components. Each decorator ensures the function has the required parameters:

### Creating a New Importer

1. Create a new file in the `importers` directory
2. Apply the `@importer` decorator to your main function
3. Ensure your function has a `file_path: str` parameter

```python
# importers/product_importer.py
from data_pipeline.decorators import importer

@importer
def import_products(file_path: str) -> None:
    # Import implementation...
    pass

# With custom name
@importer(name="my_custom_importer")
def import_data(file_path: str) -> None:
    # Import implementation...
    pass
```

### Creating a New Seeder

1. Create a new file in the `seeders` directory
2. Apply the `@seeder` decorator to your main function
3. Ensure your function has a `count: int` parameter

```python
# seeders/product_seeder.py
from data_pipeline.decorators import seeder
from data_pipeline.seeders.base_seeder import BaseSeeder
from your_app.models import Product
from data_pipeline.seeders.sqlmodel_factory import register_factory

# Register factory for generating test data
register_factory(Product, {
    'name': 'factory.Faker("product_name")',
    'price': 'factory.Faker("pydecimal", left_digits=3, right_digits=2)',
    'sku': 'factory.Sequence(lambda n: f"SKU-{n}")'
})

@seeder
def seed_products(count: int = 10) -> None:
    seeder = ProductSeeder()
    seeder.seed(count)

class ProductSeeder(BaseSeeder):
    def __init__(self):
        super().__init__(model=Product)
```

### Creating a New Processing Script

1. Create a new file in the `scripts` directory
2. Apply the `@script` decorator to your main function

```python
# scripts/normalize_data.py
import pandas as pd
from pathlib import Path
from data_pipeline.decorators import script

@script
def normalize_data(args=None):
    # Implementation details...
    input_file = Path("data_pipeline/data/src/raw_data.csv")
    output_file = Path("data_pipeline/data/output/normalized_data.csv")

    df = pd.read_csv(input_file)
    # Perform transformations
    df.to_csv(output_file, index=False)
```

## Important Notes

1. **Decorators enforce required parameters**:

   - `@importer` requires a `file_path: str` parameter
   - `@seeder` requires a `count: int` parameter
   - `@script` has no specific parameter requirements
2. In production, `import_data.py` is the main entrypoint script to load all data. You can configure your data import scripts to truncate and repopulate tables as needed.
3. For direct imports without transformation, place your CSV files in the `data_pipeline/data/output` directory.
4. Database operations are synchronous by default, which is recommended.
