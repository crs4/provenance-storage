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
import os
import tempfile
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile

from provstor_api.routes.upload import load_crate_metadata
from provstor_api.utils.gencrate import MoveCrateGenerator
from provstor_api.utils.queries import IS_FILE_OR_DIR_QUERY
from provstor_api.utils.query import run_query

router = APIRouter()


FILEINFO_QUERY = """\
PREFIX schema: <http://schema.org/>
PREFIX wfrun: <https://w3id.org/ro/terms/workflow-run#>

SELECT DISTINCT ?checksum ?size
WHERE {
  ?id a schema:MediaObject .
  ?id wfrun:sha256 ?checksum .
  ?id schema:contentSize ?size .
  FILTER(?id = <%s>)
}
"""


@router.post("/move/")
async def move(src: str, dest: str, when: datetime = None):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if when is None:
        when = now
    if when > now:
        raise HTTPException(status_code=422, detail=f"datetime {when.isoformat()} is in the future")
    if not src.startswith("file:/"):
        raise HTTPException(status_code=422, detail="Can only move a 'file:/' File or Dataset")
    qres = run_query(IS_FILE_OR_DIR_QUERY % src)
    if len(qres) < 1:
        raise HTTPException(status_code=404, detail=f"File or Dataset '{src}' not found")
    qres = run_query(FILEINFO_QUERY % src)
    kwargs = {"when": when}
    if len(qres) >= 1:
        # raise if > 1 ? (multiple checksums or sizes for an id)
        r = list(qres)[0]
        kwargs.update({"checksum": r.checksum.value, "size": r.size.value})
    generator = MoveCrateGenerator(src, dest, **kwargs)
    crate = generator.generate()
    crate_filename = f"{str(uuid.uuid4())}.zip"
    logging.info("move crate name: %s", crate_filename)
    with tempfile.TemporaryDirectory() as tmp_dir:
        crate_path = os.path.join(tmp_dir, crate_filename)
        crate.write_zip(crate_path)
        with open(crate_path, "rb") as f:
            upload_file = UploadFile(f, filename=crate_filename, headers={
                "content-type": "application/zip"
            })
            result = await load_crate_metadata(upload_file)
    return result
