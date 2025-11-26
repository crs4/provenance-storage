# Copyright © 2024-2025 CRS4
# Copyright © 2025 BSC
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


import atexit
import logging
import sys
from pathlib import Path
import requests
import tempfile
import shutil
import zipfile

import click

from . import __version__


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _log_error(response):
    try:
        r_json = response.json()
    except requests.exceptions.JSONDecodeError:
        msg = response.text
    else:
        msg = r_json.get("detail", "(no detail)")
    logging.error(msg)


def get_base_api_url():
    """Return the base URL for connection to the API."""
    # Refresh configuration to pick up any environment changes
    from provstor.config import API_HOST, API_PORT
    return f"http://{API_HOST}:{API_PORT}"


@click.group()
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(LOG_LEVELS),
    default="WARNING"
)
def cli(log_level):
    logging.basicConfig(level=getattr(logging, log_level))


@cli.command()
@click.argument(
    "crate",
    metavar="RO_CRATE",
    type=click.Path(exists=True, readable=True, path_type=Path),
)
def load(crate):
    """\
    Load RO-Crate metadata into Fuseki and upload zipped crate to MinIO.

    RO_CRATE: RO-Crate directory or ZIP archive.
    """
    if zipfile.is_zipfile(crate):
        crate_path = crate
        crate_name = crate_path.name
    else:
        if not crate.is_dir():
            raise click.ClickException("Crate must be either a zip file or a directory.")
        tmp_dir = Path(tempfile.mkdtemp(prefix="provstor_"))
        atexit.register(shutil.rmtree, tmp_dir)
        crate = crate.absolute()
        dest_path = tmp_dir / crate.name
        crate_name = f"{crate.name}.zip"
        crate_path = shutil.make_archive(dest_path, 'zip', crate)

    logging.info("Crate path: %s", crate_path)

    url = f"{get_base_api_url()}/upload/crate/"

    try:
        with open(crate_path, 'rb') as crate_to_upload:
            logging.info("Uploading crate to %s", url)
            response = requests.post(
                url,
                files={'crate_path': (crate_name, crate_to_upload, 'application/zip')},
            )
        response.raise_for_status()
        json_res = response.json()
        if json_res['result'] == "success":
            logging.info("Crate successfully uploaded")
            logging.info("Crate URL: %s", json_res['crate_url'])
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise


@cli.command()
@click.argument(
    "query_file",
    metavar="QUERY_FILE",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path)
)
@click.option(
    "-g",
    "--graph",
    metavar="STRING",
    help="Graph name (crate basename without extension)",
)
def query(query_file, graph):
    """\
    Run the SPARQL query in the provided file on the Fuseki store.

    QUERY_FILE: SPARQL query file path.
    """
    query_text = query_file.read_text()

    url = f"{get_base_api_url()}/query/run-query/"

    try:
        response = requests.post(url, files={'query_file': query_text}, params={'graph': graph})
        response.raise_for_status()
        for row in response.json()['result']:
            sys.stdout.write(", ".join(row) + "\n")
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise


@cli.command()
@click.argument(
    "rde_id",
    metavar="ROOT_DATA_ENTITY_ID"
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(path_type=Path),
    help="directory where the crate should be saved",
)
def get_crate(rde_id, outdir):
    """\
    Download the crate corresponding to the given root data entity id.

    ROOT_DATA_ENTITY_ID: @id of the RO-Crate's Root Data Entity (RDE),
    e.g. "arcp://uuid,7dcc0072-ee6b-58c0-894b-d467e4141de3/".
    """
    url = f"{get_base_api_url()}/get/crate/"

    if outdir is None:
        outdir = Path.cwd()
    else:
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, params={'rde_id': rde_id}, stream=True)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise
    content_disposition = response.headers.get('Content-Disposition')
    file_to_download = None
    if 'filename' in content_disposition:
        file_to_download = content_disposition.split('filename=')[1].strip('"')

    if not file_to_download:
        file_to_download = rde_id.rsplit("/", 1)[-1]
        if not file_to_download:
            file_to_download = "downloaded_file"

    download_path = outdir / file_to_download

    with open(download_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logging.info("Crate downloaded to %s", download_path)


@cli.command()
@click.argument(
    "file_uri",
    metavar="FILE_URI"
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(path_type=Path),
    help="directory where the file should be saved",
)
def get_file(file_uri, outdir):
    """\
    Download the file corresponding to the given URI.

    FILE_URI: URI of the file,
    e.g. arcp://uuid,7dcc0072-ee6b-58c0-894b-d467e4141de3/readme.txt.
    """
    url = f"{get_base_api_url()}/get/file/"

    if outdir is None:
        outdir = Path.cwd()
    else:
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, params={'file_uri': file_uri}, stream=True)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    content_disposition = response.headers.get('Content-Disposition')
    file_to_download = None
    if 'filename' in content_disposition:
        file_to_download = content_disposition.split('filename=')[1].strip('"')

    if not file_to_download:
        file_to_download = file_uri.rsplit("/", 1)[-1]
        if not file_to_download:
            file_to_download = "downloaded_file"

    download_path = outdir / file_to_download

    with open(download_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logging.info("File downloaded to %s", download_path)


@cli.command()
@click.argument(
    "file_id",
    metavar="FILE_ID"
)
def get_graphs_for_file(file_id):
    """\
    Get the ids of the graphs that contain (hasPart) the given file.

    FILE_ID: full URI of the file (e.g. "file://...").
    """
    url = f"{get_base_api_url()}/get/graphs-for-file/"

    try:
        response = requests.get(url, params={'file_id': file_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No graphs found for '%s'", file_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "result_id",
    metavar="RESULT_ID"
)
def get_graphs_for_result(result_id):
    """\
    Get the ids of the graphs where the given id is listed as the result of a
    CreateAction.

    RESULT_ID: RO-Crate id of the result (e.g. "file://...").
    """
    url = f"{get_base_api_url()}/get/graphs-for-result/"

    try:
        response = requests.get(url, params={'result_id': result_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No graphs found for '%s'", result_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
def get_workflow(graph_id):
    """\
    Get the workflow id corresponding to the given graph id. This should
    give a result only for a Workflow RO-Crate and crates whose profile is
    derived from Workflow-RO-Crate.

    GRAPH_ID: name of RO-Crate (e.g. "mycrate") or full URL (e.g. "http://...").
    """
    url = f"{get_base_api_url()}/get/workflow/"

    try:
        response = requests.get(url, params={'graph_id': graph_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No workflow found for graph '%s'", graph_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
def get_run_results(graph_id):
    """\
    Get the workflow run results that are either files or directories
    corresponding to the given graph id.

    GRAPH_ID: name of RO-Crate (e.g. "mycrate") or full URL (e.g. "http://...").
    """
    url = f"{get_base_api_url()}/get/run-results/"

    try:
        response = requests.get(url, params={'graph_id': graph_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No results found for '%s'", graph_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
def get_run_objects(graph_id):
    """\
    Get the workflow run objects that are either files or directories
    corresponding to the given graph id.

    GRAPH_ID: name of RO-Crate (e.g. "mycrate") or full URL (e.g. "http://...").
    """
    url = f"{get_base_api_url()}/get/run-objects/"

    try:
        response = requests.get(url, params={'graph_id': graph_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No objects found for '%s'", graph_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "result_id",
    metavar="RESULT_ID"
)
def get_objects_for_result(result_id):
    """\
    Get objects that are related to the given result in a CreateAction.

    RESULT_ID: RO-Crate id of the result (e.g. "file://...").
    """
    url = f"{get_base_api_url()}/get/objects-for-result/"

    try:
        response = requests.get(url, params={'result_id': result_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No objects found for result '%s'", result_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "result_id",
    metavar="RESULT_ID"
)
def get_actions_for_result(result_id):
    """\
    Get actions that have the given result.

    RESULT_ID: RO-Crate id of the result (e.g. "file://...").
    """
    url = f"{get_base_api_url()}/get/actions-for-result/"

    try:
        response = requests.get(url, params={'result_id': result_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No actions found for result '%s'", result_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "action_id",
    metavar="ACTION_ID"
)
def get_objects_for_action(action_id):
    """\
    Get the objects of the given CreateAction.

    ACTION_ID: id of the CreateAction (e.g. "arcp://...").
    """
    url = f"{get_base_api_url()}/get/objects-for-action/"

    try:
        response = requests.get(url, params={'action_id': action_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No objects found for action '%s'", action_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "action_id",
    metavar="ACTION_ID"
)
def get_results_for_action(action_id):
    """\
    Get the results of the given CreateAction.

    ACTION_ID: id of the CreateAction (e.g. "arcp://...").
    """
    url = f"{get_base_api_url()}/get/results-for-action/"

    try:
        response = requests.get(url, params={'action_id': action_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No results found for action '%s'", action_id)
    else:
        for item in result:
            sys.stdout.write(item + "\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
def get_run_params(graph_id):
    """\
    Get the workflow run objects that are parameters (name: value)
    corresponding to the given graph id.

    GRAPH_ID: name of RO-Crate (e.g. "mycrate") or full URL (e.g. "http://...").
    """
    url = f"{get_base_api_url()}/get/run-params/"

    try:
        response = requests.get(url, params={'graph_id': graph_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    result = response.json()['result']
    if not result:
        logging.debug("No parameters found for graph '%s'", graph_id)
    else:
        for item in result:
            sys.stdout.write(f"{item[0]}: {item[1]}" + "\n")


@cli.command()
def list_graphs():
    """\
    List all graphs in the triple store.
    """
    url = f"{get_base_api_url()}/query/list-graphs/"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    for row in response.json()['result']:
        sys.stdout.write(row + "\n")


@cli.command()
def list_rde_graphs():
    """\
    List all graphs in the triple store and the associated RDE ids.
    """
    url = f"{get_base_api_url()}/query/list-RDE-graphs/"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    for row in response.json()['result']:
        sys.stdout.write('\t'.join(row) + "\n")


@cli.command()
@click.argument(
    "result_id",
    metavar="RESULT_ID"
)
def backtrack(result_id):
    """\
    Recursively get objects related to the given result by a chain of actions.

    RESULT_ID: RO-Crate id of the result (e.g. "file://...").
    """
    url = f"{get_base_api_url()}/backtrack/"

    try:
        response = requests.get(url, params={'result_id': result_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    for item in response.json()['result']:
        sys.stdout.write(repr((
            item["action"], item["objects"], item["results"]
        )) + "\n")


@cli.command()
@click.argument(
    "src_id",
    metavar="SRC_ID"
)
@click.argument(
    "dest_id",
    metavar="DEST_ID"
)
@click.option(
    "-w",
    "--when",
    metavar="STRING",
    help="datetime when the copy happened (ended)",
)
def cp(src_id, dest_id, when):
    """\
    Record the copying of a file.

    Generates a new Process Run Crate with an action that has the source as
    object and the destination as result. The crate is then loaded onto the
    system in the same way as in the "load" command.

    \b
    SRC_ID: RO-Crate id of the source file.
    DEST_ID: RO-Crate id of the destination file.
    """
    _cp_or_mv(src_id, dest_id, when, op="copy")


@cli.command()
@click.argument(
    "src_id",
    metavar="SRC_ID"
)
@click.argument(
    "dest_id",
    metavar="DEST_ID"
)
@click.option(
    "-w",
    "--when",
    metavar="STRING",
    help="datetime when the move happened (ended)",
)
def mv(src_id, dest_id, when):
    """\
    Record the movement of a file.

    Generates a new Process Run Crate with an action that has the source as
    object and the destination as result. The crate is then loaded onto the
    system in the same way as in the "load" command.

    \b
    SRC_ID: RO-Crate id of the source file.
    DEST_ID: RO-Crate id of the destination file.
    """
    _cp_or_mv(src_id, dest_id, when, op="move")


def _cp_or_mv(src_id, dest_id, when, op="copy"):
    url = f"{get_base_api_url()}/pathops/{op}/"
    params = {'src': src_id, 'dest': dest_id}
    if when:
        params["when"] = when

    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    json_res = response.json()
    if json_res['result'] == "success":
        logging.info("Generated crate url: %s", json_res['crate_url'])


@cli.command()
@click.argument(
    "path_id",
    metavar="PATH_ID"
)
def movechain(path_id):
    """\
    Recursively get the list of paths where the given path has been moved.

    PATH_ID: RO-Crate id of the starting path (e.g. "file://...").
    """
    url = f"{get_base_api_url()}/pathops/movechain/"

    try:
        response = requests.get(url, params={'path_id': path_id})
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    for item in response.json()['result']:
        sys.stdout.write(item + "\n")


@cli.command()
def version():
    """\
    Print version string and exit.
    """
    sys.stdout.write(f"{__version__}\n")


@cli.command()
def api_status():
    """\
    Check the status of the ProvStor API.
    """
    url = f"{get_base_api_url()}/status/"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        _log_error(response)
        raise

    sys.stdout.write(f"{response.json()}\n")


if __name__ == "__main__":
    cli()
