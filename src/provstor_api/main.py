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


from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
import uvicorn
import logging

from provstor_api.routes import upload, query, get, backtrack
from provstor_api.config import settings

logging.getLogger().setLevel(logging.INFO)

app = FastAPI(title="Provenance Storage API", version="1.0")

app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(get.router, prefix="/get", tags=["Get"])
app.include_router(backtrack.router, prefix="/backtrack", tags=["Backtrack"])


@app.get("/status/", tags=["Status"])
def check_status():
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    icon_file = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")
    return FileResponse(icon_file)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.dev_mode)
