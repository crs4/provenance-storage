import json
import shutil
import tempfile
from pathlib import Path

import arcp
from minio import Minio
from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef, Literal

from .constants import (
    MINIO_STORE, MINIO_USER, MINIO_SECRET, MINIO_BUCKET, MINIO_BUCKET_POLICY,
    FUSEKI_BASE_URL, FUSEKI_DATASET
)
from .queries import RDE_QUERY


def upload_crate_to_minio(crate_path, crate_name=None, bucket=MINIO_BUCKET):
    if crate_name is None:
        crate_name = crate_path.name
    client = Minio(MINIO_STORE, MINIO_USER, MINIO_SECRET, secure=False)
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f'created bucket "{bucket}"')
        client.set_bucket_policy(MINIO_BUCKET, json.dumps(MINIO_BUCKET_POLICY))
    tmp_dir = Path(tempfile.mkdtemp(prefix="load_crate_"))
    archive = shutil.make_archive(tmp_dir / crate_name, "zip", crate_path)
    zipped_crate_name = f"{crate_name}.zip"
    client.fput_object(bucket, zipped_crate_name, archive)
    crate_url = f"http://{MINIO_STORE}/{MINIO_BUCKET}/{zipped_crate_name}"
    print("Crate URL:", crate_url)
    return crate_url


def load_crate_metadata(crate_path, fuseki_url=None, fuseki_dataset=None):
    crate_url = upload_crate_to_minio(crate_path)
    if not fuseki_url:
        fuseki_url = FUSEKI_BASE_URL
    if not fuseki_dataset:
        fuseki_dataset = FUSEKI_DATASET
    metadata_path = crate_path / "ro-crate-metadata.json"
    if not metadata_path.is_file():
        raise RuntimeError(f"file {metadata_path} not found")
    store = SPARQLUpdateStore()
    query_endpoint = f"{fuseki_url}/{fuseki_dataset}/sparql"
    update_endpoint = f"{fuseki_url}/{fuseki_dataset}/update"
    store.open((query_endpoint, update_endpoint))
    graph = Graph(store, identifier=URIRef(crate_url))
    loc = arcp.arcp_location(crate_url)
    print("ARCP location:", loc)
    graph.parse(metadata_path, publicID=loc)
    # store crate url as root data entity "url"
    qres = graph.query(RDE_QUERY)
    assert len(qres) == 1
    rde = list(qres)[0][0]
    graph.add((rde, URIRef("http://schema.org/url"), Literal(crate_url)))
