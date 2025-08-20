import os
from pathlib import Path


default_env_vars = {
    "MINIO_STORE": "localhost:9000",
    "MINIO_USER": "minioadmin",
    "MINIO_SECRET": "minioadmin",
    "MINIO_BUCKET": "provstor-bucket",
    "FUSEKI_BASE_URL": "http://localhost:3030",
    "FUSEKI_DATASET": "ds",
    "PROVSTOR_API_HOST": "0.0.0.0",
    "PROVSTOR_API_PORT": "8000"
}


def load_env():
    """Load environment variables in the .env file, if present."""
    env_file = Path(__file__).parent.parent.parent / ".env"

    def handle_error(msg):
        """Rollback loaded vars and raise error with consistent message."""
        # Rollback loaded variables to default values
        for var in loaded_variables:
            os.environ.pop(var, None)
        raise ValueError(f"{msg}\nUsing the default values...")

    if env_file.exists():
        with env_file.open() as f:
            loaded_variables = []
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if line.startswith("#") or not line:
                    continue

                if not "=" in line:
                    handle_error(f"Line {line_num}: '{line}' (must contain exactly one '=')")

                key_value_pair = line.strip().split("=")
                if len(key_value_pair) == 2:
                    key = key_value_pair[0].strip()
                    value = key_value_pair[1].strip()
                else:
                    handle_error(f"Line {line_num}: '{line}' (must contain exactly one '=')")

                # Check if the key is in the default environment variables
                if key not in default_env_vars:
                    handle_error(f"Line {line_num}: Unknown key '{key}'")

                if ' ' in value:
                    handle_error(f"Line {line_num}: Value contains spaces: '{value}'")

                if not value:
                    handle_error(f"Line {line_num}: Empty value for key '{key}'")

                # Skip if already in os.environ
                if key in os.environ:
                    continue

                os.environ[key] = value
                loaded_variables.append(key)
    else:
        raise FileNotFoundError(f"Environment file '{env_file}' not found."
                                f"\nUsing the default values...")


def load_default_env():
    """Load default environment variables if .env file is not present."""
    for key, value in default_env_vars.items():
        if key not in os.environ:
            os.environ[key] = value


def load_env_vars():
    """\
    Sets module-level variables according to configuration files. If no
    configuration files are present, the variables are set to the fallback
    values.
    """
    try:
        load_env()
    except Exception as e:
        print(f"Error loading environment variables: {e}")
        load_default_env()