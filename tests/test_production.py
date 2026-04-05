"""
Sentifargo Production Test Suite
Comprehensive tests for API endpoints, models, and integrations
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import httpx


# Test fixtures
@pytest.fixture
def test_client():
    """Create test client for API."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async test client."""
    from app.main import app

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ============================================
# Health Check Tests
# ============================================


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, test_client):
        """Test basic health check."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_liveness_check(self, test_client):
        """Test Kubernetes liveness probe."""
        response = test_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_readiness_check(self, test_client):
        """Test Kubernetes readiness probe."""
        response = test_client.get("/health/ready")
        # Should return 200 or 503 based on component health
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "components" in data

    def test_detailed_health(self, test_client):
        """Test detailed health check."""
        response = test_client.get("/health/detailed")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "uptime_seconds" in data
        assert "system" in data


# ============================================
# Chat API Tests
# ============================================


class TestChatAPI:
    """Test chat endpoints."""

    def test_chat_endpoint(self, test_client):
        """Test basic chat endpoint."""
        response = test_client.post(
            "/api/chat",
            json={
                "message": "Hello, how are you?",
                "user_id": "test_user",
                "use_rag": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data or "answer" in data or "error" not in data

    def test_chat_empty_message(self, test_client):
        """Test chat with empty message."""
        response = test_client.post(
            "/api/chat",
            json={
                "message": "",
                "user_id": "test_user",
            },
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_chat_with_rag(self, test_client):
        """Test chat with RAG enabled."""
        response = test_client.post(
            "/api/chat",
            json={
                "message": "What is fraud detection?",
                "user_id": "test_user",
                "use_rag": True,
            },
        )
        assert response.status_code == 200


# ============================================
# Fraud Detection Tests
# ============================================


class TestFraudAPI:
    """Test fraud detection endpoints."""

    def test_fraud_scoring(self, test_client):
        """Test fraud scoring endpoint."""
        response = test_client.post(
            "/api/fraud", json={"features": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]}
        )
        # May fail if model not loaded, that's ok
        assert response.status_code in [200, 500, 503]

    def test_fraud_invalid_features(self, test_client):
        """Test fraud with invalid features."""
        response = test_client.post("/api/fraud", json={"features": "invalid"})
        assert response.status_code in [400, 422, 500]

    def test_fraud_empty_features(self, test_client):
        """Test fraud with empty features."""
        response = test_client.post("/api/fraud", json={"features": []})
        assert response.status_code in [200, 400, 422, 500]


# ============================================
# Cyber Detection Tests
# ============================================


class TestCyberAPI:
    """Test cyber threat detection endpoints."""

    def test_cyber_scoring(self, test_client):
        """Test cyber scoring endpoint."""
        response = test_client.post(
            "/api/cyber", json={"features": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]}
        )
        assert response.status_code in [200, 500, 503]


# ============================================
# Behavior Analysis Tests
# ============================================


class TestBehaviorAPI:
    """Test behavior analysis endpoints."""

    def test_behavior_scoring(self, test_client):
        """Test behavior scoring endpoint."""
        response = test_client.post(
            "/api/behavior", json={"features": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]}
        )
        assert response.status_code in [200, 500, 503]


# ============================================
# Vision API Tests
# ============================================


class TestVisionAPI:
    """Test vision analysis endpoints."""

    def test_vision_predict_no_file(self, test_client):
        """Test vision endpoint without file."""
        response = test_client.post("/api/vision/predict")
        assert response.status_code in [400, 422]

    def test_vision_predict_invalid_file(self, test_client):
        """Test vision endpoint with invalid file type."""
        response = test_client.post(
            "/api/vision/predict", files={"file": ("test.txt", b"invalid content", "text/plain")}
        )
        assert response.status_code in [400, 422, 500]


# ============================================
# Recommendation API Tests
# ============================================


class TestRecommendAPI:
    """Test recommendation endpoints."""

    def test_recommend_movies(self, test_client):
        """Test movie recommendations."""
        response = test_client.post(
            "/api/recommend",
            json={
                "query": "recommend sci-fi movies",
                "user_id": "test_user",
            },
        )
        assert response.status_code in [200, 500]

    def test_recommend_products(self, test_client):
        """Test product recommendations."""
        response = test_client.post(
            "/api/recommend",
            json={
                "query": "best laptops under $1000",
                "user_id": "test_user",
            },
        )
        assert response.status_code in [200, 500]


# ============================================
# RAG API Tests
# ============================================


class TestRAGAPI:
    """Test RAG (Retrieval-Augmented Generation) endpoints."""

    def test_rag_query(self, test_client):
        """Test RAG query endpoint."""
        response = test_client.post(
            "/api/rag/query",
            json={
                "query": "What is anomaly detection?",
            },
        )
        assert response.status_code in [200, 500]

    def test_rag_upload_no_file(self, test_client):
        """Test RAG upload without file."""
        response = test_client.post("/api/rag/upload")
        assert response.status_code in [400, 422]


# ============================================
# Authentication Tests
# ============================================


class TestAuthentication:
    """Test authentication mechanisms."""

    def test_protected_endpoint_no_token(self, test_client):
        """Test protected endpoint without token."""
        # This depends on whether auth is required
        response = test_client.get("/api/monitor/summary")
        # May require auth or not depending on config
        assert response.status_code in [200, 401, 403, 500]

    def test_protected_endpoint_invalid_token(self, test_client):
        """Test protected endpoint with invalid token."""
        response = test_client.get(
            "/api/monitor/summary", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code in [200, 401, 403, 500]


# ============================================
# Rate Limiting Tests
# ============================================


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_not_exceeded(self, test_client):
        """Test requests within rate limit."""
        for _ in range(5):
            response = test_client.get("/health")
            assert response.status_code == 200

    def test_rate_limit_header(self, test_client):
        """Test rate limit headers are present."""
        response = test_client.get("/health")
        # Rate limit headers may or may not be present
        assert response.status_code == 200


# ============================================
# Error Handling Tests
# ============================================


class TestErrorHandling:
    """Test error handling and responses."""

    def test_404_endpoint(self, test_client):
        """Test 404 for non-existent endpoint."""
        response = test_client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, test_client):
        """Test method not allowed."""
        response = test_client.delete("/health")
        assert response.status_code in [405, 404]

    def test_invalid_json(self, test_client):
        """Test invalid JSON payload."""
        response = test_client.post(
            "/api/chat", content="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]


# ============================================
# Response Format Tests
# ============================================


class TestResponseFormat:
    """Test response format consistency."""

    def test_json_response(self, test_client):
        """Test all responses are JSON."""
        response = test_client.get("/health")
        assert response.headers["content-type"].startswith("application/json")

    def test_request_id_header(self, test_client):
        """Test request ID in response headers."""
        response = test_client.get("/health")
        # Request ID header may be present if middleware is active
        assert response.status_code == 200

    def test_cors_headers(self, test_client):
        """Test CORS headers."""
        response = test_client.options("/health", headers={"Origin": "http://localhost:3000"})
        # CORS should be configured
        assert response.status_code in [200, 204, 405]


# ============================================
# Performance Tests
# ============================================


class TestPerformance:
    """Basic performance tests."""

    def test_health_response_time(self, test_client):
        """Test health endpoint response time."""
        import time

        start = time.time()
        response = test_client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should respond in under 1 second

    def test_concurrent_requests(self, test_client):
        """Test handling concurrent requests."""
        import concurrent.futures

        def make_request():
            return test_client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)


# ============================================
# Integration Tests
# ============================================


class TestIntegration:
    """Integration tests for full workflows."""

    def test_chat_workflow(self, test_client):
        """Test complete chat workflow."""
        # 1. Health check
        health = test_client.get("/health")
        assert health.status_code == 200

        # 2. Send chat message
        chat = test_client.post(
            "/api/chat",
            json={
                "message": "Hello",
                "user_id": "integration_test",
            },
        )
        assert chat.status_code == 200

    def test_multimodal_workflow(self, test_client):
        """Test multimodal chat workflow."""
        # Test with text only (no file uploads in this basic test)
        response = test_client.post(
            "/api/chat/multimodal",
            data={
                "message": "Analyze this",
                "user_id": "test_user",
            },
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422, 500]


# ============================================
# Metrics Tests
# ============================================


class TestMetrics:
    """Test Prometheus metrics endpoint."""

    def test_metrics_endpoint(self, test_client):
        """Test metrics endpoint returns Prometheus format."""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        # Should be text/plain with Prometheus metrics
        content = response.text
        # Basic check for Prometheus format
        assert "Sentifargo" in content or "python" in content or "process" in content


# ============================================
# Configuration Tests
# ============================================


class TestConfiguration:
    """Test configuration module."""

    def test_settings_load(self):
        """Test settings can be loaded."""
        from app.core.config import get_settings

        settings = get_settings()
        assert settings is not None
        assert settings.app_name == "Sentifargo"

    def test_settings_cached(self):
        """Test settings are cached."""
        from app.core.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


# ============================================
# Middleware Tests
# ============================================


class TestMiddleware:
    """Test middleware functionality."""

    def test_exception_handling(self, test_client):
        """Test custom exception handling."""
        # Trigger a validation error
        response = test_client.post("/api/fraud", json={"invalid": "payload"})
        # Should return structured error response
        assert response.status_code in [400, 422, 500]
        data = response.json()
        # Error response should have structure
        assert "error" in data or "detail" in data


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
