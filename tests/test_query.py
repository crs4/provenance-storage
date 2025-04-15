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
from rdflib.term import Literal, URIRef

from provstor.cli import cli
from provstor.query import run_query

PERSON_QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT ?person ?name
WHERE {
  ?person a schema:Person .
  ?person schema:name ?name
}
"""


def test_run_query(data_dir, tmpdir):
    runner = CliRunner()
    crate_name = "crate2"
    crate = data_dir / crate_name
    args = ["load", str(crate)]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    qres = run_query(PERSON_QUERY)
    person_ids = set(row.person for row in qres)
    person_names = set(row.name for row in qres)
    assert URIRef("https://orcid.org/0000-0002-1825-0097") in person_ids
    assert Literal("Josiah Carberry") in person_names
