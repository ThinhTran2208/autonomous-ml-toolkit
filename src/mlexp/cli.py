"""Command-line entry points; tracking remains MLflow's responsibility."""

import argparse
import csv
import json
import sys
from pathlib import Path

import yaml
from mlflow.exceptions import MlflowException

from mlexp.config import load_config
from mlexp.experiment import run_experiment
from mlexp.tracking import DEFAULT_TRACKING_URI, compare_runs, render_report


def main(argv: list[str] | None = None) -> int:
    # Preserve the console encoding while making Unicode paths safe to display.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(
        prog="mlexp", description="Reproducible tabular ML experiments"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Run a fixed experiment from YAML")
    run.add_argument("config", type=Path)
    compare = commands.add_parser("compare", help="Rank compatible runs by training-only CV")
    compare.add_argument("--experiment", required=True)
    compare.add_argument("--tracking-uri", default=DEFAULT_TRACKING_URI)
    report = commands.add_parser("report", help="Render a tracked run as Markdown")
    report.add_argument("run_id")
    report.add_argument("--tracking-uri", default=DEFAULT_TRACKING_URI)
    report.add_argument("--output", type=Path, help="Write a new report file (never overwrite)")
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            print(json.dumps(run_experiment(load_config(args.config)), indent=2, allow_nan=False))
        elif args.command == "compare":
            print(json.dumps(compare_runs(args.experiment, args.tracking_uri), indent=2))
        else:
            content = render_report(args.run_id, args.tracking_uri)
            if args.output is None:
                print(content, end="")
            else:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x", encoding="utf-8") as handle:
                    handle.write(content)
                print(str(args.output))
    except (OSError, ValueError, csv.Error, yaml.YAMLError, MlflowException) as exc:
        print(f"mlexp: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
