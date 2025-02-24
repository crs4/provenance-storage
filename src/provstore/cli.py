import sys
from pathlib import Path

import click

from . import __version__
from .load import load_crate_metadata
from .query import run_query


@click.group()
def cli():
    pass


@cli.command()
@click.argument(
    "crate",
    metavar="RO_CRATE",
    type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path),
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

    RO_CRATE: RO-Crate directory.
    """
    load_crate_metadata(crate, fuseki_url, fuseki_dataset)


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
def query(query_file, fuseki_url, fuseki_dataset):
    """\
    Run the SPARQL query in the provided file on the Fuseki store.

    QUERY_FILE: SPARQL query file
    """
    run_query(query_file, fuseki_url, fuseki_dataset)


@cli.command()
def version():
    """\
    Print version string and exit.
    """
    sys.stdout.write(f"{__version__}\n")


if __name__ == "__main__":
    cli()
