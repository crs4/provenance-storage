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

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi.testclient import TestClient
import pytest
import io
import json
import zipfile
from unittest.mock import Mock, patch

# Import the app with proper module mocking
with patch.dict('sys.modules', {
    'routes.upload': Mock(),
    'routes.query': Mock(),
    'routes.get': Mock(),
    'routes.backtrack': Mock(),
    'config': Mock(),
    'utils.queries': Mock(),
    'utils.query': Mock(),
    'utils.get_utils': Mock()
}):
    from provstor_api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_zip_file():
    """Create a mock zip file with ro-crate-metadata.json."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        metadata = {
            "@context": "https://w3id.org/ro/crate/1.1/context",
            "@graph": [
                {
                    "@type": "CreativeWork",
                    "@id": "ro-crate-metadata.json",
                    "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                    "about": {"@id": "./"}
                },
                {
                    "@type": ["Dataset", "ComputationalWorkflow"],
                    "@id": "./",
                    "name": "Test Workflow"
                }
            ]
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

    @patch('provstor_api.routes.upload.Minio')
    @patch('provstor_api.routes.upload.SPARQLUpdateStore')
    @patch('provstor_api.routes.upload.Graph')
    @patch('provstor_api.routes.upload.arcp')
    def test_upload_crate_success(self, mock_arcp, mock_graph, mock_sparql_store, mock_minio, client, mock_zip_file):
        """Test successful crate upload."""
        # Mock MinIO client
        mock_minio_client = Mock()
        mock_minio_client.bucket_exists.return_value = True
        mock_minio_client.put_object.return_value = Mock()
        mock_minio.return_value = mock_minio_client

        # Mock SPARQL store and graph
        mock_store = Mock()
        mock_sparql_store.return_value = mock_store
        mock_graph_instance = Mock()
        mock_graph.return_value = mock_graph_instance
        mock_graph_instance.query.return_value = [("http://example.com/rde",)]

        # Mock arcp
        mock_arcp.arcp_location.return_value = "arcp://uuid,test-uuid/"

        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test_crate.zip", mock_zip_file, "application/zip")}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["result"] == "success"
        assert "crate_url" in result

    def test_upload_crate_invalid_content_type(self, client):
        """Test upload with invalid content type."""
        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test.txt", io.StringIO("test"), "text/plain")}
        )

        assert response.status_code == 415
        assert "crate_path must be a zip file" in response.json()["detail"]

    def test_upload_empty_file(self, client):
        """Test upload with empty file."""
        empty_file = io.BytesIO()
        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("empty.zip", empty_file, "application/zip")}
        )

        assert response.status_code == 400
        assert "Empty file uploaded" in response.json()["detail"]

    def test_upload_zip_without_metadata(self, client):
        """Test upload zip file without ro-crate-metadata.json."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            zip_file.writestr("some_file.txt", "content")
        buffer.seek(0)

        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test.zip", buffer, "application/zip")}
        )

        assert response.status_code == 404
        assert "ro-crate-metadata.json not found" in response.json()["detail"]


class TestQueryEndpoints:
    """Test query-related endpoints."""

    @patch('provstor_api.routes.query.run_query')
    def test_list_graphs(self, mock_run_query, client):
        """Test listing graphs."""
        mock_run_query.return_value = [
            ("http://example.com/graph1",),
            ("http://example.com/graph2",)
        ]

        response = client.get("/query/list-graphs/")
        assert response.status_code == 200
        result = response.json()
        assert len(result["result"]) == 2
        assert "http://example.com/graph1" in result["result"]
        assert "http://example.com/graph2" in result["result"]

    @patch('provstor_api.routes.query.run_query')
    def test_list_rde_graphs(self, mock_run_query, client):
        """Test listing RDE graphs."""
        mock_run_query.return_value = [
            ("http://example.com/rde1", "graph1"),
            ("http://example.com/rde2", "graph2")
        ]

        response = client.get("/query/list-RDE-graphs/")
        assert response.status_code == 200
        result = response.json()
        assert len(result["result"]) == 2

    @patch('provstor_api.routes.query.run_query')
    def test_run_query_sparql(self, mock_run_query, client):
        """Test running SPARQL query."""
        mock_run_query.return_value = [
            Mock(toPython=lambda: "result1"),
            Mock(toPython=lambda: "result2")
        ]

        query_content = "SELECT * WHERE { ?s ?p ?o }"
        query_file = io.StringIO(query_content)

        response = client.post(
            "/query/run-query/",
            files={"query_file": ("query.sparql", query_file, "text/plain")},
            params={"graph": "http://example.com/graph"}
        )

        assert response.status_code == 200
        result = response.json()
        assert len(result["result"]) == 2
        assert "result1" in result["result"]
        assert "result2" in result["result"]


class TestGetEndpoints:
    """Test get-related endpoints."""

    @patch('provstor_api.routes.get.run_query')
    @patch('provstor_api.routes.get.urlopen')
    def test_get_crate(self, mock_urlopen, mock_run_query, client):
        """Test getting a crate."""
        # Mock query result
        mock_run_query.return_value = [("http://minio:9000/crates/test_crate.zip",)]

        # Mock URL response
        mock_response = Mock()
        mock_response.read.return_value = b"zip content"
        mock_response.headers.get.return_value = "application/zip"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        response = client.get("/get/crate/?rde_id=http://example.com/rde1")
        assert response.status_code == 200

    @patch('provstor_api.routes.get.run_query')
    def test_get_crate_not_found(self, mock_run_query, client):
        """Test getting non-existent crate."""
        mock_run_query.return_value = []

        response = client.get("/get/crate/?rde_id=http://example.com/nonexistent")
        assert response.status_code == 404
        assert "Crate not found" in response.json()["detail"]

    @patch('provstor_api.routes.get.run_query')
    @patch('provstor_api.routes.get.urlopen')
    @patch('zipfile.ZipFile')
    def test_get_file(self, mock_zipfile, mock_urlopen, mock_run_query, client):
        """Test getting a file from crate."""
        # Mock query result
        mock_run_query.return_value = [("http://minio:9000/crates/test_crate.zip",)]

        # Mock URL response
        mock_response = Mock()
        mock_response.read.return_value = b"zip content"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Mock ZipFile
        mock_zip = Mock()
        mock_zip.read.return_value = b"file content"
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        response = client.get("/get/file/?file_uri=arcp://uuid,test-uuid/test_file.txt")
        assert response.status_code == 200

    def test_get_file_invalid_protocol(self, client):
        """Test getting file with invalid protocol."""
        response = client.get("/get/file/?file_uri=http://example.com/file.txt")
        assert response.status_code == 400
        assert "Unsupported protocol" in response.json()["detail"]


class TestBacktrackEndpoints:
    """Test backtrack-related endpoints."""

    @patch('provstor_api.routes.backtrack.fetch_actions_for_result')
    @patch('provstor_api.routes.backtrack.fetch_objects_for_action')
    @patch('provstor_api.routes.backtrack.fetch_results_for_action')
    def test_backtrack_with_result_id(self, mock_fetch_results, mock_fetch_objects, mock_fetch_actions, client):
        """Test backtracking with result ID."""
        mock_fetch_actions.return_value = ["action1"]
        mock_fetch_objects.return_value = ["object1"]
        mock_fetch_results.return_value = ["result1"]

        response = client.get("/backtrack/?result_id=http://example.com/result1")
        assert response.status_code == 200
        result = response.json()
        assert "result" in result

    @patch('provstor_api.routes.backtrack.run_query')
    @patch('provstor_api.routes.backtrack.fetch_actions_for_result')
    @patch('provstor_api.routes.backtrack.fetch_objects_for_action')
    @patch('provstor_api.routes.backtrack.fetch_results_for_action')
    def test_backtrack_with_file_uri(self, mock_fetch_results, mock_fetch_objects, mock_fetch_actions, mock_run_query, client):
        """Test backtracking with file URI."""
        # Mock query results
        mock_run_query.side_effect = [
            [("http://example.com/graph1",)],  # Graph ID query
            [("http://example.com/result1",)]  # Results query
        ]

        mock_fetch_actions.return_value = ["action1"]
        mock_fetch_objects.return_value = ["object1"]
        mock_fetch_results.return_value = ["result1"]

        response = client.get("/backtrack/?file_uri=arcp://uuid,test-uuid/file.txt")
        assert response.status_code == 200
        result = response.json()
        assert "result" in result

    def test_backtrack_missing_parameters(self, client):
        """Test backtracking without required parameters."""
        response = client.get("/backtrack/")
        assert response.status_code == 400
        assert "Either file_uri or result_id must be provided" in response.json()["detail"]

    @patch('provstor_api.routes.backtrack.run_query')
    def test_backtrack_file_not_found(self, mock_run_query, client):
        """Test backtracking with non-existent file."""
        mock_run_query.return_value = []

        response = client.get("/backtrack/?file_uri=arcp://uuid,nonexistent/file.txt")
        assert response.status_code == 404
        assert "No graphs found" in response.json()["detail"]


class TestIntegrationScenarios:
    """Integration test scenarios."""

    @patch('provstor_api.routes.upload.Minio')
    @patch('provstor_api.routes.upload.SPARQLUpdateStore')
    @patch('provstor_api.routes.upload.Graph')
    @patch('provstor_api.routes.upload.arcp')
    @patch('provstor_api.routes.query.run_query')
    def test_upload_and_query_workflow(self, mock_run_query, mock_arcp, mock_graph, mock_sparql_store, mock_minio, client, mock_zip_file):
        """Test complete workflow: upload crate then query it."""
        # Mock upload dependencies
        mock_minio_client = Mock()
        mock_minio_client.bucket_exists.return_value = True
        mock_minio_client.put_object.return_value = Mock()
        mock_minio.return_value = mock_minio_client

        mock_store = Mock()
        mock_sparql_store.return_value = mock_store
        mock_graph_instance = Mock()
        mock_graph.return_value = mock_graph_instance
        mock_graph_instance.query.return_value = [("http://example.com/rde",)]

        mock_arcp.arcp_location.return_value = "arcp://uuid,test-uuid/"

        # Upload crate
        upload_response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test_crate.zip", mock_zip_file, "application/zip")}
        )
        assert upload_response.status_code == 200

        # Query graphs
        mock_run_query.return_value = [("http://example.com/graph1",)]
        query_response = client.get("/query/list-graphs/")
        assert query_response.status_code == 200

    def test_error_handling_chain(self, client):
        """Test error handling across multiple endpoints."""
        # Test invalid upload
        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("test.txt", io.StringIO("invalid"), "text/plain")}
        )
        assert response.status_code == 415

        # Test invalid get request
        response = client.get("/get/crate/?rde_id=")
        assert response.status_code in [400, 404, 422]  # Various possible error codes


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('provstor_api.routes.upload.Minio')
    @patch('provstor_api.routes.upload.SPARQLUpdateStore')
    @patch('provstor_api.routes.upload.Graph')
    @patch('provstor_api.routes.upload.arcp')
    def test_large_metadata_file(self, mock_arcp, mock_graph, mock_sparql_store, mock_minio, client):
        """Test upload with large metadata file (should fail)."""
        # Create zip with large metadata
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            large_metadata = {"@context": "test"}
            # Create a metadata string larger than 50MB limit
            large_content = json.dumps(large_metadata) + ("x" * 50_000_001)
            zip_file.writestr("ro-crate-metadata.json", large_content)
        buffer.seek(0)

        response = client.post(
            "/upload/crate/",
            files={"crate_path": ("large_crate.zip", buffer, "application/zip")}
        )

        assert response.status_code == 413
        assert "exceeds size limit" in response.json()["detail"]

    @patch('provstor_api.routes.query.run_query')
    def test_empty_query_results(self, mock_run_query, client):
        """Test handling of empty query results."""
        mock_run_query.return_value = []

        response = client.get("/query/list-graphs/")
        assert response.status_code == 200
        assert response.json()["result"] == []

    @patch('provstor_api.routes.backtrack.fetch_actions_for_result')
    def test_backtrack_circular_dependency(self, mock_fetch_actions, client):
        """Test backtracking handles circular dependencies."""
        # This should not cause infinite recursion due to visited set
        mock_fetch_actions.return_value = []

        response = client.get("/backtrack/?result_id=http://example.com/circular")
        assert response.status_code == 404  # No results found


if __name__ == "__main__":
    pytest.main([__file__])
