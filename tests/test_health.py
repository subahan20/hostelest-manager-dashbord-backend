def test_health_check_endpoint(client):
    """Test that the GET /api/health endpoint returns 200 and correct JSON structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["message"] == "Hostelest API is running"


def test_404_not_found(client):
    """Test that requesting a nonexistent endpoint returns standardized 404 error."""
    response = client.get("/api/nonexistent-route-xyz")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert data["message"] == "Resource not found"
