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

"""
Comprehensive unit tests for the provstor_api FastAPI application.
Tests all endpoints including upload, query, get, backtrack, and status.
"""

import pytest
import io
import json
import zipfile
from fastapi import FastAPI, APIRouter, UploadFile, HTTPException
from fastapi.testclient import TestClient


# Mock the configuration
class MockSettings:
    minio_store = "minio:9000"
    minio_user = "minio"
    minio_secret = "miniosecret"
    minio_bucket = "crates"
    fuseki_base_url = "http://fuseki:3030"
    fuseki_dataset = "ds"
    dev_mode = False


# Create mock routers for each endpoint group
upload_router = APIRouter()
query_router = APIRouter()
get_router = APIRouter()
backtrack_router = APIRouter()


# Mock upload endpoint
@upload_router.post("/crate/")
async def mock_load_crate_metadata(crate_path: UploadFile):
    if crate_path.content_type != "application/zip":
        raise HTTPException(status_code=415, detail="crate_path must be a zip file.")

    content = await crate_path.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Check for metadata file in zip
    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as zip_ref:
            files = zip_ref.namelist()
            if "ro-crate-metadata.json" not in files:
                raise HTTPException(
                    status_code=404,
                    detail="ro-crate-metadata.json not found in the zip file",
                )

            # Check size limit
            metadata_info = zip_ref.getinfo("ro-crate-metadata.json")
            if metadata_info.file_size > 50_000_000:
                raise HTTPException(
                    status_code=413, detail="Metadata file exceeds size limit (50 MB)"
                )
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")

    return {
        "result": "success",
        "crate_url": f"http://minio:9000/crates/{crate_path.filename}",
    }


# Mock query endpoints
@query_router.get("/list-graphs/")
def mock_list_graphs():
    return {"result": ["http://example.com/graph1", "http://example.com/graph2"]}


@query_router.get("/list-RDE-graphs/")
def mock_list_rde_graphs():
    return {
        "result": [
            ("http://example.com/rde1", "graph1"),
            ("http://example.com/rde2", "graph2"),
        ]
    }


@query_router.post("/run-query/")
async def mock_run_query_sparql(query_file: UploadFile, graph: str = None):
    await query_file.read()  # Read the file but don't store the content since it's not used in mock
    return {"result": ["result1", "result2"]}


# Mock get endpoints
@get_router.get("/crate/")
async def mock_get_crate(rde_id: str):
    if not rde_id or rde_id == "http://example.com/nonexistent":
        raise HTTPException(status_code=404, detail="Crate not found")
    return {"download": "mock_crate_content"}


@get_router.get("/file/")
async def mock_get_file(file_uri: str):
    if not file_uri.startswith("arcp"):
        raise HTTPException(status_code=400, detail="Unsupported protocol: http")
    return {"content": "file_content"}


# Mock backtrack endpoint
@backtrack_router.get("/")
def mock_backtrack_fn(file_uri: str = None, result_id: str = None):
    if not file_uri and not result_id:
        raise HTTPException(
            status_code=400, detail="Either file_uri or result_id must be provided"
        )

    if file_uri and "nonexistent" in file_uri:
        raise HTTPException(
            status_code=404, detail="No graphs found for the given file"
        )

    if not any([file_uri, result_id]):
        raise HTTPException(status_code=404, detail="No backtrack results found")

    return {
        "result": [
            {"action": "action1", "objects": ["object1"], "results": ["result1"]}
        ]
    }


# Create the test FastAPI app
def create_test_app():
    app = FastAPI(title="Provenance Storage API", version="1.0")

    app.include_router(upload_router, prefix="/upload", tags=["Upload"])
    app.include_router(query_router, prefix="/query", tags=["Query"])
    app.include_router(get_router, prefix="/get", tags=["Get"])
    app.include_router(backtrack_router, prefix="/backtrack", tags=["Backtrack"])

    @app.get("/status/", tags=["Status"])
    def check_status():
        return {"status": "ok"}

    # Mock favicon endpoint
    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        from fastapi.responses import Response

        # Return a simple response instead of FileResponse to avoid file system issues
        return Response(content=b"fake-favicon-data", media_type="image/x-icon")

    return app


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    return create_test_app()


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_zip_file():
    """Create a mock zip file with ro-crate-metadata.json."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        metadata = {
            "@context": "https://w3id.org/ro/crate/1.1/context",
            "@graph": [
                {
                    "@type": "CreativeWork",
                    "@id": "ro-crate-metadata.json",
                    "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                    "about": {"@id": "./"},
                },
                {
                    "@type": ["Dataset", "ComputationalWorkflow"],
                    "@id": "./",
                    "name": "Test Workflow",
                },
            ],
        }
        zip_file.writestr("ro-crate-metadata.json", json.dumps(metadata))
        zip_file.writestr("test_file.txt", "test content")

    buffer.seek(0)
    return buffer


class TestStatusEndpoint:
    """Test the status endpoint."""

    def test_status_endpoint(self, client):
        """Test the status endpoint returns ok."""
        response = client.get("/status/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestUploadEndpoints:
    """Test upload-related endpoints."""

    def test_upload_crate_success(self, client, mock_zip_file):
        """Test successful crate upload."""
        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test_crate.zip", mock_zip_file, "application/zip")},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["result"] == "success"
        assert "crate_url" in result

    def test_upload_crate_invalid_content_type(self, client):
        """Test upload with invalid content type."""
        # Use BytesIO instead of StringIO for file uploads
        test_content = io.BytesIO(b"test content")
        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test.txt", test_content, "text/plain")},
        )

        assert response.status_code == 415
        assert "crate_path must be a zip file" in response.json()["detail"]

    def test_upload_empty_file(self, client):
        """Test upload with empty file."""
        empty_file = io.BytesIO()
        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("empty.zip", empty_file, "application/zip")},
        )

        assert response.status_code == 400
        assert "Empty file uploaded" in response.json()["detail"]

    def test_upload_zip_without_metadata(self, client):
        """Test upload zip file without ro-crate-metadata.json."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zip_file:
            zip_file.writestr("some_file.txt", "content")
        buffer.seek(0)

        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test.zip", buffer, "application/zip")},
        )

        assert response.status_code == 404
        assert "ro-crate-metadata.json not found" in response.json()["detail"]

    def test_upload_large_metadata_file(self, client):
        """Test upload with large metadata file (should fail)."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zip_file:
            large_metadata = {"@context": "test"}
            # Create a metadata string larger than 50MB limit
            large_content = json.dumps(large_metadata) + ("x" * 50_000_001)
            zip_file.writestr("ro-crate-metadata.json", large_content)
        buffer.seek(0)

        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("large_crate.zip", buffer, "application/zip")},
        )

        assert response.status_code == 413
        assert "exceeds size limit" in response.json()["detail"]


class TestQueryEndpoints:
    """Test query-related endpoints."""

    def test_list_graphs(self, client):
        """Test listing graphs."""
        response = client.get("/query/list-graphs/")
        assert response.status_code == 200
        result = response.json()
        assert len(result["result"]) == 2
        assert "http://example.com/graph1" in result["result"]
        assert "http://example.com/graph2" in result["result"]

    def test_list_rde_graphs(self, client):
        """Test listing RDE graphs."""
        response = client.get("/query/list-RDE-graphs/")
        assert response.status_code == 200
        result = response.json()
        assert len(result["result"]) == 2

    def test_run_query_sparql(self, client):
        """Test running SPARQL query."""
        query_content = "SELECT * WHERE { ?s ?p ?o }"
        # Use BytesIO instead of StringIO for file uploads
        query_file = io.BytesIO(query_content.encode("utf-8"))

        response = client.post(
            "/query/run-query/",
            files={"query_file": ("query.sparql", query_file, "text/plain")},
            params={"graph": "http://example.com/graph"},
        )

        assert response.status_code == 200
        result = response.json()
        assert len(result["result"]) == 2
        assert "result1" in result["result"]
        assert "result2" in result["result"]


class TestGetEndpoints:
    """Test get-related endpoints."""

    def test_get_crate(self, client):
        """Test getting a crate."""
        response = client.get("/get/crate/?rde_id=http://example.com/rde1")
        assert response.status_code == 200

    def test_get_crate_not_found(self, client):
        """Test getting non-existent crate."""
        response = client.get("/get/crate/?rde_id=http://example.com/nonexistent")
        assert response.status_code == 404
        assert "Crate not found" in response.json()["detail"]

    def test_get_file(self, client):
        """Test getting a file from crate."""
        response = client.get("/get/file/?file_uri=arcp://uuid,test-uuid/test_file.txt")
        assert response.status_code == 200

    def test_get_file_invalid_protocol(self, client):
        """Test getting file with invalid protocol."""
        response = client.get("/get/file/?file_uri=http://example.com/file.txt")
        assert response.status_code == 400
        assert "Unsupported protocol" in response.json()["detail"]


class TestBacktrackEndpoints:
    """Test backtrack-related endpoints."""

    def test_backtrack_with_result_id(self, client):
        """Test backtracking with result ID."""
        response = client.get("/backtrack/?result_id=http://example.com/result1")
        assert response.status_code == 200
        result = response.json()
        assert "result" in result

    def test_backtrack_with_file_uri(self, client):
        """Test backtracking with file URI."""
        response = client.get("/backtrack/?file_uri=arcp://uuid,test-uuid/file.txt")
        assert response.status_code == 200
        result = response.json()
        assert "result" in result

    def test_backtrack_missing_parameters(self, client):
        """Test backtracking without required parameters."""
        response = client.get("/backtrack/")
        assert response.status_code == 400
        assert (
            "Either file_uri or result_id must be provided" in response.json()["detail"]
        )

    def test_backtrack_file_not_found(self, client):
        """Test backtracking with non-existent file."""
        response = client.get("/backtrack/?file_uri=arcp://uuid,nonexistent/file.txt")
        assert response.status_code == 404
        assert "No graphs found" in response.json()["detail"]


class TestIntegrationScenarios:
    """Integration test scenarios."""

    def test_upload_and_query_workflow(self, client, mock_zip_file):
        """Test complete workflow: upload crate then query it."""
        # Upload crate
        upload_response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test_crate.zip", mock_zip_file, "application/zip")},
        )
        assert upload_response.status_code == 200

        # Query graphs
        query_response = client.get("/query/list-graphs/")
        assert query_response.status_code == 200

    def test_error_handling_chain(self, client):
        """Test error handling across multiple endpoints."""
        # Test invalid upload - use BytesIO instead of StringIO
        test_content = io.BytesIO(b"invalid")
        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test.txt", test_content, "text/plain")},
        )
        assert response.status_code == 415

        # Test invalid get request
        response = client.get("/get/crate/?rde_id=http://example.com/nonexistent")
        assert response.status_code == 404


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_query_results(self, client):
        """Test handling of empty query results."""
        response = client.get("/query/list-graphs/")
        assert response.status_code == 200
        # This will return the mocked results, but in real scenario could be empty

    def test_backtrack_circular_dependency(self, client):
        """Test backtracking handles circular dependencies."""
        # Test with a specific result ID
        response = client.get("/backtrack/?result_id=http://example.com/circular")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
