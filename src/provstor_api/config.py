# Copyright © 2024-2026 CRS4
# Copyright © 2025-2026 BSC
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

from pydantic_settings import BaseSettings


# Pydantic reads the environment variables in a case-insensitive way
class Settings(BaseSettings):
    seaweedfs_store: str = "seaweedfs-s3:8333"
    seaweedfs_filer: str = "seaweedfs-s3:8888"
    seaweedfs_bucket: str = "crates"
    seaweedfs_user: str = "admin"
    seaweedfs_access_key: str = "admin_access_key"
    seaweedfs_secret_key: str = "admin_secret_key"
    fuseki_base_url: str = "http://fuseki:3030"
    fuseki_dataset: str = "ds"
    cors_allowed_origins: str = ""
    dev_mode: bool = False


settings = Settings()
