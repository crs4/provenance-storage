import argparse
from pathlib import Path

from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef


FUSEKI_BASE_URL = "http://localhost:3030"
FUSEKI_DATASET = "ds"


def main(args):
    crate_path = Path(args.crate)
    metadata_path = crate_path / "ro-crate-metadata.json"
    if not metadata_path.is_file():
        raise RuntimeError(f"file {metadata_path} not found")
    store = SPARQLUpdateStore()
    query_endpoint = f"{args.fuseki_url}/{args.fuseki_dataset}/sparql"
    update_endpoint = f"{args.fuseki_url}/{args.fuseki_dataset}/update"
    store.open((query_endpoint, update_endpoint))
    graph = Graph(store, identifier=URIRef(crate_path.name))
    graph.parse(metadata_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("crate", metavar="CRATE", help="RO-Crate")
    parser.add_argument("-u", "--fuseki-url", metavar="STRING",
                        help="Fuseki base url", default=FUSEKI_BASE_URL)
    parser.add_argument("-d", "--fuseki-dataset", metavar="STRING",
                        help="Fuseki dataset", default=FUSEKI_DATASET)
    main(parser.parse_args())
