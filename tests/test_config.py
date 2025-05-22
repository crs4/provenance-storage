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

from provstor.config import configure, CONFIG_BASENAME
import os

CONF = """\
[minio]
user = %s
"""


def test_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(str(tmp_path))
    from provstor.config import MINIO_USER
    try:
        HOME = Path.home()
    except RuntimeError:
        pass
    else:
        if not (HOME / ".config" / CONFIG_BASENAME).is_file():
            assert MINIO_USER == "minio"
    local_conf_file = Path(CONFIG_BASENAME)
    local_conf_file.write_text(CONF % "foobar")
    configure()
    from provstor.config import MINIO_USER
    assert MINIO_USER == "foobar"
    local_conf_file.unlink()
    subdir = Path("subdir")
    subdir.mkdir()
    home_conf_file = subdir / CONFIG_BASENAME
    os.environ["XDG_CONFIG_HOME"] = str(subdir)
    home_conf_file.write_text(CONF % "barfoo")
    configure()
    from provstor.config import MINIO_USER
    assert MINIO_USER == "barfoo"
