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

from provstor.config import MINIO_STORE, MINIO_BUCKET
from provstor.list import list_graphs


def test_list_graphs(crate_map):
    res = set(list_graphs())
    assert res >= {
        f"http://{MINIO_STORE}/{MINIO_BUCKET}/crate1.zip",
        f"http://{MINIO_STORE}/{MINIO_BUCKET}/crate2.zip",
        f"http://{MINIO_STORE}/{MINIO_BUCKET}/provcrate1.zip",
    }
