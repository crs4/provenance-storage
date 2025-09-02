from rdflib.term import URIRef
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

from config import (
    DOCKER_FUSEKI_BASE_URL, FUSEKI_DATASET,
    DOCKER_MINIO_STORE, MINIO_BUCKET
)


def run_query(query, graph_id=None):
    store = SPARQLUpdateStore()
    query_endpoint = f"{DOCKER_FUSEKI_BASE_URL}/{FUSEKI_DATASET}/sparql"
    store.open(query_endpoint)
    if graph_id:
        if not graph_id.startswith("http://"):
            graph_id = f"http://{DOCKER_MINIO_STORE}/{MINIO_BUCKET}/{graph_id}.zip"
        graph_id = URIRef(graph_id)
    qres = store.query(query, queryGraph=graph_id)
    return qres
