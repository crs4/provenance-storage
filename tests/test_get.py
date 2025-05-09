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

import filecmp
import zipfile

from provstor.get import get_crate, get_file
from provstor.load import load_crate_metadata
from provstor.queries import RDE_QUERY
from provstor.query import run_query


def _load_and_get_rde_id(crate_path):
    crate_url = load_crate_metadata(crate_path)
    qres = run_query(RDE_QUERY, graph_id=crate_url)
    assert len(qres) == 1
    return str(list(qres)[0][0])


def test_get_crate(data_dir, tmpdir):
    crate_path = data_dir / "crate1"
    md_path = crate_path / "ro-crate-metadata.json"
    rde_id = _load_and_get_rde_id(crate_path)
    zip_path = get_crate(rde_id, outdir=tmpdir)
    assert zip_path.name == "crate1.zip"
    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert zipf.namelist() == ["ro-crate-metadata.json"]
        assert zipf.read("ro-crate-metadata.json") == md_path.read_bytes()


def test_get_file(data_dir, tmpdir):
    crate_path = data_dir / "crate1"
    md_path = crate_path / "ro-crate-metadata.json"
    rde_id = _load_and_get_rde_id(crate_path)
    out_md_path = get_file(f"{rde_id}/ro-crate-metadata.json", outdir=tmpdir)
    assert filecmp.cmp(out_md_path, md_path)
