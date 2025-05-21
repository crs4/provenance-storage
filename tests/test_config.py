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

from provstor.config import configure

CONF = """\
[minio]
user = foobar
"""


def test_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(str(tmp_path))
    from provstor.config import MINIO_USER
    try:
        HOME = Path.home()
    except RuntimeError:
        pass
    else:
        if not (HOME / ".provstor" / "config").is_file():
            assert MINIO_USER == "minio"
    with open("provstor.config", "wt") as f:
        f.write(CONF)
    configure()
    from provstor.config import MINIO_USER
    assert MINIO_USER == "foobar"
