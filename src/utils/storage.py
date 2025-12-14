import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def get_database_path(schema: str) -> Path:
    """
    Get the path for a database schema.

    Args:
        schema: Schema name (e.g., "tools/repo/get_repository_info")

    Returns:
        Path object for the database file
    """
    base_dir = Path(__file__).parent.parent.parent / "database"
    schema_path = base_dir / schema
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    return schema_path.with_suffix(".json")


def save_to_database(schema: str, data: Dict[str, Any]) -> str:
    """
    Save data to JSON database.

    Args:
        schema: Schema name (e.g., "tools/repo/get_repository_info")
        data: Data to save

    Returns:
        Path to the saved file
    """
    file_path = get_database_path(schema)

    # Add timestamp to data
    data_with_timestamp = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }

    with open(file_path, "w") as f:
        json.dump(data_with_timestamp, f, indent=2)

    return str(file_path)


def load_from_database(schema: str) -> Dict[str, Any]:
    """
    Load data from JSON database.

    Args:
        schema: Schema name (e.g., "tools/repo/get_repository_info")

    Returns:
        Loaded data, or empty dict if file doesn't exist
    """
    file_path = get_database_path(schema)

    if not file_path.exists():
        return {}

    with open(file_path, "r") as f:
        return json.load(f)
