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

import shutil

import arcp
from click.testing import CliRunner
import pytest
from provstor.cli import cli
from provstor.constants import MINIO_STORE, MINIO_BUCKET


@pytest.mark.parametrize("zipped", [False, True])
def test_cli_load(data_dir, tmpdir, zipped):
    runner = CliRunner()
    if zipped:
        unzipped_crate = data_dir / "crate2"
        crate = shutil.make_archive(tmpdir / "crate2", "zip", unzipped_crate)
    else:
        crate = data_dir / "crate1"
    args = ["load", str(crate)]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception


def test_cli_query(data_dir):
    query_path = data_dir / "query.txt"
    runner = CliRunner()
    args = ["query", str(query_path)]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception


def test_cli_get_crate(data_dir, tmpdir):
    runner = CliRunner()
    crate_name = "crate1"
    crate = data_dir / crate_name
    args = ["load", str(crate)]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    crate_url = f"http://{MINIO_STORE}/{MINIO_BUCKET}/{crate_name}.zip"
    rde_id = arcp.arcp_location(crate_url)
    args = ["get-crate", rde_id, "-o", tmpdir]
    print("args:", args)
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert (tmpdir / f"{crate_name}.zip").is_file()
