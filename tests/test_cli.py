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

from click.testing import CliRunner
from provstor.cli import cli


def test_cli_load(data_dir):
    crate1 = data_dir / "crate1"
    runner = CliRunner()
    args = ["load", str(crate1)]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception


def test_cli_query(data_dir):
    query_path = data_dir / "query.txt"
    runner = CliRunner()
    args = ["query", str(query_path)]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
