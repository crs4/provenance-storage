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

from provstor.load import load_crate_metadata


THIS_DIR = Path(__file__).absolute().parent
DATA_DIR_NAME = 'data'


@pytest.fixture(scope="session")
def data_dir():
    return THIS_DIR / DATA_DIR_NAME


@pytest.fixture(scope="session")
def crate_map(data_dir):
    m = {}
    for c in "crate1", "crate2", "provcrate1", "proccrate1":
        crate_path = data_dir / c
        crate_url = load_crate_metadata(crate_path)
        m[c] = {
            "path": crate_path,
            "url": crate_url,
            "rde_id": arcp.arcp_location(crate_url)
        }
    return m
