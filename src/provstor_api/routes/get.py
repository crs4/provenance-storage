from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from provstor_api.utils.query import run_query
from provstor_api.utils.queries import (
    GRAPHS_QUERY, CRATE_URL_QUERY, GRAPH_ID_FOR_FILE_QUERY,
    GRAPH_ID_FOR_RESULT_QUERY, WORKFLOW_QUERY
)
import logging
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlsplit
import shutil
import zipfile
import tempfile
from rdflib.term import Literal

router = APIRouter()


@router.get("/crate/")
async def get_crate(rde_id: str, outdir: str):
    try:
        outdir = Path(outdir)

        if not outdir.is_absolute():
            raise HTTPException(status_code=400, detail="The destination directory must be an absolute path")

        rde_id = rde_id.rstrip("/") + "/"
        qres = run_query(CRATE_URL_QUERY % rde_id)

        if len(qres) < 1:
            raise HTTPException(status_code=404, detail="Crate not found")

        crate_url = str(list(qres)[0][0])
        logging.info("crate URL: %s", crate_url)
        out_path = outdir / crate_url.rsplit("/", 1)[-1]
        logging.info("downloading to: %s", out_path)

        with urlopen(crate_url) as response, out_path.open("wb") as f:
            shutil.copyfileobj(response, f)

        return FileResponse(
            path=out_path,
            filename=out_path.name,
            media_type='application/zip',
            headers={"download_path": str(out_path)}
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading crate: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

