from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_ask_endpoint_redacts_pii():
    payload = {
        "query": "Halo dokter, NIK saya 3275011234567890 dan nama saya Budi. Saya sakit perut.",
        "session_id": "test-123"
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    assert "redacted_query" in data
    
    # NIK and Name should be redacted in the returned redacted_query
    redacted = data["redacted_query"]
    assert "3275011234567890" not in redacted
    assert "Budi" not in redacted
    
    # Should contain some form of redaction marker
    assert "<ID_NUMBER>" in redacted or "<PERSON>" in redacted or "<REDACTED>" in redacted
