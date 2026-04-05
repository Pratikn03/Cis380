from app.main import app


def test_api_v1_contract_in_openapi():
    schema = app.openapi()
    paths = schema.get("paths", {})
    assert "/api/v1/jobs" in paths
    assert "/api/v1/jobs/start" in paths
    assert "/api/v1/rag/query" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/training/overview" in paths
    assert "/api/v1/training/domain/{domain}" in paths
