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

Looks for configuration files in ./provstor.config and ~/.provstor/config. If
both are present, the corresponding configurations are merged, and in case of
conflicting settings the former overrides the latter.

Example:

[fuseki]
base_url = http://localhost:3030
dataset = ds

[minio]
store = localhost:9000
user = minio
secret = miniosecret
bucket = crates
"""

from configparser import ConfigParser
from pathlib import Path
import warnings

CONFIG_FILE_LOCATIONS = [Path.cwd() / "provstor.config"]
try:
    HOME = Path.home()
except RuntimeError as e:
    warnings.warn(f"cannot resolve home directory: {e}")
else:
    CONFIG_FILE_LOCATIONS.insert(0, HOME / ".provstor" / "config")
CONFIG = ConfigParser()
CONFIG.read(CONFIG_FILE_LOCATIONS)

FUSEKI_BASE_URL = CONFIG.get("fuseki", "base_url", fallback="http://localhost:3030")
FUSEKI_DATASET = CONFIG.get("fuseki", "dataset", fallback="ds")
MINIO_STORE = CONFIG.get("minio", "store", fallback="localhost:9000")
MINIO_USER = CONFIG.get("minio", "user", fallback="minio")
MINIO_SECRET = CONFIG.get("minio", "secret", fallback="miniosecret")
MINIO_BUCKET = CONFIG.get("minio", "bucket", fallback="crates")
