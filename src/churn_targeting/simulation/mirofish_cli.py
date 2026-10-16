
from __future__ import annotations

import argparse
import json
import os
import sys

from churn_targeting.simulation.mirofish_health import (
    MiroFishConnectionError,
    MiroFishHealthClient,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check MiroFish service health without starting a simulation."
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("MIROFISH_BASE_URL", "http://localhost:5001"),
        help="MiroFish backend base URL (or set MIROFISH_BASE_URL).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("MIROFISH_TIMEOUT_SECONDS", "5")),
        help="Request timeout in seconds.",
    )
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    try:
        client = MiroFishHealthClient(
            base_url=args.base_url,
            timeout_seconds=args.timeout,
        )
        result = client.check_health()
    except (MiroFishConnectionError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "unavailable", "error": str(exc)},
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
