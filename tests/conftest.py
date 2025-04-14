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

import pytest


THIS_DIR = Path(__file__).absolute().parent
DATA_DIR_NAME = 'data'


# pytest's tmpdir returns a py.path object
@pytest.fixture
def tmpdir(tmpdir):
    return Path(tmpdir)


@pytest.fixture
def data_dir(tmpdir):
    return THIS_DIR / DATA_DIR_NAME
