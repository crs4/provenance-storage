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

from pathlib import Path

import arcp
import pytest
import requests

from provstor.config import (
    PROVSTOR_API_ENDPOINT_HOST, PROVSTOR_API_ENDPOINT_PORT
)


THIS_DIR = Path(__file__).absolute().parent
DATA_DIR_NAME = 'data'


@pytest.fixture(scope="session")
def data_dir():
    return THIS_DIR / DATA_DIR_NAME


@pytest.fixture(scope="session")
def crate_map(data_dir):
    m = {}
    api_url = F"http://{PROVSTOR_API_ENDPOINT_HOST}:{PROVSTOR_API_ENDPOINT_PORT}/upload/crate/"
    for c in ["crate1", "crate2", "provcrate1", "proccrate1", "proccrate2"]:
        crate_path = data_dir / c
        zip_path = crate_path.with_suffix(".zip")
        if not zip_path.exists():
            import shutil
            shutil.make_archive(str(crate_path), 'zip', str(crate_path))
        with open(zip_path, 'rb') as crate_file:
            response = requests.post(api_url, files={'crate_path': (zip_path.name, crate_file, 'application/zip')})
        if response.status_code == 200 and response.json().get('result') == "success":
            crate_url = response.json().get('crate_url')
        else:
            crate_url = None
        m[c] = {
            "path": crate_path,
            "url": crate_url,
            "rde_id": arcp.arcp_location(crate_url) if crate_url else None
        }
    return m
