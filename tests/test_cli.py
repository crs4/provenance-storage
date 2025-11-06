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

import shutil
import uuid

from click.testing import CliRunner
import pytest
from provstor.cli import cli


@pytest.mark.parametrize("zipped", [False, True])
def test_cli_load(data_dir, tmp_path, crate_map, zipped):
    runner = CliRunner()
    if zipped:
        crate = shutil.make_archive(tmp_path / "crate1", "zip", data_dir / "crate1")
    else:
        crate = data_dir / "crate1"
    args = ["load", str(crate)]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception


@pytest.mark.parametrize("graph", [None, "crate1"])
def test_cli_query(graph, crate_map, data_dir):
    query_path = data_dir / "query.txt"
    runner = CliRunner()
    args = ["query", str(query_path)]
    if graph:
        args.extend(["-g", graph])
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    if graph:
        assert result.stdout.rstrip() == "https://orcid.org/0000-0001-8271-5429, Simone Leo"
    else:
        assert set(result.stdout.splitlines()) == {
            "https://orcid.org/0000-0001-8271-5429, Simone Leo",
            "https://orcid.org/0000-0002-1825-0097, Josiah Carberry"
        }


@pytest.mark.parametrize("cwd", [False, True])
def test_cli_get_crate(crate_map, tmp_path, monkeypatch, cwd):
    runner = CliRunner()
    rde_id = crate_map["crate1"]["rde_id"]
    if cwd:
        monkeypatch.chdir(str(tmp_path))
        args = ["get-crate", rde_id]
    else:
        args = ["get-crate", rde_id, "-o", tmp_path]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert (tmp_path / "crate1.zip").is_file()


@pytest.mark.parametrize("cwd", [False, True])
def test_cli_get_file(crate_map, tmp_path, monkeypatch, cwd):
    runner = CliRunner()
    rde_id = crate_map["crate1"]["rde_id"]
    file_id = rde_id + "ro-crate-metadata.json"
    if cwd:
        monkeypatch.chdir(str(tmp_path))
        args = ["get-file", file_id]
    else:
        args = ["get-file", file_id, "-o", tmp_path]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert (tmp_path / "ro-crate-metadata.json").is_file()


def test_cli_get_graphs_for_file(crate_map):
    runner = CliRunner()
    args = ["get-graphs-for-file", "file:///path/to/FOOBAR123.deepvariant.vcf.gz"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        crate_map["proccrate1"]["url"],
        crate_map["provcrate1"]["url"],
    }
    args = ["get-graphs-for-file", "file:///not/present"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_graphs_for_result(crate_map):
    runner = CliRunner()
    args = ["get-graphs-for-result", "file:///path/to/FOOBAR123.deepvariant.vcf.gz"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        crate_map["provcrate1"]["url"]
    }
    args = ["get-graphs-for-result", "file:///not/present"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_workflow(crate_map):
    runner = CliRunner()
    crate_url = crate_map["provcrate1"]["url"]
    rde_id = crate_map["provcrate1"]["rde_id"]
    args = ["get-workflow", crate_url]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) == {rde_id + "main.nf"}
    crate_url = crate_map["crate1"]["url"]
    args = ["get-workflow", crate_url]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_run_results(crate_map):
    runner = CliRunner()
    crate_url = crate_map["provcrate1"]["url"]
    args = ["get-run-results", crate_url]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) == {
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz.tbi",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    }
    crate_url = crate_map["crate1"]["url"]
    args = ["get-run-results", crate_url]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_run_objects(crate_map):
    runner = CliRunner()
    crate_url = crate_map["provcrate1"]["url"]
    rde_id = crate_map["provcrate1"]["rde_id"]
    args = ["get-run-objects", crate_url]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) == {
        "file:///path/to/FOOBAR123_1.fastq.gz",
        "file:///path/to/FOOBAR123_2.fastq.gz",
        "file:///path/to/pipeline_info/software_versions.yml",
        "http://example.com/fooconfig.yml",
        f"{rde_id}sample.csv"
    }
    crate_url = crate_map["crate1"]["url"]
    args = ["get-run-objects", crate_url]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_objects_for_result(crate_map):
    runner = CliRunner()
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    result_id = "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    args = ["get-objects-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) == {
        f"{proccrate2_rde_id}aux.txt",
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    }
    result_id = "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    args = ["get-objects-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) == {
        f"{proccrate1_rde_id}aux.vcf",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    }
    result_id = f"{proccrate1_rde_id}aux.vcf"
    args = ["get-objects-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert len(result.stdout.splitlines()) == 0
    result_id = "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    args = ["get-objects-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) == {
        "file:///path/to/FOOBAR123_1.fastq.gz",
        "file:///path/to/FOOBAR123_2.fastq.gz",
        "file:///path/to/pipeline_info/software_versions.yml",
        "http://example.com/fooconfig.yml",
        f"{provcrate1_rde_id}sample.csv",
    }
    result_id = "file:///not/present"
    args = ["get-objects-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_actions_for_result(crate_map):
    runner = CliRunner()
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    result_id = "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    args = ["get-actions-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        f"{proccrate2_rde_id}#normalization-1",
    }
    result_id = "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    args = ["get-actions-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        f"{proccrate1_rde_id}#annotation-1",
    }
    result_id = "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    args = ["get-actions-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        f"{provcrate1_rde_id}#12204f1e-758f-46e7-bad7-162768de3a5d",
        f"{provcrate1_rde_id}#publish/13fc2459df3405bf049e575f063aef3d/FOOBAR123.deepvariant.vcf.gz",
    }
    result_id = "file:///not/present"
    args = ["get-actions-for-result", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_objects_for_action(crate_map):
    runner = CliRunner()
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    action_id = f"{proccrate2_rde_id}#normalization-1"
    args = ["get-objects-for-action", action_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        f"{proccrate2_rde_id}aux.txt",
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    }
    action_id = f"{proccrate1_rde_id}#annotation-1"
    args = ["get-objects-for-action", action_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        f"{proccrate1_rde_id}aux.vcf",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    }
    action_id = f"{provcrate1_rde_id}#12204f1e-758f-46e7-bad7-162768de3a5d"
    args = ["get-objects-for-action", action_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        "file:///path/to/FOOBAR123_1.fastq.gz",
        "file:///path/to/FOOBAR123_2.fastq.gz",
        "file:///path/to/pipeline_info/software_versions.yml",
        "http://example.com/fooconfig.yml",
        f"{provcrate1_rde_id}sample.csv",
    }
    action_id = "#not-present"
    args = ["get-objects-for-action", action_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_results_for_action(crate_map):
    runner = CliRunner()
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    action_id = f"{proccrate2_rde_id}#normalization-1"
    args = ["get-results-for-action", action_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz",
        "file:///path/to/logs",
    }
    action_id = f"{proccrate1_rde_id}#annotation-1"
    args = ["get-results-for-action", action_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz",
    }
    action_id = f"{provcrate1_rde_id}#12204f1e-758f-46e7-bad7-162768de3a5d"
    args = ["get-results-for-action", action_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz.tbi",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz",
    }
    action_id = "#not-present"
    args = ["get-results-for-action", action_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_get_run_params(crate_map):
    runner = CliRunner()
    crate_url = crate_map["provcrate1"]["url"]
    args = ["get-run-params", crate_url]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) == {
        "input: sample.csv",
        "foo: foo_value"
    }
    crate_url = crate_map["crate1"]["url"]
    args = ["get-run-params", crate_url]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""


def test_cli_list_graphs(crate_map):
    runner = CliRunner()
    args = ["list-graphs"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(result.stdout.splitlines()) >= {
        crate_map["crate1"]["url"],
        crate_map["crate2"]["url"],
        crate_map["provcrate1"]["url"],
        crate_map["proccrate1"]["url"],
        crate_map["proccrate2"]["url"],
    }


def test_cli_list_rde_graphs(crate_map):
    runner = CliRunner()
    args = ["list-rde-graphs"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    assert set(tuple(_.split()) for _ in result.stdout.splitlines()) >= {
        (crate_map["crate1"]["url"], crate_map["crate1"]["rde_id"]),
        (crate_map["crate2"]["url"], crate_map["crate2"]["rde_id"]),
        (crate_map["provcrate1"]["url"], crate_map["provcrate1"]["rde_id"]),
        (crate_map["proccrate1"]["url"], crate_map["proccrate1"]["rde_id"]),
        (crate_map["proccrate2"]["url"], crate_map["proccrate2"]["rde_id"]),
    }


def test_cli_backtrack(crate_map):
    runner = CliRunner()
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    result_id = "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    args = ["backtrack", result_id]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    items = [eval(_) for _ in result.stdout.splitlines()]
    assert len(items) >= 4
    assert items[0][0] == f"{proccrate2_rde_id}#normalization-1"
    assert set(items[0][1]) >= {
        f"{proccrate2_rde_id}aux.txt",
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    }
    assert set(items[0][2]) >= {
        "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz",
        "file:///path/to/logs",
    }
    assert items[1][0] == f"{proccrate1_rde_id}#annotation-1"
    assert set(items[1][1]) >= {
        f"{proccrate1_rde_id}aux.vcf",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    }
    assert set(items[1][2]) >= {
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    }
    assert items[2][0] == f"{provcrate1_rde_id}#12204f1e-758f-46e7-bad7-162768de3a5d"
    assert set(items[2][1]) >= {
        "file:///path/to/FOOBAR123_1.fastq.gz",
        "file:///path/to/FOOBAR123_2.fastq.gz",
        "file:///path/to/pipeline_info/software_versions.yml",
        "http://example.com/fooconfig.yml",
        f"{provcrate1_rde_id}sample.csv",
    }
    assert set(items[2][2]) >= {
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz.tbi",
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz"
    }
    assert items[3][0] == f"{provcrate1_rde_id}#publish/13fc2459df3405bf049e575f063aef3d/FOOBAR123.deepvariant.vcf.gz"
    assert items[3][1] == []  # object is not a file or directory
    assert set(items[3][2]) >= {
        "file:///path/to/FOOBAR123.deepvariant.vcf.gz",
    }


def test_cli_mv(crate_map):
    src = "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    dest = "file:///a/b/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    runner = CliRunner()
    args = ["mv", src, dest]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    bad_src = "arcp://uuid,9498d061-370c-53cb-a1ce-a575c5c76f64/"
    args = ["mv", bad_src, dest]
    result = runner.invoke(cli, args)
    assert result.exit_code != 0
    missing_src = f"file:///{str(uuid.uuid4())}"
    args = ["mv", missing_src, dest]
    result = runner.invoke(cli, args)
    assert result.exit_code != 0
    d_src = "file:///path/to/logs"
    d_dest = "file:///a/b/logs"
    args = ["mv", d_src, d_dest]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception

    # don't move dest back to src to avoid errors in
    # test_cli_get_objects_for_result when it's executed after this test
    # (e.g., in two consecutive runs of the whole test suite)

    dest2 = "file:///b/c/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    args = ["mv", dest, dest2, "--when", "2025-10-10T08:05:00Z"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
