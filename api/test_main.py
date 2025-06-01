import pytest
from fastapi.testclient import TestClient
from main import app, reports_storage

client = TestClient(app)

# Clear reports storage before each test
@pytest.fixture(autouse=True)
def clear_reports():
    reports_storage.clear()

def test_invalid_token():
    # Test with no token
    response = client.get("/api/reports")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Test with invalid token format
    response = client.get("/api/reports", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]

    # Test with malformed token
    response = client.get("/api/reports", headers={"Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.invalid"})
    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]

def test_missing_authorization_header():
    response = client.get("/api/reports", headers={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_invalid_authorization_scheme():
    response = client.get("/api/reports", headers={"Authorization": "Basic invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication scheme"

def test_report_generation():
    # Test report creation without authentication
    report_data = {
        "patient_name": "John Doe",
        "diagnosis": "Dental Caries",
        "treatment": "Dental Filling",
        "notes": "Patient requires follow-up"
    }
    response = client.post("/api/reports", json=report_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_get_nonexistent_report():
    # Test getting a report that doesn't exist
    response = client.get("/api/reports/nonexistent-id")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_list_reports_empty():
    # Test listing reports when none exist
    response = client.get("/api/reports")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated" 