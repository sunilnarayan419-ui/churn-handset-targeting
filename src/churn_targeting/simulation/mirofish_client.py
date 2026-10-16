
from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlsplit

import httpx


class MiroFishAPIError(RuntimeError):
    """Raised when the MiroFish API request fails or returns invalid data."""


class MiroFishClient:
    """HTTP client for explicitly requested MiroFish API operations."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        parsed = urlsplit(base_url)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be a valid HTTP(S) URL")

        if parsed.username or parsed.password:
            raise ValueError("Do not include credentials in base_url")

        if parsed.query or parsed.fragment:
            raise ValueError("base_url must not contain a query or fragment")

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def create_simulation(
        self,
        project_id: str,
        graph_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a simulation for an existing MiroFish project.

        This modifies remote state. Call only when explicitly intended.
        """
        if not project_id.strip():
            raise ValueError("project_id must not be empty")

        payload: dict[str, Any] = {
            "project_id": project_id,
            "enable_twitter": False,
            "enable_reddit": False,
        }

        if graph_id is not None:
            if not graph_id.strip():
                raise ValueError("graph_id must not be empty")
            payload["graph_id"] = graph_id

        result = self._request_json(
            "POST",
            "/api/simulation/create",
            payload=payload,
        )

        simulation_id = result.get("simulation_id")
        status = result.get("status")

        if (
            not isinstance(simulation_id, str)
            or not simulation_id.strip()
            or not isinstance(status, str)
            or not status.strip()
        ):
            raise MiroFishAPIError(
                "MiroFish response is missing a valid simulation ID or status."
            )

        return {
            "simulation_id": simulation_id,
            "project_id": result.get("project_id", project_id),
            "status": status,
        }

    def prepare_simulation(
        self,
        simulation_id: str,
        *,
        use_llm_for_profiles: bool = True,
        parallel_profile_count: int = 1,
        force_regenerate: bool = False,
    ) -> dict[str, Any]:
        """Start preparation for an existing simulation.

        This may trigger LLM work. Call explicitly, not during status checks.
        """
        if not simulation_id.strip():
            raise ValueError("simulation_id must not be empty")

        if parallel_profile_count < 1:
            raise ValueError("parallel_profile_count must be positive")

        payload = {
            "simulation_id": simulation_id,
            "use_llm_for_profiles": use_llm_for_profiles,
            "parallel_profile_count": parallel_profile_count,
            "force_regenerate": force_regenerate,
        }

        return self._request_json(
            "POST",
            "/api/simulation/prepare",
            payload=payload,
        )

    def get_preparation_status(
        self,
        *,
        task_id: str | None = None,
        simulation_id: str | None = None,
    ) -> dict[str, Any]:
        """Check preparation progress without starting a new task."""
        if not task_id and not simulation_id:
            raise ValueError("Provide task_id or simulation_id")

        payload: dict[str, str] = {}

        if task_id:
            payload["task_id"] = task_id

        if simulation_id:
            payload["simulation_id"] = simulation_id

        return self._request_json(
            "POST",
            "/api/simulation/prepare/status",
            payload=payload,
        )

    def start_simulation(
        self,
        simulation_id: str,
        *,
        platform: str = "parallel",
        max_rounds: int | None = 3,
        enable_graph_memory_update: bool = False,
        force: bool = False,
    ) -> dict[str, Any]:
        """Start a prepared simulation; this modifies remote state."""
        if not simulation_id.strip():
            raise ValueError("simulation_id must not be empty")

        if platform not in {"twitter", "reddit", "parallel"}:
            raise ValueError(
                "platform must be twitter, reddit, or parallel"
            )

        if max_rounds is not None and max_rounds <= 0:
            raise ValueError("max_rounds must be positive")

        payload: dict[str, Any] = {
            "simulation_id": simulation_id,
            "platform": platform,
            "enable_graph_memory_update": enable_graph_memory_update,
            "force": force,
        }

        if max_rounds is not None:
            payload["max_rounds"] = max_rounds

        return self._request_json(
            "POST",
            "/api/simulation/start",
            payload=payload,
        )

    def get_run_status(self, simulation_id: str) -> dict[str, Any]:
        """Retrieve run status without starting or restarting a simulation."""
        if not simulation_id.strip():
            raise ValueError("simulation_id must not be empty")

        safe_id = quote(simulation_id, safe="")

        return self._request_json(
            "GET",
            f"/api/simulation/{safe_id}/run-status",
        )

    def get_timeline(
        self,
        simulation_id: str,
        *,
        start_round: int = 0,
        end_round: int | None = None,
    ) -> dict[str, Any]:
        """Retrieve round-level simulation history."""
        if not simulation_id.strip():
            raise ValueError("simulation_id must not be empty")

        if start_round < 0:
            raise ValueError("start_round must be non-negative")

        if end_round is not None and end_round < start_round:
            raise ValueError("end_round must be >= start_round")

        params: dict[str, int] = {"start_round": start_round}

        if end_round is not None:
            params["end_round"] = end_round

        safe_id = quote(simulation_id, safe="")

        return self._request_json(
            "GET",
            f"/api/simulation/{safe_id}/timeline",
            params=params,
        )

    def get_agent_stats(self, simulation_id: str) -> dict[str, Any]:
        """Retrieve agent activity statistics."""
        if not simulation_id.strip():
            raise ValueError("simulation_id must not be empty")

        safe_id = quote(simulation_id, safe="")

        return self._request_json(
            "GET",
            f"/api/simulation/{safe_id}/agent-stats",
        )

    def get_posts(
        self,
        simulation_id: str,
        *,
        platform: str = "reddit",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Retrieve stored posts with pagination."""
        if not simulation_id.strip():
            raise ValueError("simulation_id must not be empty")

        if platform not in {"twitter", "reddit"}:
            raise ValueError("platform must be twitter or reddit")

        if limit < 1:
            raise ValueError("limit must be positive")

        if offset < 0:
            raise ValueError("offset must be non-negative")

        safe_id = quote(simulation_id, safe="")

        return self._request_json(
            "GET",
            f"/api/simulation/{safe_id}/posts",
            params={
                "platform": platform,
                "limit": limit,
                "offset": offset,
            },
        )

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request and validate the MiroFish response."""
        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.request(
                    method,
                    f"{self.base_url}{path}",
                    json=payload if method != "GET" else None,
                    params=params,
                )

                response.raise_for_status()
                result = response.json()

        except (httpx.HTTPError, ValueError) as exc:
            raise MiroFishAPIError(
                f"MiroFish {method} {path} request failed. "
                "Check the service, API version, and response."
            ) from exc

        if not isinstance(result, dict) or result.get("success") is not True:
            raise MiroFishAPIError(
                f"MiroFish {method} {path} did not confirm success."
            )

        data = result.get("data")

        if not isinstance(data, dict):
            raise MiroFishAPIError(
                f"MiroFish {method} {path} response is missing its data object."
            )

        return data
