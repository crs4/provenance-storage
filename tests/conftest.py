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

from pathlib import Path
import atexit
import shutil
import tempfile

import arcp
import pytest
import requests

from provstor.config import API_HOST, API_PORT


THIS_DIR = Path(__file__).absolute().parent
DATA_DIR_NAME = 'data'


@pytest.fixture(scope="session")
def data_dir():
    return THIS_DIR / DATA_DIR_NAME


@pytest.fixture(scope="session")
def crate_map(data_dir):
    m = {}
    base_api_url = f"http://{API_HOST}:{API_PORT}"
    tmp_dir = Path(tempfile.mkdtemp(prefix="provstor_"))
    atexit.register(shutil.rmtree, tmp_dir)
    response = requests.get(f"{base_api_url}/query/list-graphs/")
    response.raise_for_status()
    existing_crates = {_.rsplit("/", 1)[-1]: _ for _ in response.json()["result"]}
    for c in ["crate1", "crate2", "provcrate1", "proccrate1", "proccrate2"]:
        crate_name = f"{c}.zip"
        crate_path = data_dir / c
        if crate_name not in existing_crates:
            zip_path = shutil.make_archive(tmp_dir / crate_name, 'zip', crate_path)
            with open(zip_path, 'rb') as crate_file:
                response = requests.post(
                    f"{base_api_url}/upload/crate/",
                    files={'crate_path': (crate_name, crate_file, 'application/zip')}
                )
            if response.status_code == 200 and response.json().get('result') == "success":
                crate_url = response.json().get('crate_url')
            else:
                response.raise_for_status()
        else:
            crate_url = existing_crates[crate_name]
        m[c] = {
            "path": crate_path,
            "url": crate_url,
            "rde_id": arcp.arcp_location(crate_url) if crate_url else None
        }
    return m
