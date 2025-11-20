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
from provstor_api.utils.gencrate import CopyCrateGenerator, MoveCrateGenerator
from provstor_api.utils.queries import IS_FILE_OR_DIR_QUERY, MOVE_DEST_QUERY
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


@router.post("/copy/")
async def copy(src: str, dest: str, when: datetime = None):
    return await _copy_or_move(src, dest, when=when, op="cp")


@router.post("/move/")
async def move(src: str, dest: str, when: datetime = None):
    return await _copy_or_move(src, dest, when=when, op="mv")


async def _copy_or_move(src: str, dest: str, when: datetime = None, op="cp"):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if when is None:
        when = now
    if when > now:
        raise HTTPException(status_code=422, detail=f"datetime {when.isoformat()} is in the future")
    if not src.startswith("file:/"):
        raise HTTPException(status_code=422, detail="Can only operate on a 'file:/' File or Dataset")
    qres = run_query(IS_FILE_OR_DIR_QUERY % src)
    if len(qres) < 1:
        raise HTTPException(status_code=404, detail=f"File or Dataset '{src}' not found")
    if op == "mv":
        chain = movechain(src)["result"]
        if chain:
            raise HTTPException(status_code=422, detail=f"'{src}' has already been moved to: {chain}")
    qres = run_query(FILEINFO_QUERY % src)
    kwargs = {"when": when}
    if len(qres) >= 1:
        # raise if > 1 ? (multiple checksums or sizes for an id)
        r = list(qres)[0]
        kwargs.update({"checksum": r.checksum.value, "size": r.size.value})
    gen_class = CopyCrateGenerator if op == "cp" else MoveCrateGenerator
    generator = gen_class(src, dest, **kwargs)
    crate = generator.generate()
    crate_filename = f"{str(uuid.uuid4())}.zip"
    logging.info("%s crate name: %s", op, crate_filename)
    with tempfile.TemporaryDirectory() as tmp_dir:
        crate_path = os.path.join(tmp_dir, crate_filename)
        crate.write_zip(crate_path)
        with open(crate_path, "rb") as f:
            upload_file = UploadFile(f, filename=crate_filename, headers={
                "content-type": "application/zip"
            })
            result = await load_crate_metadata(upload_file)
    return result


def _movechain_recursive(path_id, visited=None):
    if visited is None:
        visited = set()

    if path_id in visited:
        return []

    visited.add(path_id)
    results = []

    qres = run_query(MOVE_DEST_QUERY % path_id)

    if len(qres):
        dest_id = str(list(qres)[0][0])
        logging.info("dest_id: %s", dest_id)
        results.append(dest_id)
        nested_results = _movechain_recursive(dest_id, visited)
        results.extend(nested_results)

    return results


@router.get("/movechain")
def movechain(path_id: str):
    return {"result": _movechain_recursive(path_id)}
