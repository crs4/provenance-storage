from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/ds/query'
store.open((query_endpoint))
graph = Graph(store)

QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT ?name
WHERE {
  ?person a schema:Person .
  ?person schema:name ?name
}
"""

qres = graph.query(QUERY)
for row in qres:
    print(f"Author: {row.name}")
