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


import atexit
import logging
import sys
from http.client import responses
from pathlib import Path
import requests
import tempfile
import shutil
import zipfile

import click

from . import __version__


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def get_base_api_url():
    """Return the base URL for the connection to API."""
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
    # check if the crate is a zip file or a directory, if it is a directory, zip it
    if zipfile.is_zipfile(crate):
        crate_path = crate
        crate_name = crate_path.name
    else:
        if not crate.is_dir():
            sys.stdout.write("Crate must be either a zip file or a directory.\n")
        # use the /tmp directory to store the zipped crate
        tmp_dir = Path(tempfile.mkdtemp(prefix="provstor_"))
        atexit.register(shutil.rmtree, tmp_dir)
        crate = crate.absolute()
        dest_path = tmp_dir / crate.name
        crate_name = f"{crate.name}.zip"
        crate_path = shutil.make_archive(dest_path, 'zip', crate)

    # print the path of the crate
    sys.stdout.write(f"Crate path: {crate_path}\n")

    url = f"{get_base_api_url()}/upload/crate/"

    try:
        with open(crate_path, 'rb') as crate_to_upload:
            # Send the crate file to the API
            sys.stdout.write(f"Uploading crate to {url}...\n")
            response = requests.post(
                url,
                files={'crate_path': (crate_name, crate_to_upload, 'application/zip')},
            )

        if response.status_code == 200:
            if response.json()['result'] == "success":
                sys.stdout.write("Crate successfully uploaded.\n")
                sys.stdout.write(f"Crate URL: {response.json()['crate_url']}\n")
        else:
            sys.stdout.write(f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

    QUERY_FILE: SPARQL query file pathname.
    """
    query_text = query_file.read_text()

    url = f"{get_base_api_url()}/query/run-query/"

    try:
        response = requests.post(url, files={'query_file': query_text}, params={'graph': graph})

        if response.status_code == 200:
            for row in response.json()['result']:
                sys.stdout.write(", ".join(row) + "\n")
        else:
            sys.stdout.write(f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

    ROOT_DATA_ENTITY_ID: @id of the RO-Crate's Root Data Entity (RDE), e.g. "arcp://...".
    """
    url = f"{get_base_api_url()}/get/crate/"

    if outdir is None:
        outdir = Path.cwd()
    else:
        outdir = Path(outdir).absolute()
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, params={'rde_id': rde_id}, stream=True)

        if response.status_code == 200:
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

            # download_path = response.headers.get('download_path')
            sys.stdout.write(f"Crate downloaded to {download_path}\n")
        else:
            sys.stdout.write(f"API returned status code {response.status_code}: {response.json()["detail"]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

    FILE_URI: URI of the file RDE (e.g. "arcp://...").
    """
    url = f"{get_base_api_url()}/get/file/"

    if outdir is None:
        outdir = Path.cwd()
    else:
        outdir = Path(outdir).absolute()
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, params={'file_uri': file_uri}, stream=True)

        if response.status_code == 200:
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

            sys.stdout.write(f"Crate downloaded to {download_path}\n")
        else:
            sys.stdout.write(f"API returned status code {response.status_code}: {response.json()["detail"]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No graphs found for the given file.\n")
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No graphs found for the given result id.\n")
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No workflow found for the given crate name.\n")
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No results found.\n")
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No objects found.\n")
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                logging.debug("No objects found for result %s", result_id)
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No actions found.\n")
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No objects found.\n")
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No results found.\n")
            else:
                for item in result:
                    sys.stdout.write(item + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            result = response.json()['result']
            if not result:
                sys.stdout.write("No parameters found for the given graph.\n")
            else:
                for item in result:
                    sys.stdout.write(f"{item[0]}: {item[1]}" + "\n")
        else:
            sys.stdout.write(
                f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


@cli.command()
def list_graphs():
    """\
    List all graphs in the triple store.
    """
    url = f"{get_base_api_url()}/query/list-graphs/"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            # sys.stdout.write(f"Query result:\n")
            for row in response.json()['result']:
                sys.stdout.write(row + "\n")
        else:
            sys.stdout.write(f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


@cli.command()
def list_rde_graphs():
    """\
    List all graphs in the triple store and the associated RDE ids.
    """
    url = f"{get_base_api_url()}/query/list-RDE-graphs/"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            for row in response.json()['result']:
                sys.stdout.write('\t'.join(row) + "\n")
        else:
            sys.stdout.write(f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            for item in response.json()['result']:
                sys.stdout.write(repr((
                    item["action"], item["objects"], item["results"]
                )) + "\n")
        else:
            sys.stdout.write(f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


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

        if response.status_code == 200:
            sys.stdout.write(f"{response.json()}\n")
        else:
            sys.stdout.write(f"API returned status code {response.status_code}: {responses[response.status_code]}\n")
    except requests.exceptions.RequestException as e:
        sys.stdout.write(f"API is not reachable: {e}\n")


if __name__ == "__main__":
    cli()
