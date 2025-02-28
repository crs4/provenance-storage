from pathlib import Path
from shutil import copyfileobj
from urllib.request import urlopen

from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef

from .constants import FUSEKI_BASE_URL, FUSEKI_DATASET

QUERY = """\
PREFIX schema: <http://schema.org/>

SELECT ?crate_url
WHERE {
  <%s> schema:url ?crate_url
}
"""


def get_crate(rde_id, fuseki_url=None, fuseki_dataset=None, outdir=None):
    if not fuseki_url:
        fuseki_url = FUSEKI_BASE_URL
    if not fuseki_dataset:
        fuseki_dataset = FUSEKI_DATASET
    if outdir is None:
        outdir = Path.cwd()
    rde_id = rde_id.rstrip("/") + "/"
    query = QUERY % rde_id
    store = SPARQLUpdateStore()
    query_endpoint = f"{fuseki_url}/{fuseki_dataset}/sparql"
    store.open((query_endpoint))
    graph = Graph(store, identifier=URIRef("urn:x-arq:UnionGraph"))
    qres = graph.query(query)
    assert len(qres) >= 1
    crate_url = str(list(qres)[0][0])
    print("crate URL:", crate_url)
    out_path = outdir / crate_url.rsplit("/", 1)[-1]
    print("downloading to:", out_path)
    outdir.mkdir(parents=True, exist_ok=True)
    with urlopen(crate_url) as response, out_path.open("wb") as f:
        copyfileobj(response, f)
    return out_path
