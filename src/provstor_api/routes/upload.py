# Copyright © 2024-2026 CRS4
# Copyright © 2025-2026 BSC
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


from fastapi import APIRouter, UploadFile, HTTPException
import logging
import tempfile
import zipfile
import os
import arcp
import boto3
from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef, Literal

from provstor_api.utils.queries import RDE_QUERY, INSERT_QUERY
from provstor_api.utils.query import run_query
from provstor_api.config import settings

router = APIRouter()


EXTERNAL_RESULTS_QUERY = """\
PREFIX schema: <http://schema.org/>
SELECT ?f ?c
WHERE {
  ?f a ?c .
  { ?f a schema:MediaObject } UNION { ?f a schema:Dataset } .
  FILTER(STRSTARTS(STR(?f), "file:/")) .
  ?a a schema:CreateAction .
  ?a schema:result ?f .
}
"""


@router.post("/crate/")
async def load_crate_metadata(crate_path: UploadFile):
    if crate_path.content_type != "application/zip":
        raise HTTPException(status_code=415, detail="crate_path must be a zip file.")

    content = await crate_path.read()

    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    crate_url = f"http://{settings.seaweedfs_filer}/buckets/{settings.seaweedfs_bucket}/{crate_path.filename}"
    logging.info("Crate URL: %s", crate_url)
    loc = arcp.arcp_location(crate_url)
    logging.info("ARCP location: %s", loc)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_zip_path = os.path.join(tmp_dir, crate_path.filename)

        with open(tmp_zip_path, 'wb') as f:
            f.write(content)  # type: ignore

        metadata_filename = "ro-crate-metadata.json"
        metadata_path = None

        with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                if os.path.basename(zip_info.filename) == metadata_filename:
                    if zip_info.file_size > 50_000_000:
                        raise HTTPException(status_code=413, detail="Metadata file exceeds size limit (50 MB)")

                    metadata_path = os.path.join(tmp_dir, metadata_filename)
                    with zip_ref.open(zip_info) as src, open(metadata_path, 'wb') as dst:
                        dst.write(src.read())  # type: ignore

                    logging.info("Extracted metadata file: %s", metadata_path)
                    break

        if not metadata_path:
            raise HTTPException(status_code=422, detail="ro-crate-metadata.json not found in the zip file")

        local_graph = Graph()
        local_graph.parse(metadata_path, publicID=loc)
        qres = local_graph.query(EXTERNAL_RESULTS_QUERY)
        new_results = set(str(r[0]) for r in qres)
        qres = run_query(EXTERNAL_RESULTS_QUERY)
        existing_results = set(str(r[0]) for r in qres)
        common_results = new_results & existing_results
        if common_results:
            raise HTTPException(status_code=422, detail=f"these results already exist: {common_results}")
        # store crate url as root data entity "url"
        qres = local_graph.query(RDE_QUERY)
        if not qres:
            raise HTTPException(status_code=500, detail="Failed to store crate metadata in the graph")
        assert len(qres) == 1
        rde = list(qres)[0][0]
        local_graph.add((rde, URIRef("http://schema.org/url"), Literal(crate_url)))
        metadata = local_graph.serialize(format="nt")
        if isinstance(metadata, bytes):
            metadata = metadata.decode()

        client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.seaweedfs_store}",
            aws_access_key_id=settings.seaweedfs_access_key,
            aws_secret_access_key=settings.seaweedfs_secret_key,
        )
        try:
            client.create_bucket(Bucket=settings.seaweedfs_bucket)
        except client.exceptions.BucketAlreadyExists:
            pass
        else:
            logging.info('created bucket "%s"', settings.seaweedfs_bucket)

        await crate_path.seek(0)
        client.put_object(
            Bucket=settings.seaweedfs_bucket,
            Key=crate_path.filename,
            Body=crate_path.file,
        )

        try:
            store = SPARQLUpdateStore()
            query_endpoint = f"{settings.fuseki_base_url}/{settings.fuseki_dataset}/sparql"
            update_endpoint = f"{settings.fuseki_base_url}/{settings.fuseki_dataset}/update"
            store.open((query_endpoint, update_endpoint))
            graph = Graph(store, identifier=URIRef(crate_url))
            graph.update(INSERT_QUERY % metadata)
        except Exception as e:
            client.delete_object(
                Bucket=settings.seaweedfs_bucket,
                Key=crate_path.filename,
            )
            raise HTTPException(status_code=500, detail=f"Failed to upload metadata to the store: {e}")
        return {"result": "success", "crate_url": crate_url}
