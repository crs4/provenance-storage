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

from rdflib.term import Literal, URIRef

from provstor.constants import MINIO_STORE, MINIO_BUCKET
from provstor.load import load_crate_metadata
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

    def check_results(exp_results, graph_id=None):
        qres = run_query(PERSON_QUERY, graph_id=graph_id)
        assert list(qres) == exp_results

    for c in "crate1", "crate2":
        load_crate_metadata(data_dir / c)

    check_results([
        (URIRef("https://orcid.org/0000-0001-8271-5429"), Literal("Simone Leo")),
        (URIRef("https://orcid.org/0000-0002-1825-0097"), Literal("Josiah Carberry"))
    ])
    check_results([
        (URIRef("https://orcid.org/0000-0001-8271-5429"), Literal("Simone Leo"))
    ], graph_id="crate1")
    check_results([
        (URIRef("https://orcid.org/0000-0002-1825-0097"), Literal("Josiah Carberry"))
    ], graph_id=f"http://{MINIO_STORE}/{MINIO_BUCKET}/crate2.zip")
