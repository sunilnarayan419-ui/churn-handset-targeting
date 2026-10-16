
"""Command-line entry point for retention scenario comparisons."""

import argparse
from pathlib import Path

from churn_targeting.simulation.experiment import run_scenario_comparison


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an assumption-based retention comparison report."
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        type=Path,
        required=True,
        help="YAML scenario files to compare.",
    )
    parser.add_argument(
        "--value-per-save",
        type=float,
        required=True,
        help="Assumed economic value per incremental retained customer.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/simulation"),
        help="Directory for generated JSON reports.",
    )

    args = parser.parse_args()

    result = run_scenario_comparison(
        args.scenarios,
        value_per_incremental_save=args.value_per_save,
        output_dir=args.output_dir,
    )

    print("Scenario comparison completed.")
    print(f"Scenarios: {result['scenario_count']}")
    print(f"Comparison: {result['comparison_path']}")
    print(f"Manifest: {result['manifest_path']}")
    print(f"SHA-256: {result['comparison_sha256']}")


if __name__ == "__main__":
    main()
