"""Command-line interface: validate, train, graph-load, serve."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

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

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
