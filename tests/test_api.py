"""
API Tests for Munch AI Dating Assistant
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthEndpoints:
    """Test health and basic endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client"""
        # Mock config before importing app
        os.makedirs("config", exist_ok=True)
        os.makedirs("web_interface", exist_ok=True)

        if not os.path.exists("config/config.yaml"):
            with open("config/config.yaml", "w") as f:
                f.write("""
app:
  host: "0.0.0.0"
  port: 8000
ollama:
  cloud_model: "test-model"
  api_key: "test-key"
curated_channels: []
""")

        if not os.path.exists("web_interface/index.html"):
            with open("web_interface/index.html", "w") as f:
                f.write("<html><body>Test</body></html>")

    def test_health_endpoint(self):
        """Test /health endpoint returns 200"""
        from app import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "model" in data

    def test_api_root(self):
        """Test /api endpoint returns API info"""
        from app import app
        client = TestClient(app)
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client"""
        os.makedirs("config", exist_ok=True)
        os.makedirs("web_interface", exist_ok=True)

        if not os.path.exists("config/config.yaml"):
            with open("config/config.yaml", "w") as f:
                f.write("""
app:
  host: "0.0.0.0"
  port: 8000
ollama:
  cloud_model: "test-model"
  api_key: "test-key"
curated_channels: []
""")

    def test_register_user(self):
        """Test user registration"""
        from app import app
        client = TestClient(app)
        response = client.post(
            "/api/auth/register",
            json={
                "email": f"test_{os.urandom(4).hex()}@example.com",
                "password": "testpass123",
                "username": "testuser"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token" in data

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        from app import app
        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401


class TestCacheService:
    """Test cache service functionality"""

    def test_cache_service_initialization(self):
        """Test cache service can be initialized"""
        from services.cache_service import CacheService
        cache = CacheService()
        # Should not raise, even if Redis unavailable
        assert cache is not None

    def test_cache_graceful_fallback(self):
        """Test cache operations work when Redis unavailable"""
        from services.cache_service import CacheService
        cache = CacheService("redis://invalid:9999")

        # Operations should return None/False gracefully
        assert cache.get("test_key") is None
        assert cache.set("test_key", {"data": "test"}) is False


class TestDatabaseService:
    """Test database service functionality"""

    def test_database_service_initialization(self):
        """Test database service can be initialized"""
        from services.database_service import DatabaseService
        db_service = DatabaseService()
        assert db_service is not None
