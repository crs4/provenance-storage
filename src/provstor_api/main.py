from provstor.config import API_HOST, API_PORT
from fastapi import FastAPI
from fastapi.responses import FileResponse
from routes import upload, query, get, backtrack
import os
import uvicorn
import logging

logging.getLogger().setLevel(logging.INFO)

app = FastAPI(title="Provenance Storage API", version="1.0")

app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(get.router, prefix="/get", tags=["Get"])
app.include_router(backtrack.router, prefix="/backtrack", tags=["Backtrack"])
app.include_router(backtrack.router, prefix="/backtrack", tags=["Backtrack"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])


@app.get("/status/", tags=["Status"])
def check_status():
    return {"status": "ok"}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    icon_file = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")
    return FileResponse(icon_file)

if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)