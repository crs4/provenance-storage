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

import io, zipfile
import pytest
from rdflib import URIRef

from fastapi.testclient import TestClient
from provstor_api.main import app
import provstor_api.routes.upload as upload
from provstor_api.routes.query import list_graphs, list_rde_graphs
import provstor_api.routes.query as query

client = TestClient(app)

def make_zip(with_metadata=True, metadata_name="ro-crate-metadata.json"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        if with_metadata:
            # metadata can be nested; the code checks basename only
            z.writestr(f"crate/{metadata_name}", b'{"@context": "https://w3id.org/ro/crate/1.1/context"}')
        else:
            z.writestr("README.txt", b"Readme file")
    buf.seek(0)
    return buf

@pytest.fixture
def mock_client(monkeypatch):
    class FakeMinio:
        def __init__(self, *a, **kw): pass
        def bucket_exists(self, b): return True
        def make_bucket(self, b): pass
        def set_bucket_policy(self, b, pol): pass
        def put_object(self, *a, **kw): pass

    class FakeStore:
        def open(self, endpoints): self.endpoints = endpoints

    class FakeGraph:
        def __init__(self, store, identifier=None):
            self.store = store
            self.identifier = identifier
        def parse(self, path, publicID=None): self.parsed = (path, publicID)
        def query(self, _):  # pretend RDE query succeeded and returned one row
            return [(URIRef("http://example.org/rde"),)]
        def add(self, triple): self.added = triple

    # --- Patch them in the route module namespace ---
    monkeypatch.setattr(upload, "Minio", FakeMinio)
    monkeypatch.setattr(upload, "SPARQLUpdateStore", FakeStore)
    monkeypatch.setattr(upload, "Graph", FakeGraph)
    monkeypatch.setattr(upload.arcp, "arcp_location", lambda url: "arcp://example/root")

    # Make settings deterministic but harmless
    upload.settings.minio_store = "minio:9000"
    upload.settings.minio_bucket = "crates"
    upload.settings.fuseki_base_url = "http://fuseki:3030"
    upload.settings.fuseki_dataset = "ds"

    return TestClient(app)

# Tests for upload crate
def test_check_status():
    response = client.get("/status/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_rejects_non_zip(mock_client):
    r = mock_client.post("/upload/crate/", files={"crate_path": ("x.txt", b"hi", "text/plain")})
    assert r.status_code == 415
    assert r.json()["detail"] == "crate_path must be a zip file."

def test_rejects_empty_file(mock_client):
    r = mock_client.post("/upload/crate/", files={"crate_path": ("empty.zip", b"", "application/zip")})
    assert r.status_code == 400
    assert r.json()["detail"] == "Empty file uploaded."

def test_rejects_missing_metadata(mock_client):
    buf = make_zip(with_metadata=False)
    r = mock_client.post("/upload/crate/", files={"crate_path": ("crate.zip", buf.getvalue(), "application/zip")})
    assert r.status_code == 404
    assert r.json()["detail"] == "ro-crate-metadata.json not found in the zip file"

def test_correct_path(mock_client):
    buf = make_zip(with_metadata=True)
    r = mock_client.post("/upload/crate/", files={"crate_path": ("crate.zip", buf.getvalue(), "application/zip")})
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "success"
    assert body["crate_url"] == "http://minio:9000/crates/crate.zip"

# Tests for list-graphs
def test_list_graphs_ok(monkeypatch):
    monkeypatch.setattr(list_graphs, "GRAPHS_QUERY", "SELECT ?g WHERE { GRAPH ?g { ?s ?p ?o } }")

    def fake_run_query(q):
        return [("http://example.org/g1",), ("http://example.org/g2",)]
    monkeypatch.setattr(list_graphs, "run_query", fake_run_query)

    r = client.get("/query/list-graphs/")
    assert r.status_code == 200
    assert r.json() == {"result": ["http://example.org/g1", "http://example.org/g2"]}

def test_list_graphs_empty(monkeypatch):
    monkeypatch.setattr(list_graphs, "GRAPHS_QUERY", "SELECT ?g WHERE { }")
    monkeypatch.setattr(list_graphs, "run_query", lambda q: [])

    r = client.get("/query/list-graphs/")
    assert r.status_code == 200
    assert r.json() == {"result": []}

# Tests for list-rde-graphs
def test_list_rde_graphs_ok(monkeypatch):
    monkeypatch.setattr(query, "RDE_GRAPH_QUERY",
    "SELECT DISTINCT ?g ?rde WHERE { GRAPH ?g { ?md a schema:CreativeWork ; schema:about ?rde . FILTER(contains(str(?md), 'ro-crate-metadata.json') && STRSTARTS(STR(?md), 'arcp://uuid,')) } } ORDER BY ?g")

    def fake_run_query(q):
        return [
            ("http://example.org/rde1", "rde1"),
            ("http://example.org/rde2", "rde2")
        ]
    monkeypatch.setattr(query, "run_query", fake_run_query)

    r = client.get("/query/list-RDE-graphs/")
    assert r.status_code == 200
    assert r.json() == {
        "result": [
            ['http://example.org/rde1', 'rde1'],
            ['http://example.org/rde2', 'rde2']
        ]
    }

def test_list_rde_graphs_empty(monkeypatch):
    monkeypatch.setattr(query, "RDE_GRAPH_QUERY", "SELECT ?rde WHERE { }")
    monkeypatch.setattr(query, "run_query", lambda q: [])

    r = client.get("/query/list-RDE-graphs/")
    assert r.status_code == 200
    assert r.json() == {"result": []}

