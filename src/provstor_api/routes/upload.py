from fastapi import APIRouter, UploadFile, HTTPException
import json
import logging
import tempfile
import zipfile
import os
import arcp
from minio import Minio
from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef, Literal

from utils.queries import RDE_QUERY
from config import (
    MINIO_STORE, MINIO_USER, MINIO_SECRET, MINIO_BUCKET,
    FUSEKI_DATASET, FUSEKI_BASE_URL,
)

router = APIRouter()

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


@router.post("/crate/")
async def load_crate_metadata(crate_path: UploadFile):
    if crate_path.content_type != "application/zip":
        raise HTTPException(status_code=415, detail="crate_path must be a zip file.")

    try:
        content = await crate_path.read()

        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_zip_path = os.path.join(tmp_dir, crate_path.filename)

            with open(tmp_zip_path, 'wb') as f:
                f.write(content)  # type: ignore

            metadata_filename = "ro-crate-metadata.json"
            metadata_path = None

            with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                for zip_info in zip_ref.infolist():
                    if os.path.basename(zip_info.filename) == metadata_filename:
                        # Check if the file is too large
                        if zip_info.file_size > 50_000_000:
                            raise HTTPException(status_code=413, detail="Metadata file exceeds size limit (50 MB)")

                        metadata_path = os.path.join(tmp_dir, metadata_filename)
                        with zip_ref.open(zip_info) as src, open(metadata_path, 'wb') as dst:
                            dst.write(src.read())  # type: ignore

                        logging.info("Extracted metadata file: %s", metadata_path)
                        break

            if not metadata_path:
                raise HTTPException(status_code=404, detail="ro-crate-metadata.json not found in the zip file")

            client = Minio(MINIO_STORE, MINIO_USER, MINIO_SECRET, secure=False)
            if not client.bucket_exists(MINIO_BUCKET):
                client.make_bucket(MINIO_BUCKET)
                logging.info('created bucket "%s"', MINIO_BUCKET)
                client.set_bucket_policy(MINIO_BUCKET, json.dumps(MINIO_BUCKET_POLICY))

            await crate_path.seek(0)  # Reset file pointer to the beginning
            client.put_object(
                MINIO_BUCKET,
                crate_path.filename,
                crate_path.file,
                length=-1,
                part_size=50 * 1024 * 1024
            )

            crate_url = f"http://{MINIO_STORE}/{MINIO_BUCKET}/{crate_path.filename}"
            logging.info("Crate URL: %s", crate_url)

            store = SPARQLUpdateStore()
            query_endpoint = f"{FUSEKI_BASE_URL}/{FUSEKI_DATASET}/sparql"
            update_endpoint = f"{FUSEKI_BASE_URL}/{FUSEKI_DATASET}/update"
            store.open((query_endpoint, update_endpoint))
            graph = Graph(store, identifier=URIRef(crate_url))
            loc = arcp.arcp_location(crate_url)
            logging.info("ARCP location: %s", loc)
            graph.parse(metadata_path, publicID=loc)
            # store crate url as root data entity "url"
            qres = graph.query(RDE_QUERY)
            if not qres:
                raise HTTPException(status_code=500, detail="Failed to store crate metadata in the graph")

            assert len(qres) == 1
            rde = list(qres)[0][0]
            graph.add((rde, URIRef("http://schema.org/url"), Literal(crate_url)))
            return {"result": "success", "crate_url": crate_url}

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
