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

from provstor.backtrack import backtrack


def test_backtrack(crate_map):
    proccrate2_rde_id = crate_map["proccrate2"]["rde_id"]
    proccrate1_rde_id = crate_map["proccrate1"]["rde_id"]
    provcrate1_rde_id = crate_map["provcrate1"]["rde_id"]
    result_id = "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz"
    items = list(backtrack(result_id))
    assert len(items) >= 3
    assert items[0][0] == f"{proccrate2_rde_id}#normalization-1"
    assert set(items[0][1]) >= {
        f"{proccrate2_rde_id}aux.txt",
        "file:///path/to/FOOBAR123.deepvariant.ann.vcf.gz"
    }
    assert set(items[0][2]) >= {
        "file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz"
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
