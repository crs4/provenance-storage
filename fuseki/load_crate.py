from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID

store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/ds/query'
update_endpoint = 'http://localhost:3030/ds/update'
store.open((query_endpoint, update_endpoint))
graph = Graph(store, identifier=DATASET_DEFAULT_GRAPH_ID)
graph.parse("crate1/ro-crate-metadata.json")
