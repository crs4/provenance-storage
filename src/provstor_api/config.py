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

from pydantic_settings import BaseSettings


# Pydantic reads the environment variables in a case-insensitive way
class Settings(BaseSettings):
    minio_store: str = "minio:9000"
    minio_user: str = "minio"
    minio_secret: str = "miniosecret"
    minio_bucket: str = "crates"
    fuseki_base_url: str = "http://fuseki:3030"
    fuseki_dataset: str = "ds"
    allowed_origins: str = "*"
    dev_mode: bool = False


settings = Settings()
