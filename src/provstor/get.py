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

from .queries import (
    CRATE_URL_QUERY,
    GRAPH_ID_FOR_FILE_QUERY,
    GRAPH_ID_FOR_RESULT_QUERY,
    WORKFLOW_QUERY,
    WFRUN_RESULTS_QUERY,
    WFRUN_OBJECTS_QUERY,
    WFRUN_PARAMS_QUERY
)
from .query import run_query


def get_crate(rde_id, outdir=None):
    if outdir is None:
        outdir = Path.cwd()
    else:
        outdir.mkdir(parents=True, exist_ok=True)
    rde_id = rde_id.rstrip("/") + "/"
    qres = run_query(CRATE_URL_QUERY % rde_id)
    assert len(qres) >= 1
    crate_url = str(list(qres)[0][0])
    logging.info("crate URL: %s", crate_url)
    out_path = outdir / crate_url.rsplit("/", 1)[-1]
    logging.info("downloading to: %s", out_path)
    with urlopen(crate_url) as response, out_path.open("wb") as f:
        copyfileobj(response, f)
    return out_path


def get_file(file_uri, outdir=None):
    if outdir is None:
        outdir = Path.cwd()
    else:
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
    zip_path = get_crate(rde_id, outdir=zip_dir)
    zip_member = res.path.lstrip("/")
    logging.info("extracting: %s", zip_member)
    with zipfile.ZipFile(zip_path, "r") as zipf:
        out_path = zipf.extract(zip_member, path=outdir)
    shutil.rmtree(zip_dir)
    return Path(out_path)


def get_graphs_for_file(file_id):
    qres = run_query(GRAPH_ID_FOR_FILE_QUERY % file_id)
    return (str(_[0]) for _ in qres)


def get_graphs_for_result(file_id):
    qres = run_query(GRAPH_ID_FOR_RESULT_QUERY % file_id)
    return (str(_[0]) for _ in qres)


def get_workflow(graph_id):
    qres = run_query(WORKFLOW_QUERY, graph_id=graph_id)
    assert len(qres) >= 1
    workflow = str(list(qres)[0][0])
    return workflow


def get_run_results(graph_id):
    qres = run_query(WFRUN_RESULTS_QUERY, graph_id=graph_id)
    return (str(_[0]) for _ in qres)


def get_run_objects(graph_id):
    qres = run_query(WFRUN_OBJECTS_QUERY, graph_id=graph_id)
    return (str(_[0]) for _ in qres)


def get_run_params(graph_id):
    qres = run_query(WFRUN_PARAMS_QUERY, graph_id=graph_id)
    return ((str(_.name), str(_.value)) for _ in qres)
