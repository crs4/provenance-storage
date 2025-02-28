from pathlib import Path
from shutil import copyfileobj
from urllib.parse import urlsplit
from urllib.request import urlopen
import tempfile
import shutil
import zipfile

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


def get_file(file_uri, fuseki_url=None, fuseki_dataset=None, outdir=None):
    if not fuseki_url:
        fuseki_url = FUSEKI_BASE_URL
    if not fuseki_dataset:
        fuseki_dataset = FUSEKI_DATASET
    if outdir is None:
        outdir = Path.cwd()
    outdir.mkdir(parents=True, exist_ok=True)
    if file_uri.startswith("http"):
        out_path = outdir / file_uri.rsplit("/", 1)[-1]
        with urlopen(file_uri) as response, out_path.open("wb") as f:
            copyfileobj(response, f)
        return out_path
    elif not file_uri.startswith("arcp"):
        raise ValueError(f"{file_uri}: unsupported protocol")
    res = urlsplit(file_uri)
    rde_id = f"{res.scheme}://{res.netloc}/"
    zip_dir = Path(tempfile.mkdtemp())
    zip_path = get_crate(
        rde_id,
        fuseki_url=fuseki_url,
        fuseki_dataset=fuseki_dataset,
        outdir=zip_dir
    )
    zip_member = res.path.lstrip("/")
    print("extracting:", zip_member)
    with zipfile.ZipFile(zip_path, "r") as zipf:
        out_path = zipf.extract(zip_member, path=outdir)
    shutil.rmtree(zip_dir)
    return Path(out_path)
