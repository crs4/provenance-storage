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
    for row in qres:
        print(row)
