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


@router.get("/file/")
async def get_file(file_uri: str, outdir: str):
    try:
        outdir = Path(outdir)

        if not outdir.is_absolute():
            raise HTTPException(status_code=400, detail="The destination directory must be an absolute path")

        if file_uri.startswith("http"):
            out_path = outdir / file_uri.rsplit("/", 1)[-1]
            with urlopen(file_uri) as response, out_path.open("wb") as f:
                shutil.copyfileobj(response, f)
            return FileResponse(
                path=out_path,
                filename=out_path.name,
                media_type='application/octet-stream',
                headers={"download_path": str(out_path)}
            )
        elif not file_uri.startswith("arcp"):
            raise ValueError(f"{file_uri}: unsupported protocol")
        res = urlsplit(file_uri)
        rde_id = f"{res.scheme}://{res.netloc}/"
        zip_dir = Path(tempfile.mkdtemp())
        zip_path = await get_crate(rde_id, outdir=zip_dir)
        zip_member = res.path.lstrip("/")
        logging.info("extracting: %s", zip_member)
        with zipfile.ZipFile(zip_path.path, "r") as zipf:
            out_path = zipf.extract(zip_member, path=outdir)
        shutil.rmtree(zip_dir)
        download_file = zip_member.rsplit("/", 1)[-1]

        return FileResponse(
            path=out_path,
            filename=download_file,
            media_type='application/zip',
            headers={"download_path": str(out_path)}
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/graphs-for-file/")
def get_graphs_for_file(file_id: str):
    try:
        query_res = run_query(GRAPH_ID_FOR_FILE_QUERY % file_id)
        output = next(iter(query_res), None)
        result = output[0] if output is not None else Literal('')
        return {"result": result}
    except Exception as e:
        logging.error(f"Error retrieving graph from input file: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to retrieve graph from input file: {str(e)}")


@router.get("/graphs-for-result/")
def get_graphs_for_result(result_id: str):
    try:
        query_res = run_query(GRAPH_ID_FOR_RESULT_QUERY % result_id)
        output = next(iter(query_res), None)
        result = output[0] if output is not None else Literal('')
        return {"result": result}
    except Exception as e:
        logging.error(f"Error retrieving graph from input file: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to retrieve graph from input file: {str(e)}")

