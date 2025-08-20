from rdflib.term import URIRef
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
import os

FUSEKI_BASE_URL = os.getenv("FUSEKI_BASE_URL")
FUSEKI_DATASET = os.getenv("FUSEKI_DATASET")
MINIO_STORE = os.getenv("MINIO_STORE")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

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
