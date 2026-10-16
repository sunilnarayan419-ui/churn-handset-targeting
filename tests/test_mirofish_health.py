
import httpx
import pytest

from churn_targeting.simulation.mirofish_health import (
    MiroFishConnectionError,
    MiroFishHealthClient,
)


def make_transport(status_code=200, payload=None):
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/health"

        return httpx.Response(
            status_code,
            json=payload
            if payload is not None
            else {
                "status": "ok",
                "service": "MiroFish Backend",
            },
        )

    return httpx.MockTransport(handler)


def test_health_check_accepts_valid_mirofish_response():
    client = MiroFishHealthClient(
        "http://localhost:5001",
        transport=make_transport(),
    )

    result = client.check_health()

    assert result == {
        "status": "ok",
        "service": "MiroFish Backend",
        "endpoint": "/health",
    }


def test_health_check_rejects_http_error():
    client = MiroFishHealthClient(
        "http://localhost:5001",
        transport=make_transport(status_code=503),
    )

    with pytest.raises(MiroFishConnectionError):
        client.check_health()


def test_health_check_rejects_unexpected_service():
    client = MiroFishHealthClient(
        "http://localhost:5001",
        transport=make_transport(
            payload={"status": "ok", "service": "Another Service"}
        ),
    )

    with pytest.raises(MiroFishConnectionError):
        client.check_health()


def test_health_check_rejects_non_object_json():
    def handler(request):
        return httpx.Response(200, json=["ok"])

    client = MiroFishHealthClient(
        "http://localhost:5001",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(MiroFishConnectionError):
        client.check_health()


def test_invalid_base_url_is_rejected():
    with pytest.raises(ValueError):
        MiroFishHealthClient("not-a-url")


def test_non_positive_timeout_is_rejected():
    with pytest.raises(ValueError):
        MiroFishHealthClient(
            "http://localhost:5001",
            timeout_seconds=0,
        )
