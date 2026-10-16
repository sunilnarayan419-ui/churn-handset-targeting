
import httpx
import pytest

from churn_targeting.simulation.mirofish_client import (
    MiroFishAPIError,
    MiroFishClient,
)


def make_transport(status_code=200, payload=None):
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/api/simulation/create"

        body = request.read().decode("utf-8")
        import json

        request_data = json.loads(body)

        assert request_data["project_id"] == "proj_test"
        assert request_data["enable_twitter"] is False
        assert request_data["enable_reddit"] is False

        return httpx.Response(
            status_code,
            json=payload
            if payload is not None
            else {
                "success": True,
                "data": {
                    "simulation_id": "sim_test",
                    "project_id": "proj_test",
                    "status": "created",
                },
            },
        )

    return httpx.MockTransport(handler)


def test_create_simulation_success():
    client = MiroFishClient(
        "http://localhost:5001",
        transport=make_transport(),
    )

    result = client.create_simulation("proj_test")

    assert result == {
        "simulation_id": "sim_test",
        "project_id": "proj_test",
        "status": "created",
    }


def test_create_simulation_rejects_empty_project_id():
    client = MiroFishClient("http://localhost:5001")

    with pytest.raises(ValueError):
        client.create_simulation(" ")


def test_create_simulation_rejects_http_error():
    client = MiroFishClient(
        "http://localhost:5001",
        transport=make_transport(status_code=500),
    )

    with pytest.raises(MiroFishAPIError):
        client.create_simulation("proj_test")


def test_create_simulation_rejects_unsuccessful_response():
    client = MiroFishClient(
        "http://localhost:5001",
        transport=make_transport(
            payload={"success": False, "error": "Project not found"},
        ),
    )

    with pytest.raises(MiroFishAPIError):
        client.create_simulation("proj_test")


def test_create_simulation_rejects_missing_simulation_id():
    client = MiroFishClient(
        "http://localhost:5001",
        transport=make_transport(
            payload={
                "success": True,
                "data": {"status": "created"},
            },
        ),
    )

    with pytest.raises(MiroFishAPIError):
        client.create_simulation("proj_test")


def test_invalid_timeout_is_rejected():
    with pytest.raises(ValueError):
        MiroFishClient(
            "http://localhost:5001",
            timeout_seconds=0,
        )
