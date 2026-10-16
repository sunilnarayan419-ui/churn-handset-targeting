"""Command-line interface: validate, train, graph-load, serve."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from urllib.request import Request, urlopen

from .simulation.config import SimulationSettings
from .simulation.experiment import load_scenario
from .simulation.mirofish_adapter import MiroFishAdapter
from .simulation.mirofish_client import MiroFishClient
from .simulation.runner import SimulationRunner

from .config import SEED, Settings
from .data import load_customers, quality_report


def _cmd_validate(args) -> int:
    df = load_customers(args.data_dir)
    print(json.dumps(asdict(quality_report(df)), indent=2))
    return 0


def _cmd_train(args) -> int:
    from .modeling import save_bundle, train

    df = load_customers(args.data_dir)
    result = train(df, seed=args.seed, search=args.search)
    save_bundle(result.bundle, args.out)
    print(json.dumps({"saved": str(args.out), "metrics_test": result.metrics}, indent=2))
    return 0


def _cmd_graph_load(args) -> int:
    from .graph import GraphStore

    s = Settings.from_env()
    if not (s.neo4j_uri and s.neo4j_password):
        raise SystemExit("Set NEO4J_URI and NEO4J_PASSWORD (see .env.example)")
    df = load_customers(args.data_dir)
    with GraphStore(s.neo4j_uri, s.neo4j_user, s.neo4j_password, s.neo4j_database) as g:
        g.ensure_schema()
        if args.reset:
            g.clear()
        print(json.dumps(g.load(df), indent=2))
    return 0


def _cmd_serve(args) -> int:  # pragma: no cover - thin wrapper
    import uvicorn

    uvicorn.run("churn_targeting.api.main:create_app", factory=True, host=args.host, port=args.port)
    return 0



def _cmd_mirofish_run(args) -> int:
    """Run a scenario against an explicitly approved existing MiroFish project."""
    settings = SimulationSettings.from_env()
    base_url = (args.base_url or settings.base_url).rstrip("/")

    if not base_url:
        raise SystemExit(
            "Set MIROFISH_BASE_URL or pass --base-url. "
            "No simulation was submitted."
        )

    # Always screen the selected existing project before any remote mutation.
    preflight_args = argparse.Namespace(
        base_url=base_url,
        scenario=args.scenario,
        project_id=args.project_id,
    )
    preflight_result = _cmd_mirofish_preflight(preflight_args)
    if preflight_result != 0:
        raise SystemExit(
            "MiroFish preflight blocked this project. "
            "No simulation was submitted."
        )

    scenario = load_scenario(Path(args.scenario))
    client = MiroFishClient(
        base_url=base_url,
        timeout_seconds=settings.timeout_seconds,
    )
    adapter = MiroFishAdapter(
        client,
        project_id=args.project_id,
        allow_remote_execution=args.allow_remote_execution,
        confirm_project_requirement_matches_scenario=(
            args.confirm_project_requirement_matches_scenario
        ),
        max_rounds=args.max_rounds,
        max_wait_seconds=args.max_wait_seconds,
    )
    runner = SimulationRunner(
        adapter,
        timeout_seconds=args.runner_timeout_seconds,
    )
    outcome = runner.run(scenario)

    print(json.dumps({
        "execution_mode": "mirofish",
        "project_id": args.project_id,
        "scenario_id": scenario.scenario_id,
        "elapsed_seconds": outcome.elapsed_seconds,
        "result": outcome.result.model_dump(),
    }, indent=2, ensure_ascii=False, allow_nan=False))

    return 0 if outcome.result.status == "succeeded" else 1



def _cmd_mirofish_preflight(args) -> int:
    """Inspect an existing project's requirement without mutating MiroFish."""
    settings = SimulationSettings.from_env()
    base_url = (args.base_url or settings.base_url).rstrip("/")

    if not base_url:
        raise SystemExit(
            "Set MIROFISH_BASE_URL or pass --base-url. No API request was made."
        )

    scenario = load_scenario(Path(args.scenario))
    url = f"{base_url}/api/graph/project/list"
    request = Request(url, headers={"Accept": "application/json"}, method="GET")

    try:
        with urlopen(request, timeout=settings.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(json.dumps({
            "status": "preflight_error",
            "error_type": type(exc).__name__,
            "read_only": True,
            "execution_authorized": False,
        }, indent=2))
        return 2

    if not isinstance(payload, dict) or payload.get("success") is not True:
        print(json.dumps({
            "status": "preflight_error",
            "message": "MiroFish project-list response was not successful.",
            "read_only": True,
            "execution_authorized": False,
        }, indent=2))
        return 2

    projects = payload.get("data")
    if not isinstance(projects, list):
        raise SystemExit("Unexpected project-list schema; no mutation was made.")

    project = next(
        (
            item for item in projects
            if isinstance(item, dict)
            and item.get("project_id") == args.project_id
        ),
        None,
    )

    if project is None:
        print(json.dumps({
            "status": "project_not_found",
            "project_id": args.project_id,
            "read_only": True,
            "execution_authorized": False,
        }, indent=2))
        return 1

    requirement = str(project.get("simulation_requirement") or "")
    normalized = requirement.casefold()

    incompatible_markers = (
        "agricultural", "agriculture", "farmer", "compost", "nandipur"
    )
    domain_markers = (
        "telecom", "churn", "retention", "handset", "subscriber"
    )

    incompatible = any(marker in normalized for marker in incompatible_markers)
    domain_evidence = [
        marker for marker in domain_markers if marker in normalized
    ]

    if incompatible or not domain_evidence:
        status = "blocked_incompatible_or_unverified"
    else:
        status = "candidate_requires_manual_review"

    print(json.dumps({
        "status": status,
        "read_only": True,
        "execution_authorized": False,
        "project_id": project.get("project_id"),
        "project_name": project.get("name"),
        "project_status": project.get("status"),
        "simulation_requirement": requirement,
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.name,
        "scenario_objective": scenario.objective,
        "domain_keyword_evidence": domain_evidence,
        "warning": (
            "Keyword matching is only a screening heuristic. "
            "A human must verify semantic compatibility before execution."
        ),
        "next_action": (
            "Do not execute against this project."
            if status == "blocked_incompatible_or_unverified"
            else "Review the full requirement and graph schema manually."
        ),
    }, indent=2, ensure_ascii=False))

    return 0 if status == "candidate_requires_manual_review" else 1


def main(argv: list[str] | None = None) -> int:
    s = Settings.from_env()
    p = argparse.ArgumentParser(prog="churn-targeting", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="check keys, join and data quality")
    v.add_argument("--data-dir", default=str(s.data_dir))
    v.set_defaults(func=_cmd_validate)

    t = sub.add_parser("train", help="train, calibrate, evaluate and save the model bundle")
    t.add_argument("--data-dir", default=str(s.data_dir))
    t.add_argument("--out", default=str(s.model_path))
    t.add_argument("--seed", type=int, default=SEED)
    t.add_argument("--search", action="store_true", help="re-run the randomised hyper-parameter search")
    t.set_defaults(func=_cmd_train)

    g = sub.add_parser("graph-load", help="load customers into Neo4j")
    g.add_argument("--data-dir", default=str(s.data_dir))
    g.add_argument("--reset", action="store_true", help="delete existing graph data first")
    g.set_defaults(func=_cmd_graph_load)

    sv = sub.add_parser("serve", help="run the FastAPI service")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8000)
    sv.set_defaults(func=_cmd_serve)

    m = sub.add_parser(
        "mirofish-run",
        help="Run a scenario against an explicitly approved existing MiroFish project",
    )
    m.add_argument("--scenario", required=True, help="Path to a validated scenario YAML file")
    m.add_argument("--project-id", required=True, help="Existing MiroFish project ID")
    m.add_argument("--base-url", default=None, help="Overrides MIROFISH_BASE_URL")
    m.add_argument(
        "--allow-remote-execution",
        action="store_true",
        required=True,
        help="Explicitly permit remote simulation operations",
    )
    m.add_argument(
        "--confirm-project-requirement-matches-scenario",
        action="store_true",
        required=True,
        help="Confirm that the existing project's requirement matches the scenario",
    )
    m.add_argument("--max-rounds", type=int, default=3)
    m.add_argument("--max-wait-seconds", type=float, default=300.0)
    m.add_argument("--runner-timeout-seconds", type=float, default=360.0)
    m.set_defaults(func=_cmd_mirofish_run)

    pf = sub.add_parser(
        "mirofish-preflight",
        help="Read-only compatibility screening for an existing MiroFish project",
    )
    pf.add_argument("--scenario", required=True, help="Path to a scenario YAML file")
    pf.add_argument("--project-id", required=True, help="Existing MiroFish project ID")
    pf.add_argument("--base-url", default=None, help="Overrides MIROFISH_BASE_URL")
    pf.set_defaults(func=_cmd_mirofish_preflight)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
