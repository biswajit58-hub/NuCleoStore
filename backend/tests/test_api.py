import hashlib

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture
def client(isolated_storage):
    """A TestClient with isolated storage + a fresh DB."""
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_encode_and_decode_roundtrip(client):
    payload = b"NucleoStore API round-trip test."
    sha = hashlib.sha256(payload).hexdigest()

    r = client.post("/encode", files={"file": ("sample.txt", payload, "text/plain")})
    assert r.status_code == 200
    body = r.json()
    assert body["sha256"] == sha
    assert body["source_bytes"] == len(payload)
    assert len(body["dna_preview"]) > 0
    assert set(body["dna_preview"]).issubset({"A", "T", "G", "C"})

    job_id = body["job_id"]
    r2 = client.post(f"/decode/{job_id}")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["verified"] is True
    assert body2["sha256"] == sha
    assert body2["coding"] == 0


def test_encode_ecc_shows_coding(client):
    payload = b"ecc round-trip"
    r = client.post("/encode?ecc=rep3", files={"file": ("ecc.txt", payload, "text/plain")})
    assert r.status_code == 200
    assert r.json()["ecc"] == "rep3"

    job_id = r.json()["job_id"]
    r2 = client.post(f"/decode/{job_id}")
    assert r2.status_code == 200
    assert r2.json()["coding"] == 1


def test_encode_empty_file(client):
    r = client.post("/encode", files={"file": ("empty.bin", b"", "application/octet-stream")})
    assert r.status_code == 200
    body = r.json()
    assert body["source_bytes"] == 0
    assert body["dna_length"] > 0


def test_decode_unknown_job_returns_404(client):
    r = client.post("/decode/nonexistent-id")
    assert r.status_code == 404


def test_jobs_lists_after_encode(client):
    client.post("/encode", files={"file": ("a.txt", b"alpha", "text/plain")})
    client.post("/encode", files={"file": ("b.txt", b"beta", "text/plain")})
    r = client.get("/jobs")
    assert r.status_code == 200
    jobs = r.json()["jobs"]
    assert len(jobs) == 2
    assert {j["original_name"] for j in jobs} == {"a.txt", "b.txt"}


def test_download_dna_returns_atgc(client):
    payload = b"download dna test"
    r = client.post("/encode", files={"file": ("x.txt", payload, "text/plain")})
    job_id = r.json()["job_id"]
    r2 = client.get(f"/dna/{job_id}")
    assert r2.status_code == 200
    body = r2.text
    assert len(body) > 0
    assert set(body).issubset({"A", "T", "G", "C"})


def test_download_original_matches_upload(client):
    payload = b"byte-for-byte check"
    r = client.post("/encode", files={"file": ("orig.bin", payload, "application/octet-stream")})
    job_id = r.json()["job_id"]
    r2 = client.get(f"/original/{job_id}")
    assert r2.status_code == 200
    assert r2.content == payload


def test_download_reconstructed_requires_decode_first(client):
    r = client.post("/encode", files={"file": ("z.txt", b"recon", "text/plain")})
    job_id = r.json()["job_id"]
    r2 = client.get(f"/reconstructed/{job_id}")
    assert r2.status_code == 409
    client.post(f"/decode/{job_id}")
    r3 = client.get(f"/reconstructed/{job_id}")
    assert r3.status_code == 200
    assert r3.content == b"recon"


def test_download_endpoints_404_for_unknown_job(client):
    for path in ("/dna/nope", "/original/nope", "/reconstructed/nope"):
        r = client.get(path)
        assert r.status_code == 404


def test_decode_file_returns_original(client):
    payload = b"round-trip via uploaded .dna"
    r = client.post("/encode", files={"file": ("note.txt", payload, "text/plain")})
    job_id = r.json()["job_id"]
    dna_resp = client.get(f"/dna/{job_id}")
    assert dna_resp.status_code == 200
    dna_bytes = dna_resp.content
    r2 = client.post("/decode-file", files={"file": ("note.txt.dna", dna_bytes, "text/plain")})
    assert r2.status_code == 200
    assert r2.content == payload


def test_decode_file_rejects_non_container(client):
    r = client.post("/decode-file", files={"file": ("fake.dna", b"ATGCATGCATGC", "text/plain")})
    assert r.status_code == 400