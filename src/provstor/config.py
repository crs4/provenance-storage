# Copyright © 2024-2025 CRS4
#
# This file is part of ProvStor.
#
# ProvStor is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# ProvStor is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ProvStor. If not, see <https://www.gnu.org/licenses/>.

"""\
Configuration file support.

Looks for configuration files in ./provstor.config and
~/.config/provstor.config. If both are present, the corresponding
configurations are merged, and in case of conflicting settings the former
overrides the latter. Note that if the environment variable XDG_CONFIG_HOME is
set and not empty, its value is used instead of ~/.config. See
https://specifications.freedesktop.org/basedir-spec/latest.

Example:

[fuseki]
base_url = http://localhost:3030
dataset = ds

[minio]
store = localhost:9000
user = minio
secret = miniosecret
bucket = crates

[api]
host = 127.0.0.1
port = 8000
"""

from configparser import ConfigParser
from pathlib import Path
import os
import warnings

CONFIG_BASENAME = "provstor.config"


def load_config():
    """Load environment variables in the .env file, if present."""
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        with env_file.open() as f:
            for line in f:
                if not line.startswith("#") and "=" in line:
                    key_value_pair = line.strip().split("=", 1)
                    if len(key_value_pair) == 2:
                        key = key_value_pair[0]
                        value = key_value_pair[1]
                        if key not in os.environ:
                            os.environ[key] = value
                    else:
                        raise ValueError(f"Invalid line in environment file: '{line}' (must contain exactly one '=')"
                                         f"\nContinue to parse the environment variables from the default configuation file...")

def configure():
    """\
    Sets module-level variables according to configuration files. If no
    configuration files are present, the variables are set to the fallback
    values.
    """
    try:
        load_config()
    except:
        raise
    finally:
        CONFIG_FILE_LOCATIONS = [Path.cwd() / CONFIG_BASENAME]
        if homeconf := os.getenv("XDG_CONFIG_HOME"):
            homeconf = Path(homeconf)
            CONFIG_FILE_LOCATIONS.insert(0, homeconf / CONFIG_BASENAME)
        else:
            try:
                HOME = Path.home()
            except RuntimeError as e:
                warnings.warn(f"cannot resolve home directory: {e}")
            else:
                CONFIG_FILE_LOCATIONS.insert(0, HOME / ".config" / CONFIG_BASENAME)
        CONFIG = ConfigParser()
        CONFIG.read(CONFIG_FILE_LOCATIONS)
        g = globals()

        # API Configuration
        g["API_HOST"] = os.getenv("API_HOST", CONFIG.get("api", "host", fallback="0.0.0.0"))
        g["API_PORT"] = int(os.getenv("API_PORT", CONFIG.getint("api", "port", fallback=8000)))

        # Fuseki Configuration
        g["FUSEKI_BASE_URL"] = os.getenv("FUSEKI_BASE_URL", CONFIG.get("fuseki", "base_url", fallback="http://localhost:3030"))
        g["FUSEKI_DATASET"] = os.getenv("FUSEKI_DATASET", CONFIG.get("fuseki", "dataset", fallback="ds"))

        # MinIO Configuration
        g["MINIO_STORE"] = os.getenv("MINIO_STORE", CONFIG.get("minio", "store", fallback="localhost:9000"))
        g["MINIO_USER"] = os.getenv("MINIO_USER", CONFIG.get("minio", "user", fallback="minio"))
        g["MINIO_SECRET"] = os.getenv("MINIO_SECRET", CONFIG.get("minio", "secret", fallback="miniosecret"))
        g["MINIO_BUCKET"] = os.getenv("MINIO_BUCKET", CONFIG.get("minio", "bucket", fallback="crates"))

configure()
