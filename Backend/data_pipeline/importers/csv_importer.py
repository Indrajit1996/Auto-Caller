import csv
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generic, TypeVar

import pandas as pd
from sqlalchemy import text
from sqlmodel import SQLModel, and_, or_, select
from sqlmodel.orm.session import Session

from app.core.db import SessionLocal

T = TypeVar("T", bound=SQLModel)


class CSVImporter(Generic[T]):
    """Class for importing CSV data into SQLModel models using existing DB configuration."""

    def __init__(self, model_class: type[T], batch_size: int = 5000):
        self.model_class = model_class
        self.batch_size = batch_size

    @contextmanager
    def get_db(self) -> Generator[Session, Any, None]:
        """Context manager for database sessions."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def validate_csv(
        self,
        csv_path: Path,
        required_columns: list[str] | None = None,
        delimiter: str = ",",
        custom_validator: Callable[[Path, list[str] | None], tuple[bool, str | None]]
        | None = None,
    ) -> tuple[bool, str | None, list[str] | None]:
        """
        Validates a CSV file before importing:
        - Checks if the file exists and is readable
        - Verifies it's a valid CSV file
        - Validates against required columns if specified
        - Validates that all records have values for required columns
        - Runs a custom validator if provided

        Args:
            csv_path: Path to the CSV file
            required_columns: List of column names that must exist in the CSV
            delimiter: CSV delimiter character
            custom_validator: Optional function for custom validation
                              that takes (csv_path, header_columns) and returns (is_valid, error_message)

        Returns:
            Tuple of (is_valid, error_message, header_columns)
        """
        # Check if file exists
        if not csv_path.exists():
            return False, f"CSV file not found: {csv_path}", None

        # Check if file is readable and has content
        try:
            # Read the entire CSV file for validation (without loading everything into memory)
            with open(csv_path, encoding="utf-8") as f:
                # Check if file is empty
                first_line = f.readline().strip()
                if not first_line:
                    return False, f"CSV file is empty: {csv_path}", None

                # Reset file pointer
                f.seek(0)

                # Check for blank lines in the first few lines
                sample_lines = []
                for _ in range(10):  # Check first 10 lines for blank lines
                    line = f.readline()
                    if not line:  # End of file
                        break
                    sample_lines.append(line)

                # Reset file pointer again
                f.seek(0)

                # Check for blank lines in the sample
                if any(not line.strip() for line in sample_lines):
                    return (
                        False,
                        "CSV contains blank lines which may cause parsing errors",
                        None,
                    )

                # Use csv reader for the entire file
                reader = csv.reader(f, delimiter=delimiter)

                # Get header
                try:
                    header = next(reader, None)
                except csv.Error as e:
                    return False, f"CSV format error in header: {str(e)}", None

            if not header:
                return False, f"CSV file has no valid header: {csv_path}", None

            # Check for empty header columns
            if any(not col.strip() for col in header):
                return False, "CSV header contains blank column names", None

            # Clean header columns (trim whitespace)
            header = [col.strip() for col in header]

            # If required columns were specified, validate they exist in header
            if required_columns:
                missing_columns = [col for col in required_columns if col not in header]
                if missing_columns:
                    return (
                        False,
                        f"Missing required columns: {', '.join(missing_columns)}",
                        header,
                    )

            # Now read the entire file to validate all rows
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=delimiter)
                next(reader)  # Skip header

                # Check for data rows
                line_number = 2  # Start at 2 to account for header
                has_data = False
                inconsistent_rows = []
                missing_data_rows = []

                # Get indices of required columns
                column_indices = (
                    {header.index(col) for col in required_columns}
                    if required_columns
                    else set()
                )

                # Process each row
                for row in reader:
                    has_data = True

                    # Check for consistent column counts
                    if len(row) != len(header):
                        inconsistent_rows.append(line_number)
                        # Only collect first 5 inconsistent rows to avoid memory issues on large files
                        if len(inconsistent_rows) >= 5:
                            break

                    # Check for missing data in required columns
                    elif required_columns:
                        if any(
                            i < len(row) and not row[i].strip() for i in column_indices
                        ):
                            missing_data_rows.append(line_number)
                            # Only collect first 5 rows with missing data
                            if len(missing_data_rows) >= 5:
                                break

                    line_number += 1

            if not has_data:
                return False, "CSV file has a header but no data rows", header

            if inconsistent_rows:
                row_numbers = ", ".join(map(str, inconsistent_rows[:5]))
                if len(inconsistent_rows) > 5:
                    row_numbers += " and more"
                return (
                    False,
                    f"Inconsistent column counts at row(s): {row_numbers}",
                    header,
                )

            if missing_data_rows:
                row_numbers = ", ".join(map(str, missing_data_rows[:5]))
                if len(missing_data_rows) > 5:
                    row_numbers += " and more"
                return (
                    False,
                    f"Missing required data in row(s): {row_numbers}",
                    header,
                )

            # Apply custom validator if provided
            if custom_validator and callable(custom_validator):
                is_valid, error_message = custom_validator(csv_path, header)
                if not is_valid:
                    return False, error_message, header

            return True, None, header

        except Exception as e:
            return (
                False,
                f"Error validating CSV file: {str(e) or 'Unknown error'}",
                None,
            )

    def import_csv(
        self,
        csv_path: Path,
        mapping: dict[str, str] | None = None,
        transform_functions: dict[str, Callable] | None = None,
        unique_fields: list[str] | None = None,
        required_columns: list[str] | None = None,
        skip_validation: bool = False,
        custom_validator: Callable[[Path, list[str] | None], tuple[bool, str | None]]
        | None = None,
        skip_empty_rows: bool = True,
        truncate: bool = False,
    ) -> int:
        """
        Import data from CSV file to database.

        Args:
            csv_path: Path to the CSV file
            mapping: Dictionary mapping CSV column names to model field names
            transform_functions: Dictionary of field names and functions to transform their values
            unique_fields: List of field names to check for uniqueness (can be a single field or combination)
            required_columns: List of columns that must exist in the CSV file (if None, header columns are used)
            skip_validation: If True, skips the validation step
            custom_validator: Optional function for custom validation
                              that takes (csv_path, header_columns) and returns (is_valid, error_message)
            skip_empty_rows: If True, empty rows in the CSV will be skipped during import
            truncate: If True, truncate the table before importing data

        Returns:
            Number of records imported

        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            ValueError: If the CSV validation fails
        """
        header_columns = None

        # If required_columns is None, first get the header to use as required columns
        if required_columns is None:
            try:
                # Read just the header row to get column names
                with open(csv_path, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header_columns = next(reader, [])
                    if not header_columns:
                        raise ValueError("CSV file must have a header row")
                    header_columns = [col.strip() for col in header_columns]

                # Use the header as required columns
                required_columns = header_columns
            except Exception as e:
                if not skip_validation:
                    raise ValueError(f"Error reading CSV header: {str(e)}")

        # Validate the CSV file unless skip_validation is True
        if not skip_validation:
            is_valid, error_message, header_columns = self.validate_csv(
                csv_path,
                required_columns=required_columns,
                custom_validator=custom_validator,
            )
            if not is_valid:
                raise ValueError(error_message)
        elif not csv_path.exists():
            # Even if validation is skipped, still check basic file existence
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Truncate the table if requested
        if truncate:
            with self.get_db() as db:
                # Delete all records from the table
                db.execute(
                    text("TRUNCATE TABLE :table_name").params(
                        table_name=self.model_class.__tablename__
                    )
                )
                db.commit()

        # For very large files, use pandas with chunking
        total_imported = 0

        # Configure pandas to handle common CSV issues
        read_csv_kwargs = {
            "chunksize": self.batch_size,
            "skip_blank_lines": skip_empty_rows,
            "on_bad_lines": "warn" if skip_validation else "error",
        }

        for chunk in pd.read_csv(csv_path, **read_csv_kwargs):
            # Transform the chunk according to mapping and transform functions
            records = self._transform_chunk(chunk, mapping, transform_functions)

            # Filter out duplicates if unique_fields provided
            if unique_fields:
                records = self._filter_duplicates(records, unique_fields)

            # Convert to model instances and save
            imported = self._save_records(records)
            total_imported += imported

        return total_imported

    def _transform_chunk(
        self,
        chunk: pd.DataFrame,
        mapping: dict[str, str] | None = None,
        transform_functions: dict[str, Callable] | None = None,
    ) -> list[dict[str, Any]]:
        """Transform a chunk of data according to mapping and transform functions."""
        # Apply column mapping if provided
        if mapping:
            chunk = chunk.rename(columns=mapping)

        # Convert to records for processing
        records = chunk.to_dict(orient="records")

        # Apply transform functions if provided, even for fields not in CSV
        if transform_functions and records:
            for record in records:
                for field, func in transform_functions.items():
                    # Apply transform to existing fields, or add new fields not in CSV
                    if callable(func):
                        record[field] = func(record)
                    else:
                        # Handle static values (non-callable)
                        record[field] = func

        return records

    def _filter_duplicates(
        self, records: list[dict[str, Any]], unique_fields: list[str]
    ) -> list[dict[str, Any]]:
        """
        Filter out records that already exist in the database or are duplicated within the imported data.
        First checks for duplicates within the records themselves, then against the database.
        """
        if not records:
            return []

        # Step 1: Filter duplicates within the records themselves
        seen_keys = set()
        unique_records = []

        for record in records:
            # Create a tuple of the values of unique fields for each record
            key_values = tuple(record.get(field) for field in unique_fields)

            # Skip if any key field is None
            if None in key_values:
                unique_records.append(record)
                continue

            # Skip if we've seen this key combination before
            if key_values in seen_keys:
                continue

            seen_keys.add(key_values)
            unique_records.append(record)

        # Step 2: Filter against existing records in the database
        with self.get_db() as db:
            filtered_records = []

            # Process in batches to avoid too many individual queries
            for i in range(0, len(unique_records), 100):
                batch = unique_records[i : i + 100]

                # Build a compound query for the whole batch
                query_conditions = []
                for record in batch:
                    record_conditions = []

                    # For each record, check if it has all the required unique fields
                    for field in unique_fields:
                        if field in record and record[field] is not None:
                            record_conditions.append(
                                getattr(self.model_class, field) == record[field]
                            )

                    # Only add conditions if we have valid fields to check
                    if record_conditions:
                        if len(record_conditions) > 1:
                            query_conditions.append(and_(*record_conditions))
                        else:
                            query_conditions.append(record_conditions[0])

                # If we have conditions to check
                if query_conditions:
                    # Get all matching records in one query using SQLModel's select
                    statement = select(self.model_class)
                    if len(query_conditions) > 1:
                        statement = statement.where(or_(*query_conditions))
                    else:
                        statement = statement.where(query_conditions[0])

                    result = db.exec(statement).all()

                    # Create a set of existing record keys
                    existing_keys = set()
                    for existing in result:
                        key_tuple = tuple(
                            getattr(existing, field)
                            for field in unique_fields
                            if hasattr(existing, field)
                        )
                        if all(
                            v is not None for v in key_tuple
                        ):  # Only add if all values are not None
                            existing_keys.add(key_tuple)

                    # Add only records that don't exist in DB
                    for record in batch:
                        record_key = tuple(record.get(field) for field in unique_fields)
                        if None not in record_key and record_key not in existing_keys:
                            filtered_records.append(record)
                else:
                    # If no conditions (e.g., all fields are None), add all records in this batch
                    filtered_records.extend(batch)

            return filtered_records

    def _save_records(self, records: list[dict[str, Any]]) -> int:
        """Save records to database and return number saved."""
        model_instances = [self.model_class(**record) for record in records]

        if not model_instances:
            return 0

        with self.get_db() as db:
            db.add_all(model_instances)
            db.commit()

        return len(model_instances)
