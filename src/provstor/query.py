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


from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef

from .config import (
    FUSEKI_BASE_URL, FUSEKI_DATASET,
    MINIO_STORE, MINIO_BUCKET
)


def run_query(query, graph_id=None):
    store = SPARQLUpdateStore()
    query_endpoint = f"{FUSEKI_BASE_URL}/{FUSEKI_DATASET}/sparql"
    store.open(query_endpoint)
    if graph_id:
        if not graph_id.startswith("http://"):
            graph_id = f"http://{MINIO_STORE}/{MINIO_BUCKET}/{graph_id}.zip"
        graph_id = URIRef(graph_id)
    qres = store.query(query, queryGraph=graph_id)
    return qres
