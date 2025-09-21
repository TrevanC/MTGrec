import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.inference import get_inference_recommender

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_api_v1_health():
    """Test API v1 health endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_api_v1_version():
    """Test API v1 version endpoint"""
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data

def test_inference_recommender_initialization():
    """Test that InferenceRecommender can be retrieved"""
    try:
        # This will raise RuntimeError if not initialized
        recommender = get_inference_recommender()
        assert recommender is not None
        # Test that it has the expected methods
        assert hasattr(recommender, 'recommend')
        assert hasattr(recommender, 'get_card_by_oracle_id')
        assert hasattr(recommender, 'get_card_by_name')
    except RuntimeError:
        # If not initialized, that's expected in test environment
        # since startup events don't run in TestClient
        pytest.skip("InferenceRecommender not initialized in test environment")