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

import pytest

from provstor.config import MINIO_STORE, MINIO_BUCKET
from provstor.get import (
    get_crate,
    get_file,
    get_graphs_for_file,
    get_graphs_for_result,
    get_workflow,
    get_run_results,
    get_run_objects,
    get_objects_for_result,
    get_actions_for_result,
    get_objects_for_action,
    get_results_for_action,
    get_run_params
)


@pytest.mark.parametrize("cwd", [False, True])
def test_get_crate(crate_map, tmp_path, monkeypatch, cwd):
    crate_path = crate_map["crate1"]["path"]
    md_path = crate_path / "ro-crate-metadata.json"
    if cwd:
        monkeypatch.chdir(str(tmp_path))
        zip_path = get_crate(crate_map["crate1"]["rde_id"])
    else:
        zip_path = get_crate(crate_map["crate1"]["rde_id"], outdir=tmp_path)
    assert zip_path.name == "crate1.zip"
    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert zipf.namelist() == ["ro-crate-metadata.json"]
        assert zipf.read("ro-crate-metadata.json") == md_path.read_bytes()


@pytest.mark.parametrize("cwd", [False, True])
def test_get_file(crate_map, tmp_path, monkeypatch, cwd):
    crate_path = crate_map["crate1"]["path"]
    md_path = crate_path / "ro-crate-metadata.json"
    rde_id = crate_map["crate1"]["rde_id"]
    if cwd:
        monkeypatch.chdir(str(tmp_path))
        out_md_path = get_file(f"{rde_id}/ro-crate-metadata.json")
    else:
        out_md_path = get_file(f"{rde_id}/ro-crate-metadata.json", outdir=tmp_path)
    assert filecmp.cmp(out_md_path, md_path)


def test_get_graphs_for_file(crate_map):
    graphs = get_graphs_for_file("file:///path/to/FOOBAR123.deepvariant.vcf.gz")
    assert set(graphs) >= {
        f"http://{MINIO_STORE}/{MINIO_BUCKET}/proccrate1.zip",
        f"http://{MINIO_STORE}/{MINIO_BUCKET}/provcrate1.zip"
    }


def test_get_graphs_for_result(crate_map):
    graphs = get_graphs_for_result("file:///path/to/FOOBAR123.deepvariant.vcf.gz")
    assert set(graphs) >= {
        f"http://{MINIO_STORE}/{MINIO_BUCKET}/provcrate1.zip"
    }


def test_get_workflow(crate_map):
    graph_id = crate_map["provcrate1"]["url"]
    rde_id = crate_map["provcrate1"]["rde_id"]
    results = set(get_workflow(graph_id))
    assert results == {f"{rde_id}main.nf"}


def test_get_run_results(crate_map):
    graph_id = crate_map["provcrate1"]["url"]
    results = set(get_run_results(graph_id))
    assert results == {
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz.tbi",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    }


def test_get_run_objects(crate_map):
    graph_id = crate_map["provcrate1"]["url"]
    rde_id = crate_map["provcrate1"]["rde_id"]
    objects = set(get_run_objects(graph_id))
    assert objects == {
        "file:///path/to/FOOBAR123_1.fastq.gz",
        "file:///path/to/FOOBAR123_2.fastq.gz",
        "file:///path/to/pipeline_info/software_versions.yml",
        "http://example.com/fooconfig.yml",
        f"{rde_id}sample.csv"
    }


def test_get_objects_for_result(crate_map):
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    objects = set(get_objects_for_result(
        "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    ))
    assert objects >= {
        f"{proccrate2_rde_id}aux.txt",
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    }
    objects = set(get_objects_for_result(
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    ))
    assert objects >= {
        f"{proccrate1_rde_id}aux.vcf",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    }
    objects = set(get_objects_for_result(f"{proccrate1_rde_id}aux.vcf"))
    assert len(objects) == 0
    objects = set(get_objects_for_result(
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    ))
    assert objects >= {
        "file:///path/to/FOOBAR123_1.fastq.gz",
        "file:///path/to/FOOBAR123_2.fastq.gz",
        "file:///path/to/pipeline_info/software_versions.yml",
        "http://example.com/fooconfig.yml",
        f"{provcrate1_rde_id}sample.csv",
    }


def test_get_actions_for_result(crate_map):
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    actions = set(get_actions_for_result(
        "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    ))
    assert actions >= {
        f"{proccrate2_rde_id}#normalization-1",
    }
    actions = set(get_actions_for_result(
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    ))
    assert actions >= {
        f"{proccrate1_rde_id}#annotation-1",
    }
    actions = set(get_actions_for_result(
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    ))
    assert actions >= {
        f"{provcrate1_rde_id}#12204f1e-758f-46e7-bad7-162768de3a5d",
        f"{provcrate1_rde_id}#publish/13fc2459df3405bf049e575f063aef3d/FOOBAR123.deepvariant.vcf.gz"
    }


def test_get_objects_for_action(crate_map):
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    objects = set(get_objects_for_action(
        f"{proccrate2_rde_id}#normalization-1"
    ))
    assert objects >= {
        f"{proccrate2_rde_id}aux.txt",
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    }
    objects = set(get_objects_for_action(
        f"{proccrate1_rde_id}#annotation-1"
    ))
    assert objects >= {
        f"{proccrate1_rde_id}aux.vcf",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    }
    objects = set(get_objects_for_action(
        f"{provcrate1_rde_id}#12204f1e-758f-46e7-bad7-162768de3a5d"
    ))
    assert objects >= {
        "file:///path/to/FOOBAR123_1.fastq.gz",
        "file:///path/to/FOOBAR123_2.fastq.gz",
        "file:///path/to/pipeline_info/software_versions.yml",
        "http://example.com/fooconfig.yml",
        f"{provcrate1_rde_id}sample.csv",
    }


def test_get_results_for_action(crate_map):
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    results = set(get_results_for_action(
        f"{proccrate2_rde_id}#normalization-1"
    ))
    assert results >= {
        "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz",
    }
    results = set(get_results_for_action(
        f"{proccrate1_rde_id}#annotation-1"
    ))
    assert results >= {
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz",
    }
    results = set(get_results_for_action(
        f"{provcrate1_rde_id}#12204f1e-758f-46e7-bad7-162768de3a5d"
    ))
    assert results >= {
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz.tbi",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz",
    }


def test_get_run_params(crate_map):
    graph_id = crate_map["provcrate1"]["url"]
    params = set(get_run_params(graph_id))
    assert params == {
        ("input", "sample.csv"),
        ("foo", "foo_value")
    }
