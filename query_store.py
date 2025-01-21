import argparse
from pathlib import Path

from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef

FUSEKI_BASE_URL = "http://localhost:3030"
FUSEKI_DATASET = "ds"


def main(args):
    query_path = Path(args.query_file)
    if not query_path.is_file():
        raise RuntimeError(f"file {query_path} not found")
    with open(query_path, "rt") as f:
        query = f.read()
    store = SPARQLUpdateStore()
    query_endpoint = f"{args.fuseki_url}/{args.fuseki_dataset}/sparql"
    store.open((query_endpoint))
    # graph = Graph(store, identifier=URIRef("urn:x-arq:DefaultGraph"))
    graph = Graph(store, identifier=URIRef("urn:x-arq:UnionGraph"))
    qres = graph.query(query)
    for row in qres:
        print(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query_file", metavar="QUERY_FILE",
                        help="SPARQL query file")
    parser.add_argument("-u", "--fuseki-url", metavar="STRING",
                        help="Fuseki base url", default=FUSEKI_BASE_URL)
    parser.add_argument("-d", "--fuseki-dataset", metavar="STRING",
                        help="Fuseki dataset", default=FUSEKI_DATASET)
    main(parser.parse_args())
