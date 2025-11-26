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

import io
import zipfile
import pytest
from rdflib import URIRef
from types import SimpleNamespace

from fastapi.testclient import TestClient
from provstor_api.main import app
from provstor_api.utils.queries import IS_FILE_OR_DIR_QUERY
import provstor_api.routes.upload as upload
import provstor_api.routes.query as query
import provstor_api.routes.backtrack as backtrack
import provstor_api.routes.get as get
import provstor_api.routes.pathops as pathops


# Test Constants
class TestConstants:
    # URLs and URIs
    MINIO_URL = "http://minio:9000"
    MINIO_STORE = "minio:9000"
    MINIO_BUCKET = "crates"
    FUSEKI_URL = "http://fuseki:3030"
    FUSEKI_DATASET = "ds"

    # Example URIs
    EXAMPLE_URI = "http://example.org"
    EXAMPLE_RDE_URI = f"{EXAMPLE_URI}/rde"
    EXAMPLE_FILE_URI = f"{EXAMPLE_URI}/file1"
    EXAMPLE_GRAPH_URI_1 = f"{EXAMPLE_URI}/g1"
    EXAMPLE_GRAPH_URI_2 = f"{EXAMPLE_URI}/g2"
    EXAMPLE_RDE_1 = f"{EXAMPLE_URI}/rde1"
    EXAMPLE_RDE_2 = f"{EXAMPLE_URI}/rde2"

    # ARCP URIs
    ARCP_LOCATION = "arcp://example/root"
    ARCP_RDE_1 = "arcp://rde-1"
    ARCP_FILE_TXT = f"{ARCP_RDE_1}/dir/file.txt"
    ARCP_FILE_DAT = f"{ARCP_RDE_1}/x/y/file.dat"
    ARCP_FILE_MISSING = f"{ARCP_RDE_1}/dir/missing.txt"

    # file:/ URIs
    FILE_URI_A = "file:/a/f.txt"
    FILE_URI_B = "file:/b/f.txt"
    FILE_URI_C = "file:/c/f.txt"

    # File names and paths
    CRATE_ZIP = "crate.zip"
    ANOTHER_ZIP = "another.zip"
    METADATA_JSON = "ro-crate-metadata.json"
    METADATA_CONTEXT = '{"@context": "https://w3id.org/ro/crate/1.1/context"}'

    # Content types
    CONTENT_TYPE_ZIP = "application/zip"
    CONTENT_TYPE_PLAIN = "text/plain"
    CONTENT_TYPE_OCTET = "application/octet-stream"

    # IDs
    GRAPH_ID_1 = "g1"
    GRAPH_ID_2 = "g2"
    GRAPH_ID_3 = "g-3"
    GRAPH_ID_9 = "g-9"
    RESULT_ID_123 = "res-123"
    RESULT_ID_ABC = "res-abc"
    RESULT_ID_XYZ = "res-xyz"
    RESULT_ID_42 = "res-42"
    RESULT_ID_7 = "res-7"
    RESULT_ID_8 = "res-8"
    FILE_ID_123 = "file-123"
    ACTION_ID_1 = "act-1"
    ACTION_ID_2 = "act-2"
    WORKFLOW_1 = "wf1"
    WORKFLOW_2 = "wf2"

    # Query placeholders
    QUERY_PLACEHOLDER_Q1 = "Q1:%s"
    QUERY_PLACEHOLDER_Q2 = "Q2"
    QUERY_SELECT_ALL = "SELECT * WHERE { ?s ?p ?o }"
    QUERY_CONSTRUCT = "CONSTRUCT {} WHERE {}"

    # File content
    ZIP_DATA = b"ZIPDATA"
    GENERIC_DATA = b"DATA"
    FILE_CONTENT = b"Content file"
    BINARY_CONTENT = b"\x00\x01"
    README_CONTENT = b"Readme file"


TC = TestConstants

client = TestClient(app)


def make_zip(with_metadata=True, metadata_name=TC.METADATA_JSON):
    """Return a BytesIO containing a zip file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        if with_metadata:
            z.writestr(f"crate/{metadata_name}", TC.METADATA_CONTEXT.encode())
        else:
            z.writestr("README.txt", TC.README_CONTENT)
    buf.seek(0)
    return buf


def make_zip_bytes(files: dict[str, bytes]) -> bytes:
    """Return bytes of a zip containing {path: data}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for path, data in files.items():
            z.writestr(path, data)
    return buf.getvalue()


@pytest.fixture
def mock_client(monkeypatch):
    class MockMinio:
        def __init__(self, **kw):
            pass

        def bucket_exists(self, **kw):
            return True

        def make_bucket(self, **kw):
            pass

        def set_bucket_policy(self, **kw):
            pass

        def put_object(self, **kw):
            pass

    class MockStore:
        def open(self, endpoints):
            self.endpoints = endpoints

    class MockGraph:
        def __init__(self, store=None, identifier=None):
            self.store = store
            self.identifier = identifier

        def parse(self, path, publicID=None):
            self.parsed = (path, publicID)

        def query(self, _):
            return [(URIRef(TC.EXAMPLE_RDE_URI),)]

        def add(self, triple):
            self.added = triple

        def serialize(self, format="nt"):
            return "Lorem Ipsum"

        def update(self, insert_query):
            self.insert_query = insert_query

    monkeypatch.setattr(upload, "Minio", MockMinio)
    monkeypatch.setattr(upload, "SPARQLUpdateStore", MockStore)
    monkeypatch.setattr(upload, "Graph", MockGraph)
    monkeypatch.setattr(upload, "run_query", lambda q: [])
    monkeypatch.setattr(upload.arcp, "arcp_location", lambda url: TC.ARCP_LOCATION)

    upload.settings.minio_store = TC.MINIO_STORE
    upload.settings.minio_bucket = TC.MINIO_BUCKET
    upload.settings.fuseki_base_url = TC.FUSEKI_URL
    upload.settings.fuseki_dataset = TC.FUSEKI_DATASET

    return TestClient(app)


# Tests for upload crate
def test_check_status():
    response = client.get("/status/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rejects_non_zip(mock_client):
    r = mock_client.post("/upload/crate/",
                         files={"crate_path": ("not_zip_file.txt", b"not zip", TC.CONTENT_TYPE_PLAIN)})
    assert r.status_code == 415
    assert r.json()["detail"] == "crate_path must be a zip file."


def test_rejects_empty_file(mock_client):
    r = mock_client.post("/upload/crate/",
                         files={"crate_path": ("empty_file.zip", b"", TC.CONTENT_TYPE_ZIP)})
    assert r.status_code == 400
    assert r.json()["detail"] == "Empty file uploaded."


def test_rejects_missing_metadata(mock_client):
    buf = make_zip(with_metadata=False)
    r = mock_client.post("/upload/crate/",
                         files={"crate_path": (TC.CRATE_ZIP, buf.getvalue(), TC.CONTENT_TYPE_ZIP)})
    assert r.status_code == 422
    assert r.json()["detail"] == f"{TC.METADATA_JSON} not found in the zip file"


def test_correct_path(mock_client):
    buf = make_zip(with_metadata=True)
    r = mock_client.post("/upload/crate/",
                         files={"crate_path": (TC.CRATE_ZIP, buf.getvalue(), TC.CONTENT_TYPE_ZIP)})
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "success"
    assert body["crate_url"] == f"{TC.MINIO_URL}/{TC.MINIO_BUCKET}/{TC.CRATE_ZIP}"


def test_upload_existing_result(mock_client, monkeypatch):
    buf = make_zip(with_metadata=True)
    monkeypatch.setattr(upload, "run_query", lambda q: [(URIRef(TC.EXAMPLE_RDE_URI),)])
    r = mock_client.post("/upload/crate/",
                         files={"crate_path": (TC.CRATE_ZIP, buf.getvalue(), TC.CONTENT_TYPE_ZIP)})
    assert r.status_code == 422
    assert r.json()["detail"] == f"these results already exist: {{'{TC.EXAMPLE_RDE_URI}'}}"


# Tests for list-graphs
def test_list_graphs_ok(monkeypatch):

    def mock_run_query(q):
        return [(TC.EXAMPLE_GRAPH_URI_1,), (TC.EXAMPLE_GRAPH_URI_2,)]

    monkeypatch.setattr(query, "run_query", mock_run_query)

    r = client.get("/query/list-graphs/")
    assert r.status_code == 200
    assert r.json() == {"result": [TC.EXAMPLE_GRAPH_URI_1, TC.EXAMPLE_GRAPH_URI_2]}


def test_list_graphs_empty(monkeypatch):
    monkeypatch.setattr(query, "run_query", lambda q: [])

    r = client.get("/query/list-graphs/")
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for list-rde-graphs
def test_list_rde_graphs_ok(monkeypatch):

    def mock_run_query(q):
        return [
            (TC.EXAMPLE_RDE_1, "rde1"),
            (TC.EXAMPLE_RDE_2, "rde2")
        ]

    monkeypatch.setattr(query, "run_query", mock_run_query)

    r = client.get("/query/list-RDE-graphs/")
    assert r.status_code == 200
    assert r.json() == {
        "result": [
            [TC.EXAMPLE_RDE_1, 'rde1'],
            [TC.EXAMPLE_RDE_2, 'rde2']
        ]
    }


def test_list_rde_graphs_empty(monkeypatch):
    monkeypatch.setattr(query, "run_query", lambda q: [])

    r = client.get("/query/list-RDE-graphs/")
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for run query sparql
def test_run_query_plain_items_ok(monkeypatch):
    called = {}

    def mock_run_query(q, graph):
        called["query"] = q
        called["graph"] = graph
        return ["a", "b", "c"]

    monkeypatch.setattr(query, "run_query", mock_run_query)

    r = client.post(
        "/query/run-query/",
        files={"query_file": ("query.txt", TC.QUERY_SELECT_ALL.encode(), TC.CONTENT_TYPE_PLAIN)},
    )
    assert r.status_code == 200
    assert r.json() == {"result": ["a", "b", "c"]}
    assert "SELECT *" in called["query"]
    assert called["graph"] is None


def test_run_query_with_graph_param(monkeypatch):
    called = {}

    def mock_run_query(q, graph):
        called["query"] = q
        called["graph"] = graph
        return []

    monkeypatch.setattr(query, "run_query", mock_run_query)

    r = client.post(
        "/query/run-query/",
        files={"query_file": ("query.txt", TC.QUERY_CONSTRUCT.encode(), TC.CONTENT_TYPE_PLAIN)},
        params={"graph": TC.EXAMPLE_GRAPH_URI_1}
    )
    assert r.status_code == 200
    assert r.json() == {"result": []}
    assert called["graph"] == TC.EXAMPLE_GRAPH_URI_1


# Tests for backtrack endpoint
def test_backtrack_no_results(monkeypatch):
    monkeypatch.setattr(backtrack, "_backtrack_recursive", lambda rid: [])
    r = client.get("/backtrack/", params={"result_id": TC.RESULT_ID_123})
    assert r.status_code == 200
    assert r.json() == {"result": []}


def test_backtrack_success(monkeypatch):
    captured = {}

    def mock_bt(rid):
        captured["rid"] = rid
        return [{"id": rid, "steps": 3}]

    monkeypatch.setattr(backtrack, "_backtrack_recursive", mock_bt)

    r = client.get("/backtrack/", params={"result_id": TC.RESULT_ID_ABC})
    assert r.status_code == 200
    assert r.json() == {"result": [{"id": TC.RESULT_ID_ABC, "steps": 3}]}
    assert captured["rid"] == TC.RESULT_ID_ABC


# Tests for get crate
def test_get_crate_not_found(monkeypatch):
    monkeypatch.setattr(get, "CRATE_URL_QUERY", "SELECT ... %s ...")
    monkeypatch.setattr(get, "run_query", lambda q: [])

    r = client.get("/get/crate/", params={"rde_id": TC.RESULT_ID_123})
    assert r.status_code == 404
    assert r.json()["detail"] == f"No crate found for '{TC.RESULT_ID_123}/'"


def test_get_crate_ok_with_content_type(monkeypatch):
    called = {}
    monkeypatch.setattr(get, "CRATE_URL_QUERY", "Q:%s")

    def mock_run_query(q):
        called["query"] = q
        return [(f"{TC.MINIO_URL}/{TC.MINIO_BUCKET}/{TC.CRATE_ZIP}",)]

    monkeypatch.setattr(get, "run_query", mock_run_query)

    class MockResp:
        def __init__(self):
            self.headers = {"Content-Type": TC.CONTENT_TYPE_ZIP}

        def read(self):
            return TC.ZIP_DATA

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(get, "urlopen", lambda url: MockResp())

    r = client.get("/get/crate/", params={"rde_id": TC.RESULT_ID_123})
    assert r.status_code == 200
    assert r.content == TC.ZIP_DATA
    assert r.headers["Content-Disposition"] == f"attachment; filename={TC.CRATE_ZIP}"
    assert r.headers["content-type"] == TC.CONTENT_TYPE_ZIP
    assert called["query"] == f"Q:{TC.RESULT_ID_123}/"


def test_get_crate_ok_defaults_content_type(monkeypatch):
    monkeypatch.setattr(get, "CRATE_URL_QUERY", "Q:%s")
    monkeypatch.setattr(get, "run_query",
                        lambda q: [(f"{TC.MINIO_URL}/{TC.MINIO_BUCKET}/{TC.ANOTHER_ZIP}",)])

    class MockRespNoCT:
        def __init__(self):
            self.headers = {}

        def read(self):
            return TC.GENERIC_DATA

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(get, "urlopen", lambda url: MockRespNoCT())

    r = client.get("/get/crate/", params={"rde_id": f"{TC.EXAMPLE_URI}/rde/42/"})
    assert r.status_code == 200
    assert r.content == TC.GENERIC_DATA
    assert r.headers["Content-Disposition"] == f"attachment; filename={TC.ANOTHER_ZIP}"
    assert r.headers["content-type"] == TC.CONTENT_TYPE_ZIP


# Tests for get file
def test_get_file_unsupported_protocol():
    r = client.get("/get/file/", params={"file_uri": TC.EXAMPLE_FILE_URI})
    assert r.status_code == 400
    assert r.json()["detail"] == "Unsupported protocol: http"


def test_get_file_crate_not_found(monkeypatch):
    monkeypatch.setattr(get, "CRATE_URL_QUERY", "Q:%s")
    monkeypatch.setattr(get, "run_query", lambda q: [])

    r = client.get("/get/file/", params={"file_uri": TC.ARCP_FILE_TXT})
    assert r.status_code == 404
    assert r.json()["detail"] == f"No crate found for '{TC.ARCP_RDE_1}/'"


def test_get_file_ok_with_mapped_content_type(monkeypatch):
    monkeypatch.setattr(get, "CRATE_URL_QUERY", "Q:%s")
    monkeypatch.setattr(get, "run_query",
                        lambda q: [(f"{TC.MINIO_URL}/{TC.MINIO_BUCKET}/{TC.CRATE_ZIP}",)])
    monkeypatch.setattr(get, "content_type_map", {"txt": TC.CONTENT_TYPE_PLAIN})

    zip_bytes = make_zip_bytes({"dir/file.txt": TC.FILE_CONTENT})

    class MockResp:
        headers = {}

        def read(self):
            return zip_bytes

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(get, "urlopen", lambda url: MockResp())

    r = client.get("/get/file/", params={"file_uri": TC.ARCP_FILE_TXT})
    assert r.status_code == 200
    assert r.content == TC.FILE_CONTENT
    assert r.headers["Content-Disposition"] == "attachment; filename=file.txt"
    assert r.headers["content-type"] == f"{TC.CONTENT_TYPE_PLAIN}; charset=utf-8"


def test_get_file_ok_default_content_type(monkeypatch):
    monkeypatch.setattr(get, "CRATE_URL_QUERY", "Q:%s")
    monkeypatch.setattr(get, "run_query",
                        lambda q: [(f"{TC.MINIO_URL}/{TC.MINIO_BUCKET}/{TC.ANOTHER_ZIP}",)])
    monkeypatch.setattr(get, "content_type_map", {"txt": TC.CONTENT_TYPE_PLAIN})

    zip_bytes = make_zip_bytes({"x/y/file.dat": TC.BINARY_CONTENT})

    class MockResp:
        headers = {}

        def read(self):
            return zip_bytes

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(get, "urlopen", lambda url: MockResp())

    r = client.get("/get/file/", params={"file_uri": TC.ARCP_FILE_DAT})
    assert r.status_code == 200
    assert r.content == TC.BINARY_CONTENT
    assert r.headers["Content-Disposition"] == "attachment; filename=file.dat"
    assert r.headers["content-type"] == TC.CONTENT_TYPE_OCTET


def test_get_file_member_missing(monkeypatch):
    monkeypatch.setattr(get, "CRATE_URL_QUERY", "Q:%s")
    monkeypatch.setattr(get, "run_query",
                        lambda q: [(f"{TC.MINIO_URL}/{TC.MINIO_BUCKET}/miss.zip",)])

    zip_bytes = make_zip_bytes({"dir/other.txt": b"nope"})

    class MockResp:
        headers = {}

        def read(self):
            return zip_bytes

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(get, "urlopen", lambda url: MockResp())

    r = client.get("/get/file/", params={"file_uri": TC.ARCP_FILE_MISSING})
    assert r.status_code == 404
    assert r.json()["detail"] == "File 'dir/missing.txt' not found in the crate"


# Tests for get graphs-for-file
def test_graphs_for_file_ok(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q: [(TC.GRAPH_ID_1,), (TC.GRAPH_ID_2,)])
    r = client.get("/get/graphs-for-file/", params={"file_id": TC.FILE_ID_123})
    assert r.status_code == 200
    assert r.json() == {"result": [TC.GRAPH_ID_1, TC.GRAPH_ID_2]}


def test_graphs_for_file_empty(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q: [])
    r = client.get("/get/graphs-for-file/", params={"file_id": TC.FILE_ID_123})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get graphs-for-result
def test_graphs_for_result_ok(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q: [("grA",), ("grB",)])
    r = client.get("/get/graphs-for-result/", params={"result_id": TC.RESULT_ID_42})
    assert r.status_code == 200
    assert r.json() == {"result": ["grA", "grB"]}


def test_graphs_for_result_empty(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q: [])
    r = client.get("/get/graphs-for-result/", params={"result_id": TC.RESULT_ID_42})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get workflow
def test_workflow_ok_and_graph_id_forwarded(monkeypatch):
    seen = {}

    def mock_run_query(q, graph_id=None):
        seen["graph_id"] = graph_id
        return [(TC.WORKFLOW_1,), (TC.WORKFLOW_2,)]

    monkeypatch.setattr(get, "run_query", mock_run_query)
    r = client.get("/get/workflow/", params={"graph_id": TC.GRAPH_ID_1})
    assert r.status_code == 200
    assert r.json() == {"result": [TC.WORKFLOW_1, TC.WORKFLOW_2]}
    assert seen["graph_id"] == TC.GRAPH_ID_1


def test_workflow_empty(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q, graph_id=None: [])
    r = client.get("/get/workflow/", params={"graph_id": TC.GRAPH_ID_1})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get run-results
def test_run_results_ok(monkeypatch):
    seen = {}

    def mock_run_query(q, graph_id=None):
        seen["graph_id"] = graph_id
        return [("r1",), ("r2",)]

    monkeypatch.setattr(get, "run_query", mock_run_query)

    r = client.get("/get/run-results/", params={"graph_id": TC.GRAPH_ID_2})
    assert r.status_code == 200
    assert r.json() == {"result": ["r1", "r2"]}
    assert seen["graph_id"] == TC.GRAPH_ID_2


def test_run_results_empty(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q, graph_id=None: [])
    r = client.get("/get/run-results/", params={"graph_id": TC.GRAPH_ID_2})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get run-objects
def test_run_objects_ok(monkeypatch):
    seen = {}

    def mock_run_query(q, graph_id=None):
        seen["graph_id"] = graph_id
        return [("o1",), ("o2",)]

    monkeypatch.setattr(get, "run_query", mock_run_query)
    r = client.get("/get/run-objects/", params={"graph_id": TC.GRAPH_ID_3})
    assert r.status_code == 200
    assert r.json() == {"result": ["o1", "o2"]}
    assert seen["graph_id"] == TC.GRAPH_ID_3


def test_run_objects_empty(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q, graph_id=None: [])
    r = client.get("/get/run-objects/", params={"graph_id": TC.GRAPH_ID_3})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get objects-for-result
def test_objects_for_result_ok(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q: [("objA",), ("objB",)])
    r = client.get("/get/objects-for-result/", params={"result_id": TC.RESULT_ID_7})
    assert r.status_code == 200
    assert r.json() == {"result": ["objA", "objB"]}


def test_objects_for_result_empty(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q: [])
    r = client.get("/get/objects-for-result/", params={"result_id": TC.RESULT_ID_7})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get actions-for-result
def test_actions_for_result_ok(monkeypatch):
    monkeypatch.setattr(get, "fetch_actions_for_result", lambda rid: ["a1", "a2"])
    r = client.get("/get/actions-for-result/", params={"result_id": TC.RESULT_ID_8})
    assert r.status_code == 200
    assert r.json() == {"result": ["a1", "a2"]}


def test_actions_for_result_empty(monkeypatch):
    monkeypatch.setattr(get, "fetch_actions_for_result", lambda rid: [])
    r = client.get("/get/actions-for-result/", params={"result_id": TC.RESULT_ID_8})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get objects-for-action
def test_objects_for_action_ok(monkeypatch):
    monkeypatch.setattr(get, "fetch_objects_for_action", lambda aid: ["oX", "oY"])
    r = client.get("/get/objects-for-action/", params={"action_id": TC.ACTION_ID_1})
    assert r.status_code == 200
    assert r.json() == {"result": ["oX", "oY"]}


def test_objects_for_action_empty(monkeypatch):
    monkeypatch.setattr(get, "fetch_objects_for_action", lambda aid: [])
    r = client.get("/get/objects-for-action/", params={"action_id": TC.ACTION_ID_1})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get results-for-action
def test_results_for_action_ok(monkeypatch):
    monkeypatch.setattr(get, "fetch_results_for_action", lambda aid: ["rX", "rY"])
    r = client.get("/get/results-for-action/", params={"action_id": TC.ACTION_ID_2})
    assert r.status_code == 200
    assert r.json() == {"result": ["rX", "rY"]}


def test_results_for_action_empty(monkeypatch):
    monkeypatch.setattr(get, "fetch_results_for_action", lambda aid: [])
    r = client.get("/get/results-for-action/", params={"action_id": TC.ACTION_ID_2})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for get run-params
def test_run_params_ok(monkeypatch):
    seen = {}

    def mock_run_query(q, graph_id=None):
        seen["graph_id"] = graph_id
        return [SimpleNamespace(name="p1", value="v1"),
                SimpleNamespace(name="p2", value="v2")]

    monkeypatch.setattr(get, "run_query", mock_run_query)

    r = client.get("/get/run-params/", params={"graph_id": TC.GRAPH_ID_9})
    assert r.status_code == 200
    assert r.json() == {"result": [["p1", "v1"], ["p2", "v2"]]}
    assert seen["graph_id"] == TC.GRAPH_ID_9


def test_run_params_empty(monkeypatch):
    monkeypatch.setattr(get, "run_query", lambda q, graph_id=None: [])
    r = client.get("/get/run-params/", params={"graph_id": TC.GRAPH_ID_9})
    assert r.status_code == 200
    assert r.json() == {"result": []}


# Tests for pathops/copy and pathops/move
@pytest.mark.parametrize("op", ["copy", "move"])
def test_cpmv_future_datetime(op):
    future_date = "9999-10-10T08:05:00+00:00"
    r = client.post(
        f"/pathops/{op}/",
        params={
            "src": TC.FILE_URI_A,
            "dest": TC.FILE_URI_B,
            "when": future_date,
        }
    )
    assert r.status_code == 422
    assert r.json()["detail"] == f"datetime {future_date} is in the future"


@pytest.mark.parametrize("op", ["copy", "move"])
def test_cpmv_not_fileuri(op):
    r = client.post(
        f"/pathops/{op}/",
        params={
            "src": TC.ARCP_FILE_TXT,
            "dest": TC.FILE_URI_B,
        }
    )
    assert r.status_code == 422
    assert r.json()["detail"] == "Can only operate on a 'file:/' File or Dataset"


@pytest.mark.parametrize("op", ["copy", "move"])
def test_cpmv_missing_src(monkeypatch, op):
    monkeypatch.setattr(pathops, "run_query", lambda q: [])
    r = client.post(
        f"/pathops/{op}/",
        params={
            "src": TC.FILE_URI_A,
            "dest": TC.FILE_URI_B,
        }
    )
    assert r.status_code == 404
    assert r.json()["detail"] == f"File or Dataset '{TC.FILE_URI_A}' not found"


def test_mv_already_moved(monkeypatch):
    chain = ["file:///foo"]
    monkeypatch.setattr(pathops, "movechain", lambda p: {"result": chain})
    monkeypatch.setattr(pathops, "run_query", lambda q: [(URIRef(TC.FILE_URI_A),)])
    r = client.post(
        "/pathops/move/",
        params={
            "src": TC.FILE_URI_A,
            "dest": TC.FILE_URI_B,
        }
    )
    assert r.status_code == 422
    assert r.json()["detail"] == f"'{TC.FILE_URI_A}' has already been moved to: {chain}"


@pytest.mark.parametrize("op", ["copy", "move"])
def test_cpmv_ok(monkeypatch, op):

    def mock_run_query(q):
        if q == IS_FILE_OR_DIR_QUERY % TC.FILE_URI_A:
            return [(URIRef(TC.FILE_URI_A),)]
        return []

    monkeypatch.setattr(pathops, "run_query", mock_run_query)

    async def mock_load_crate_metadata(f):
        return {
            "result": "success",
            "crate_url": crate_url,
        }

    monkeypatch.setattr(pathops, "load_crate_metadata", mock_load_crate_metadata)

    crate_url = "http://minio:9000/crates/foo.zip"
    monkeypatch.setattr(pathops, "movechain", lambda p: {"result": []})
    r = client.post(
        "/pathops/move/",
        params={
            "src": TC.FILE_URI_A,
            "dest": TC.FILE_URI_B,
        }
    )
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "success"
    assert body["crate_url"] == crate_url


def test_movechain(monkeypatch):
    move_dest_query_results = [
        [(URIRef(TC.FILE_URI_C),)],
        [(URIRef(TC.FILE_URI_B),)],
    ]

    def mock_run_query(q):
        try:
            return move_dest_query_results.pop()
        except IndexError:
            return []

    monkeypatch.setattr(pathops, "run_query", mock_run_query)

    r = client.get(
        "/pathops/movechain/",
        params={"path_id": TC.FILE_URI_A}
    )
    assert r.status_code == 200
    assert r.json() == {"result": [TC.FILE_URI_B, TC.FILE_URI_C]}
