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

from fastapi import APIRouter, HTTPException, UploadFile
from routes.upload import load_crate_metadata
from utils.gencrate import MoveCrateGenerator
from utils.queries import IS_FILE_QUERY
from utils.query import run_query

router = APIRouter()


@router.post("/move/")
async def move(src: str = None, dest: str = None):
    qres = run_query(IS_FILE_QUERY % src)
    if len(qres) < 1:
        raise HTTPException(status_code=404, detail=f"File '{src}' not found")
    generator = MoveCrateGenerator(src, dest)
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
