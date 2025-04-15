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


from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef

from .constants import (
    FUSEKI_BASE_URL, FUSEKI_DATASET, FUSEKI_UNION_GRAPH,
    MINIO_STORE, MINIO_BUCKET
)


def run_query(query, fuseki_url=None, fuseki_dataset=None, graph=None):
    if not fuseki_url:
        fuseki_url = FUSEKI_BASE_URL
    if not fuseki_dataset:
        fuseki_dataset = FUSEKI_DATASET
    if not graph:
        graph_name = FUSEKI_UNION_GRAPH
    else:
        graph_name = f"http://{MINIO_STORE}/{MINIO_BUCKET}/{graph}.zip"
    store = SPARQLUpdateStore()
    query_endpoint = f"{fuseki_url}/{fuseki_dataset}/sparql"
    store.open((query_endpoint))
    graph = Graph(store, identifier=URIRef(graph_name))
    qres = graph.query(query)
    return qres
