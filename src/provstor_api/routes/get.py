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


from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import logging
from urllib.request import urlopen
from urllib.parse import urlsplit
import zipfile
import io

from provstor_api.utils.query import run_query
from provstor_api.utils.queries import (
    CRATE_URL_QUERY, GRAPH_ID_FOR_FILE_QUERY,
    GRAPH_ID_FOR_RESULT_QUERY, WORKFLOW_QUERY, WFRUN_RESULTS_QUERY,
    WFRUN_OBJECTS_QUERY, OBJECTS_FOR_RESULT_QUERY, WFRUN_PARAMS_QUERY
)
from provstor_api.utils.get_utils import fetch_actions_for_result, fetch_objects_for_action, fetch_results_for_action

router = APIRouter()


content_type_map = {
    'zip': 'application/zip',
    'pdf': 'application/pdf',
    'svg': 'image/svg+xml',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'gif': 'image/gif',
}


@router.get("/crate/")
async def get_crate(rde_id: str):
    rde_id = rde_id.rstrip("/") + "/"
    qres = run_query(CRATE_URL_QUERY % rde_id)

    if len(qres) < 1:
        raise HTTPException(status_code=404, detail=f"No crate found for '{rde_id}'")

    crate_url = str(list(qres)[0][0])
    logging.info("Internal crate URL: %s", crate_url)
    file_to_download = crate_url.rsplit("/", 1)[-1]
    logging.info("downloading file: %s", file_to_download)

    with urlopen(crate_url) as response:
        content_type = response.headers.get('Content-Type', 'application/zip')

        return StreamingResponse(
            io.BytesIO(response.read()),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_to_download}",
            }
        )


@router.get("/file/")
async def get_file(file_uri: str):
    res = urlsplit(file_uri)

    if not res.scheme.startswith("arcp"):
        raise HTTPException(status_code=400, detail=f"Unsupported protocol: {res.scheme}")

    rde_id = f"{res.scheme}://{res.netloc}/"
    zip_member = res.path.lstrip("/")
    file_to_download = zip_member.rsplit("/", 1)[-1]
    logging.info("extracting: %s", zip_member)

    rde_id = rde_id.rstrip("/") + "/"
    qres = run_query(CRATE_URL_QUERY % rde_id)
    if len(qres) < 1:
        raise HTTPException(status_code=404, detail=f"No crate found for '{rde_id}'")

    crate_url = str(list(qres)[0][0])
    with urlopen(crate_url) as zip_response:
        zip_data = io.BytesIO(zip_response.read())

        with zipfile.ZipFile(zip_data, "r") as zipf:
            try:
                file_data = zipf.read(zip_member)
                file_ext = file_to_download.rsplit('.', 1)[-1].lower()
                if file_ext in content_type_map:
                    content_type = content_type_map[file_ext]
                else:
                    content_type = 'application/octet-stream'

                return StreamingResponse(
                    io.BytesIO(file_data),
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={file_to_download}",
                    }
                )

            except KeyError:
                raise HTTPException(status_code=404, detail=f"File '{zip_member}' not found in the crate")


@router.get("/graphs-for-file/")
def get_graphs_for_file(file_id: str):
    query_res = run_query(GRAPH_ID_FOR_FILE_QUERY % file_id)
    output = [str(_[0]) for _ in query_res]
    return {"result": output}


@router.get("/graphs-for-result/")
def get_graphs_for_result(result_id: str):
    query_res = run_query(GRAPH_ID_FOR_RESULT_QUERY % result_id)
    output = [str(_[0]) for _ in query_res]
    return {"result": output}


@router.get("/workflow/")
def get_workflow(graph_id: str):
    query_res = run_query(WORKFLOW_QUERY, graph_id=graph_id)
    output = [str(_[0]) for _ in query_res]
    return {"result": output}


@router.get("/run-results/")
def get_run_results(graph_id: str):
    query_res = run_query(WFRUN_RESULTS_QUERY, graph_id=graph_id)
    output = [str(_[0]) for _ in query_res]
    return {"result": output}


@router.get("/run-objects/")
def get_run_objects(graph_id: str):
    query_res = run_query(WFRUN_OBJECTS_QUERY, graph_id=graph_id)
    output = [str(_[0]) for _ in query_res]
    return {"result": output}


@router.get("/objects-for-result/")
def get_objects_for_result(result_id: str):
    query_res = run_query(OBJECTS_FOR_RESULT_QUERY % result_id)
    output = [str(_[0]) for _ in query_res]
    return {"result": output}


@router.get("/actions-for-result/")
def get_actions_for_result(result_id: str):
    output = fetch_actions_for_result(result_id)
    return {"result": output}


@router.get("/objects-for-action/")
def get_objects_for_action(action_id: str):
    output = fetch_objects_for_action(action_id)
    return {"result": output}


@router.get("/results-for-action/")
def get_results_for_action(action_id: str):
    output = fetch_results_for_action(action_id)
    return {"result": output}


@router.get("/run-params/")
def get_run_params(graph_id: str):
    query_res = run_query(WFRUN_PARAMS_QUERY, graph_id=graph_id)
    output = [(str(_.name), str(_.value)) for _ in query_res]
    return {"result": output}
