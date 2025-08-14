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


import logging
import sys
from http.client import responses
from pathlib import Path
import requests

import click

from . import __version__
from .backtrack import backtrack as backtrack_f
from .get import (
    get_crate as get_crate_f,
    get_file as get_file_f,
    get_graphs_for_file as get_graphs_for_file_f,
    get_graphs_for_result as get_graphs_for_result_f,
    get_run_results as get_run_results_f,
    get_run_objects as get_run_objects_f,
    get_run_params as get_run_params_f,
    get_objects_for_result as get_objects_for_result_f,
    get_actions_for_result as get_actions_for_result_f,
    get_objects_for_action as get_objects_for_action_f,
    get_results_for_action as get_results_for_action_f,
    get_workflow as get_workflow_f
)
from .list import list_graphs as list_graphs_f
from .load import load_crate_metadata
from .query import run_query


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


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
    crate_url = load_crate_metadata(crate)
    sys.stdout.write(f"{crate_url}\n")


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

    QUERY_FILE: SPARQL query file
    """
    query_text = query_file.read_text()

    url = "http://localhost:8000/query/run-query/"

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

    ROOT_DATA_ENTITY_ID: @id of the RO-Crate's Root Data Entity
    """
    url = "http://localhost:8000/get/crate/"

    if outdir is None:
        outdir = Path.cwd()
    else:
        outdir = Path(outdir).absolute()
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, params={'rde_id': rde_id, 'outdir': outdir})

        if response.status_code == 200:
            download_path = response.headers.get('download_path')
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

    FILE_URI: URI of the file.
    """
    out_path = get_file_f(file_uri, outdir)
    sys.stdout.write(f"file extracted to {out_path}\n")


@cli.command()
@click.argument(
    "file_id",
    metavar="FILE_ID"
)
def get_graphs_for_file(file_id):
    """\
    Get the ids of the graphs that contain (hasPart) the given file.

    FILE_ID: full URI of the file (e.g. file://...).
    """
    graphs = get_graphs_for_file_f(file_id)
    for g in graphs:
        sys.stdout.write(f"{g}\n")


@cli.command()
@click.argument(
    "result_id",
    metavar="RESULT_ID"
)
def get_graphs_for_result(result_id):
    """\
    Get the ids of the graphs where the given id is listed as the result of a
    CreateAction.

    RESULT_ID: RO-Crate id of the result.
    """
    graphs = get_graphs_for_result_f(result_id)
    for g in graphs:
        sys.stdout.write(f"{g}\n")


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

    GRAPH_ID: id of the graph in the triple store.
    """
    workflows = get_workflow_f(graph_id)
    for g in workflows:
        sys.stdout.write(f"{g}\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
def get_run_results(graph_id):
    """\
    Get the workflow run results that are either files or directories
    corresponding to the given graph id.

    GRAPH_ID: id of the graph in the triple store.
    """
    results = get_run_results_f(graph_id)
    for r in results:
        sys.stdout.write(f"{r}\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
def get_run_objects(graph_id):
    """\
    Get the workflow run objects that are either files or directories
    corresponding to the given graph id.

    GRAPH_ID: id of the graph in the triple store.
    """
    objects = get_run_objects_f(graph_id)
    for r in objects:
        sys.stdout.write(f"{r}\n")


@cli.command()
@click.argument(
    "result_id",
    metavar="RESULT_ID"
)
def get_objects_for_result(result_id):
    """\
    Get objects that are related to the given result in a CreateAction.

    RESULT_ID: id of the result item.
    """
    objects = get_objects_for_result_f(result_id)
    for r in objects:
        sys.stdout.write(f"{r}\n")


@cli.command()
@click.argument(
    "result_id",
    metavar="RESULT_ID"
)
def get_actions_for_result(result_id):
    """\
    Get actions that have the given result.

    RESULT_ID: id of the result item.
    """
    actions = get_actions_for_result_f(result_id)
    for a in actions:
        sys.stdout.write(f"{a}\n")


@cli.command()
@click.argument(
    "action_id",
    metavar="ACTION_ID"
)
def get_objects_for_action(action_id):
    """\
    Get the objects of the given CreateAction.

    ACTION_ID: id of the CreateAction.
    """
    objects = get_objects_for_action_f(action_id)
    for r in objects:
        sys.stdout.write(f"{r}\n")


@cli.command()
@click.argument(
    "action_id",
    metavar="ACTION_ID"
)
def get_results_for_action(action_id):
    """\
    Get the results of the given CreateAction.

    ACTION_ID: id of the CreateAction.
    """
    results = get_results_for_action_f(action_id)
    for r in results:
        sys.stdout.write(f"{r}\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
def get_run_params(graph_id):
    """\
    Get the workflow run objects that are parameters (name: value)
    corresponding to the given graph id.

    GRAPH_ID: id of the graph in the triple store.
    """
    params = get_run_params_f(graph_id)
    for name, value in params:
        sys.stdout.write(f"{name}: {value}\n")


@cli.command()
def list_graphs():
    """\
    List all graphs in the triple store.
    """
    graphs = list_graphs_f()
    for g in graphs:
        sys.stdout.write(f"{g}\n")


@cli.command()
@click.argument(
    "result_id",
    metavar="RESULT_ID"
)
def backtrack(result_id):
    """\
    Recursively get objects related to the given result by a chain of actions.

    RESULT_ID: id of the result item.
    """
    for item in backtrack_f(result_id):
        sys.stdout.write(f"{item}\n")


@cli.command()
def version():
    """\
    Print version string and exit.
    """
    sys.stdout.write(f"{__version__}\n")


if __name__ == "__main__":
    cli()
