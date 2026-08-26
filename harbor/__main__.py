"""Command-line interface for :mod:`harbor`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import build_task, run_task


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or run Harbor-format SRBench tasks.")
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="create a task from an existing train/test split")
    build.add_argument("--template", required=True, type=Path)
    build.add_argument("--train", required=True, type=Path)
    build.add_argument("--test", required=True, type=Path)
    build.add_argument("--spec", required=True, type=Path)
    build.add_argument("--output-dir", required=True, type=Path)
    build.add_argument("--name", default=None)

    run = commands.add_parser("run", help="run a prepared task and print raw hidden-test R²")
    run.add_argument("--task", required=True, type=Path)
    run.add_argument("--model", required=True)
    run.add_argument("--harbor-bin", default="harbor")
    run.add_argument("--agent", default="claude-code")
    run.add_argument("--env", default="daytona")
    run.add_argument("--job-name", default="srbench_evaluation")
    run.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    if args.command == "build":
        print(build_task(args.template, args.train, args.test, args.spec, args.output_dir, args.name))
    else:
        print(json.dumps(run_task(args.task, model=args.model, harbor_bin=args.harbor_bin,
                                  agent=args.agent, environment=args.env,
                                  job_name=args.job_name, extra=args.extra)))


if __name__ == "__main__":
    main()
