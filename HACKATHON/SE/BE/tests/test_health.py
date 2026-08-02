from fastapi.testclient import TestClient

from app.main import EXPECTED_TRIP_IDS
from app.modules.fleet.fleet_service import fleet_service


def test_health_is_public_and_matches_contract(app_factory):
    app = app_factory(STREAM_FPS=25)
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "dms-backend",
        "version": "1.0.0",
        "stream_fps": 25.0,
    }
    assert "X-Request-ID" in response.headers


def test_ready_returns_503_for_empty_cache(app_factory):
    app = app_factory()
    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["dataset_ready"] is True
    assert response.json()["cached_trips"] == 0


def test_ready_returns_200_for_all_expected_trips(app_factory):
    app = app_factory()
    with TestClient(app) as client:
        app.state.trip_cache.update({trip_id: object() for trip_id in EXPECTED_TRIP_IDS})
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["cached_trips"] == 10


def test_external_api_mode_requires_outbound_credentials(app_factory):
    app = app_factory(AI_SOURCE_MODE="external_api", AI_API_BASE_URL="", AI_API_KEY="")
    with TestClient(app) as client:
        app.state.trip_cache.update({trip_id: object() for trip_id in EXPECTED_TRIP_IDS})
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["external_ai_ready"] is False


def test_openapi_has_no_authentication_scheme(app_factory):
    app = app_factory()
    schema = app.openapi()

    assert schema.get("components", {}).get("securitySchemes") is None
    assert "/api/v1/fleet/summary" in schema["paths"]
    assert "/api/fleet/summary" in schema["paths"]
    assert schema["paths"]["/api/fleet/summary"]["get"]["deprecated"] is True


def test_request_id_is_preserved_on_errors(app_factory):
    app = app_factory()
    with TestClient(app) as client:
        response = client.get("/does-not-exist", headers={"X-Request-ID": "test-request-1"})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "test-request-1"
    assert response.json() == {
        "code": "HTTP_404",
        "message": "Not Found",
        "request_id": "test-request-1",
    }


def test_invalid_query_uses_common_422_error_contract(app_factory):
    app = app_factory()
    with TestClient(app) as client:
        response = client.get("/api/v1/fleet/summary?limit=0")

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_missing_trip_uses_common_404_error_contract(app_factory, monkeypatch, tmp_path):
    monkeypatch.setattr(fleet_service.adapter, "data_dir", tmp_path)
    app = app_factory()
    with TestClient(app) as client:
        response = client.get("/api/v1/trip/T99d/trajectory")

    assert response.status_code == 404
    assert response.json()["code"] == "TRIP_NOT_FOUND"
    assert response.json()["details"] == {"trip_id": "T99d"}
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_cors_preflight_allows_local_frontend(app_factory):
    app = app_factory()
    with TestClient(app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_preflight_allows_product_dashboard(app_factory):
    app = app_factory()
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/alerts/snapshot",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
