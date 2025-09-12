# Copyright © 2024-2025 CRS4
# Copyright © 2025 BSC
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


import os


DEFAULT_ENV_VARS = {
    "MINIO_STORE": "minio:9000",
    "MINIO_USER": "minio",
    "MINIO_SECRET": "miniosecret",
    "MINIO_BUCKET": "crates",
    "FUSEKI_BASE_URL": "http://fuseki:3030",
    "FUSEKI_DATASET": "ds",
    "ALLOWED_ORIGINS": "*",
}


def load_env_vars():
    """\
    Sets module-level variables according to environment variables.
    """
    g = globals()
    for key, value in DEFAULT_ENV_VARS.items():
        g[key] = os.environ.get(key, value)


load_env_vars()
