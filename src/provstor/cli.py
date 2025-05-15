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
from pathlib import Path

import click

from . import __version__
from .get import (
    get_crate as get_crate_f,
    get_file as get_file_f,
    get_graph_id as get_graph_id_f,
    get_run_results as get_run_results_f,
    get_run_objects as get_run_objects_f,
    get_run_params as get_run_params_f,
    get_workflow as get_workflow_f
)
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
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
def load(crate, fuseki_url, fuseki_dataset):
    """\
    Load RO-Crate metadata into Fuseki and upload zipped crate to MinIO.

    RO_CRATE: RO-Crate directory or ZIP archive.
    """
    crate_url = load_crate_metadata(crate, fuseki_url, fuseki_dataset)
    sys.stdout.write(f"{crate_url}\n")


@cli.command()
@click.argument(
    "query_file",
    metavar="QUERY_FILE",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path)
)
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
@click.option(
    "-g",
    "--graph",
    metavar="STRING",
    help="Graph name (crate basename without extension)",
)
def query(query_file, fuseki_url, fuseki_dataset, graph):
    """\
    Run the SPARQL query in the provided file on the Fuseki store.

    QUERY_FILE: SPARQL query file
    """
    query = query_file.read_text()
    qres = run_query(query, fuseki_url, fuseki_dataset, graph)
    for row in qres:
        sys.stdout.write(", ".join(row) + "\n")


@cli.command()
@click.argument(
    "rde_id",
    metavar="ROOT_DATA_ENTITY_ID"
)
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(path_type=Path),
    help="directory where the crate should be saved",
)
def get_crate(rde_id, fuseki_url, fuseki_dataset, outdir):
    """\
    Download the crate corresponding to the given root data entity id.

    ROOT_DATA_ENTITY_ID: @id of the RO-Crate's Root Data Entity
    """
    out_path = get_crate_f(rde_id, fuseki_url, fuseki_dataset, outdir)
    sys.stdout.write(f"crate downloaded to {out_path}\n")


@cli.command()
@click.argument(
    "file_uri",
    metavar="FILE_URI"
)
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
@click.option(
    "-o",
    "--outdir",
    type=click.Path(path_type=Path),
    help="directory where the file should be saved",
)
def get_file(file_uri, fuseki_url, fuseki_dataset, outdir):
    """\
    Download the file corresponding to the given URI.

    FILE_URI: URI of the file.
    """
    out_path = get_file_f(file_uri, fuseki_url, fuseki_dataset, outdir)
    sys.stdout.write(f"file extracted to {out_path}\n")


@cli.command()
@click.argument(
    "file_id",
    metavar="FILE_ID"
)
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
def get_graph_id(file_id, fuseki_url, fuseki_dataset):
    """\
    Get the graph id corresponding to the given file.

    FILE_ID: full URI of the file (e.g. file://...).
    """
    graph_id = get_graph_id_f(file_id, fuseki_url, fuseki_dataset)
    sys.stdout.write(f"{graph_id}\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
def get_workflow(graph_id, fuseki_url, fuseki_dataset):
    """\
    Get the workflow id corresponding to the given graph id.

    GRAPH_ID: id of the graph in the triple store.
    """
    workflow = get_workflow_f(graph_id, fuseki_url, fuseki_dataset)
    sys.stdout.write(f"{workflow}\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
def get_run_results(graph_id, fuseki_url, fuseki_dataset):
    """\
    Get the workflow run results that are either files or directories
    corresponding to the given graph id.

    GRAPH_ID: id of the graph in the triple store.
    """
    results = get_run_results_f(graph_id, fuseki_url, fuseki_dataset)
    for r in results:
        sys.stdout.write(f"{r}\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
def get_run_objects(graph_id, fuseki_url, fuseki_dataset):
    """\
    Get the workflow run objects that are either files or directories
    corresponding to the given graph id.

    GRAPH_ID: id of the graph in the triple store.
    """
    objects = get_run_objects_f(graph_id, fuseki_url, fuseki_dataset)
    for r in objects:
        sys.stdout.write(f"{r}\n")


@cli.command()
@click.argument(
    "graph_id",
    metavar="GRAPH_ID"
)
@click.option(
    "-u",
    "--fuseki-url",
    metavar="STRING",
    help="Fuseki base url",
)
@click.option(
    "-d",
    "--fuseki-dataset",
    metavar="STRING",
    help="Fuseki dataset",
)
def get_run_params(graph_id, fuseki_url, fuseki_dataset):
    """\
    Get the workflow run objects that are parameters (name: value)
    corresponding to the given graph id.

    GRAPH_ID: id of the graph in the triple store.
    """
    params = get_run_params_f(graph_id, fuseki_url, fuseki_dataset)
    for name, value in params:
        sys.stdout.write(f"{name}: {value}\n")


@cli.command()
def version():
    """\
    Print version string and exit.
    """
    sys.stdout.write(f"{__version__}\n")


if __name__ == "__main__":
    cli()
