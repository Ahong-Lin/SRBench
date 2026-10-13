"""Three public entry points; each stage can be used independently."""
import argparse
import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="srbench", description="Generate equations, package Harbor tasks, compare laws.")
    parser.add_argument("command", choices=["generate", "package", "plot"])
    if not argv or argv[0] in {"-h", "--help"}:
        parser.print_help()
        return
    args = parser.parse_args(argv[:1])
    if args.command == "generate":
        from .generation.batch import main as run
    elif args.command == "package":
        from .packaging.pipeline import main as run
    else:
        from .plotting.compare import main as run
    try:
        run(argv[1:])
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc
