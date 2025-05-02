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


from pathlib import Path
from shutil import copyfileobj
from urllib.parse import urlsplit
from urllib.request import urlopen
import logging
import tempfile
import shutil
import zipfile

from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef

from .constants import FUSEKI_BASE_URL, FUSEKI_DATASET, FUSEKI_UNION_GRAPH
from .queries import (
    GRAPH_ID_FOR_FILE_QUERY,
    RUN_RESULTS_QUERY,
    RUN_OBJECTS_QUERY
)

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
    graph = Graph(store, identifier=URIRef(FUSEKI_UNION_GRAPH))
    qres = graph.query(query)
    assert len(qres) >= 1
    crate_url = str(list(qres)[0][0])
    logging.info("crate URL: %s", crate_url)
    out_path = outdir / crate_url.rsplit("/", 1)[-1]
    logging.info("downloading to: %s", out_path)
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
    logging.info("extracting: %s", zip_member)
    with zipfile.ZipFile(zip_path, "r") as zipf:
        out_path = zipf.extract(zip_member, path=outdir)
    shutil.rmtree(zip_dir)
    return Path(out_path)


def get_graph_id(file_id, fuseki_url=None, fuseki_dataset=None):
    if not fuseki_url:
        fuseki_url = FUSEKI_BASE_URL
    if not fuseki_dataset:
        fuseki_dataset = FUSEKI_DATASET
    query = GRAPH_ID_FOR_FILE_QUERY % file_id
    store = SPARQLUpdateStore()
    query_endpoint = f"{fuseki_url}/{fuseki_dataset}/sparql"
    store.open((query_endpoint))
    graph = Graph(store, identifier=URIRef(FUSEKI_UNION_GRAPH))
    qres = graph.query(query)
    assert len(qres) >= 1
    graph_id = str(list(qres)[0][0])
    return graph_id


def get_run_results(graph_id, fuseki_url=None, fuseki_dataset=None):
    if not fuseki_url:
        fuseki_url = FUSEKI_BASE_URL
    if not fuseki_dataset:
        fuseki_dataset = FUSEKI_DATASET
    query = RUN_RESULTS_QUERY
    store = SPARQLUpdateStore()
    query_endpoint = f"{fuseki_url}/{fuseki_dataset}/sparql"
    store.open((query_endpoint))
    graph = Graph(store, identifier=URIRef(graph_id))
    qres = graph.query(query)
    return (str(_[0]) for _ in qres)


def get_run_objects(graph_id, fuseki_url=None, fuseki_dataset=None):
    if not fuseki_url:
        fuseki_url = FUSEKI_BASE_URL
    if not fuseki_dataset:
        fuseki_dataset = FUSEKI_DATASET
    query = RUN_OBJECTS_QUERY
    store = SPARQLUpdateStore()
    query_endpoint = f"{fuseki_url}/{fuseki_dataset}/sparql"
    store.open((query_endpoint))
    graph = Graph(store, identifier=URIRef(graph_id))
    qres = graph.query(query)
    return (str(_[0]) for _ in qres)
