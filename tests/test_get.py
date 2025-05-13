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

import filecmp
import zipfile

from provstor.constants import MINIO_STORE, MINIO_BUCKET
from provstor.get import (
    get_crate,
    get_file,
    get_graph_id,
    get_workflow,
    get_run_results,
    get_run_objects,
    get_run_params
)
from provstor.load import load_crate_metadata
from provstor.queries import RDE_QUERY
from provstor.query import run_query


def _load_and_get_rde_id(crate_path):
    crate_url = load_crate_metadata(crate_path)
    qres = run_query(RDE_QUERY, graph_id=crate_url)
    assert len(qres) == 1
    return str(list(qres)[0][0])


def test_get_crate(data_dir, tmpdir):
    crate_path = data_dir / "crate1"
    md_path = crate_path / "ro-crate-metadata.json"
    rde_id = _load_and_get_rde_id(crate_path)
    zip_path = get_crate(rde_id, outdir=tmpdir)
    assert zip_path.name == "crate1.zip"
    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert zipf.namelist() == ["ro-crate-metadata.json"]
        assert zipf.read("ro-crate-metadata.json") == md_path.read_bytes()


def test_get_file(data_dir, tmpdir):
    crate_path = data_dir / "crate1"
    md_path = crate_path / "ro-crate-metadata.json"
    rde_id = _load_and_get_rde_id(crate_path)
    out_md_path = get_file(f"{rde_id}/ro-crate-metadata.json", outdir=tmpdir)
    assert filecmp.cmp(out_md_path, md_path)


def test_get_graph_id(data_dir):
    crate_path = data_dir / "provcrate1"
    _load_and_get_rde_id(crate_path)
    graph_id = get_graph_id("file:///path/to/FOOBAR123.md.cram")
    assert graph_id == f"http://{MINIO_STORE}/{MINIO_BUCKET}/provcrate1.zip"


def test_get_workflow(data_dir):
    crate_path = data_dir / "provcrate1"
    rde_id = _load_and_get_rde_id(crate_path)
    graph_id = f"http://{MINIO_STORE}/{MINIO_BUCKET}/provcrate1.zip"
    workflow = get_workflow(graph_id)
    assert workflow == f"{rde_id}main.nf"


def test_get_run_results(data_dir):
    crate_path = data_dir / "provcrate1"
    _load_and_get_rde_id(crate_path)
    graph_id = f"http://{MINIO_STORE}/{MINIO_BUCKET}/provcrate1.zip"
    results = set(get_run_results(graph_id))
    assert results == {
        "file:///path/to/FOOBAR123.md.cram.crai",
        "file:///path/to/FOOBAR123.md.cram"
    }


def test_get_run_objects(data_dir):
    crate_path = data_dir / "provcrate1"
    rde_id = _load_and_get_rde_id(crate_path)
    graph_id = f"http://{MINIO_STORE}/{MINIO_BUCKET}/provcrate1.zip"
    objects = set(get_run_objects(graph_id))
    assert objects == {
        "file:///path/to/FOOBAR123_1.fastq.gz",
        "file:///path/to/FOOBAR123_2.fastq.gz",
        "file:///path/to/pipeline_info/software_versions.yml",
        "http://example.com/fooconfig.yml",
        f"{rde_id}sample.csv"
    }


def test_get_run_params(data_dir):
    crate_path = data_dir / "provcrate1"
    _load_and_get_rde_id(crate_path)
    graph_id = f"http://{MINIO_STORE}/{MINIO_BUCKET}/provcrate1.zip"
    params = set(get_run_params(graph_id))
    assert params == {
        ("input", "sample.csv"),
        ("foo", "foo_value")
    }
