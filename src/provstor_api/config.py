import os
from pathlib import Path


DEFAULT_ENV_VARS = {
    "MINIO_STORE": "minio:9000",
    "MINIO_USER": "minio",
    "MINIO_SECRET": "miniosecret",
    "MINIO_BUCKET": "crates",
    "FUSEKI_BASE_URL": "http://fuseki:3030",
    "FUSEKI_DATASET": "ds",
    "PROVSTOR_API_HOST": "0.0.0.0",
    "PROVSTOR_API_PORT": "8000"
}


def load_env():
    """Load environment variables in the .env file, if present."""
    env_file = Path(__file__).parent.parent.parent / ".env.test"

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

                # If it's not a comment, check that it contains exactly one '='
                if not "=" in line:
                    handle_error(f"Line {line_num}: '{line}' (must contain exactly one '=')")

                key_value_pair = line.strip().split("=")
                # Check that it splits into exactly two parts
                if len(key_value_pair) == 2:
                    key = key_value_pair[0].strip()
                    value = key_value_pair[1].strip()
                else:
                    handle_error(f"Line {line_num}: '{line}' (must contain exactly one '=')")

                # Validate key and value
                if ' ' in key or key == '':
                    handle_error(f"Line {line_num}: Bad key: '{key}' (must not contain spaces or be empty)")
                if ' ' in value or value == '':
                    handle_error(f"Line {line_num}: Bad value: '{value}' (must not contain spaces or be empty)")

                # Skip if already in os.environ
                if key in os.environ:
                    continue

                os.environ[key] = value
                loaded_variables.append(key)
    else:
        raise FileNotFoundError(f"Environment file '{env_file}' not found."
                                f"\nUsing the default values...")

    # Check if all default environment variables are set
    if len(set(os.environ.keys()).intersection(DEFAULT_ENV_VARS.keys())) != len(DEFAULT_ENV_VARS.keys()):
        handle_error("Not all default environment variables are set in the .env file.")

    return loaded_variables


def load_default_env():
    """Load default environment variables if .env file is not present."""
    for key, value in DEFAULT_ENV_VARS.items():
        if key not in os.environ:
            os.environ[key] = value
        else:
            print(f"Environment variable '{key}' already set to '{os.environ[key]}', skipping default value.")


def load_env_vars():
    """\
    Sets module-level variables according to configuration files. If no
    configuration files are present, the variables are set to the fallback
    values.
    """
    try:
        env_vars = load_env()
    except Exception as e:
        print(f"Error loading environment variables: {e}")
        load_default_env()
        env_vars = DEFAULT_ENV_VARS.keys()
    g = globals()
    for key in env_vars:
        g[key] = os.getenv(key)

load_env_vars()
