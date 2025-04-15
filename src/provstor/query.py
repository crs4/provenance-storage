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

from .constants import FUSEKI_BASE_URL, FUSEKI_DATASET


def run_query(query_path, fuseki_url=None, fuseki_dataset=None):
    if not fuseki_url:
        fuseki_url = FUSEKI_BASE_URL
    if not fuseki_dataset:
        fuseki_dataset = FUSEKI_DATASET
    if not query_path.is_file():
        raise RuntimeError(f"file {query_path} not found")
    with open(query_path, "rt") as f:
        query = f.read()
    store = SPARQLUpdateStore()
    query_endpoint = f"{fuseki_url}/{fuseki_dataset}/sparql"
    store.open((query_endpoint))
    # graph = Graph(store, identifier=URIRef("urn:x-arq:DefaultGraph"))
    graph = Graph(store, identifier=URIRef("urn:x-arq:UnionGraph"))
    qres = graph.query(query)
    return qres
