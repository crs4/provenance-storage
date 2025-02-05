import argparse
import json
import shutil
import tempfile
from pathlib import Path

import arcp
from minio import Minio
from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef


MINIO_STORE = "localhost:9000"
MINIO_USER = "minio"
MINIO_SECRET = "miniosecret"
MINIO_BUCKET = "crates"
# anonymous read-only policy, see https://github.com/minio/minio-py/blob/88f4244fe89fb9f23de4f183bdf79524c712deaa/examples/set_bucket_policy.py#L27
MINIO_BUCKET_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Resource": f"arn:aws:s3:::{MINIO_BUCKET}",
        },
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{MINIO_BUCKET}/*",
        },
    ],
}

FUSEKI_BASE_URL = "http://localhost:3030"
FUSEKI_DATASET = "ds"


def upload_crate_to_minio(crate_path, crate_name=None, bucket=MINIO_BUCKET):
    if crate_name is None:
        crate_name = crate_path.name
    client = Minio(MINIO_STORE, MINIO_USER, MINIO_SECRET, secure=False)
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f'created bucket "{bucket}"')
        client.set_bucket_policy(MINIO_BUCKET, json.dumps(MINIO_BUCKET_POLICY))
    tmp_dir = Path(tempfile.mkdtemp(prefix="load_crate_"))
    archive = shutil.make_archive(tmp_dir/crate_name, "zip", crate_path)
    zipped_crate_name = f"{crate_name}.zip"
    client.fput_object(bucket, zipped_crate_name, archive)
    crate_url = f"http://{MINIO_STORE}/{MINIO_BUCKET}/{zipped_crate_name}"
    print("Crate URL:", crate_url)
    return crate_url


def main(args):
    crate_path = Path(args.crate)
    crate_url = upload_crate_to_minio(crate_path)
    metadata_path = crate_path / "ro-crate-metadata.json"
    if not metadata_path.is_file():
        raise RuntimeError(f"file {metadata_path} not found")
    store = SPARQLUpdateStore()
    query_endpoint = f"{args.fuseki_url}/{args.fuseki_dataset}/sparql"
    update_endpoint = f"{args.fuseki_url}/{args.fuseki_dataset}/update"
    store.open((query_endpoint, update_endpoint))
    graph = Graph(store, identifier=URIRef(crate_url))
    loc = arcp.arcp_location(crate_url)
    print("ARCP location:", loc)
    graph.parse(metadata_path, publicID=loc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("crate", metavar="CRATE", help="RO-Crate")
    parser.add_argument("-u", "--fuseki-url", metavar="STRING",
                        help="Fuseki base url", default=FUSEKI_BASE_URL)
    parser.add_argument("-d", "--fuseki-dataset", metavar="STRING",
                        help="Fuseki dataset", default=FUSEKI_DATASET)
    main(parser.parse_args())
