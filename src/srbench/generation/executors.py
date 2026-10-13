"""Execution only: one isolated output directory and seed per lineage job.

The batch coordinator owns scientific selection, deduplication and publication.
Daytona is optional; importing this module does not load its SDK or credentials.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shlex
import shutil
import signal
import subprocess
import tarfile
import tempfile
import threading
import time
import uuid
from pathlib import Path, PurePosixPath

from srbench.common.io import write_json
from srbench.generation.checkpoints import latest_run


class JobTimeoutError(RuntimeError):
    """A bounded job can be deferred while retaining its progress."""


def run_local(command, log_path, *, cancelled=None, timeout=None):
    cancelled = cancelled or threading.Event()
    if cancelled.is_set():
        raise RuntimeError("Job cancelled before start")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Running {command[2]}; log: {log_path}", flush=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\nCommand: " + json.dumps(command, ensure_ascii=False) + "\n")
        handle.flush()
        # Avoid 30 numerical jobs each starting a full BLAS thread pool.
        env = dict(os.environ)
        for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
            env[key] = "1"
        process = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=True)
        start = time.monotonic()
        try:
            while True:
                if cancelled.is_set():
                    raise RuntimeError(f"Job cancelled; partial records saved in {log_path.parent}")
                if timeout is not None and time.monotonic() - start >= timeout:
                    raise JobTimeoutError(f"Job exceeded {timeout}s; inspect {log_path}")
                try:
                    return process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                except ProcessLookupError:
                    process.wait()


def model_environment(provider):
    """Forward only credentials for the chosen model service, never .env itself."""
    if provider not in {"openai", "openrouter"}:
        raise RuntimeError("Daytona generation supports openai/openrouter")
    prefix = provider.upper()
    keys = [f"{prefix}_API_KEY", f"{prefix}_BASE_URL", f"SRBENCH_{prefix}_MAX_RETRIES",
            f"SRBENCH_{prefix}_READ_TIMEOUT"]
    if not os.environ.get(keys[0], "").strip():
        raise RuntimeError(f"Missing {keys[0]}")
    return {key: os.environ[key] for key in keys if os.environ.get(key)} | {
        "PYTHONUNBUFFERED": "1", "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    }


def check_daytona(provider):
    model_environment(provider)
    if not os.environ.get("DAYTONA_API_KEY", "").strip():
        raise RuntimeError("Missing DAYTONA_API_KEY; load your .env before running")
    try:
        from daytona import Daytona, CreateSandboxFromSnapshotParams, SessionExecuteRequest  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Install the optional executor: python -m pip install -e '.[daytona]'") from exc


def source_archive(destination, project=None):
    """Whitelist package files: no outputs, credentials, tests or user home files."""
    project = project or Path(__file__).resolve().parents[3]
    files = [project / "pyproject.toml"]
    files += sorted((project / "src" / "srbench").rglob("*"))
    with tarfile.open(destination, "w:gz") as archive:
        for path in files:
            if (not path.is_file() or path.is_symlink() or "__pycache__" in path.parts
                    or path.suffix in {".pyc", ".pyo"} or path.name.startswith(".env")):
                continue
            archive.add(path, arcname=str(path.relative_to(project)), recursive=False)
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def _relocate_paths(value, source, destination):
    if isinstance(value, str) and (value == source or value.startswith(source + "/")):
        return destination + value[len(source):]
    if isinstance(value, dict):
        return {key: _relocate_paths(item, source, destination) for key, item in value.items()}
    if isinstance(value, list):
        return [_relocate_paths(item, source, destination) for item in value]
    return value


def checkpoint_archive(destination, output, remote_output):
    """Upload only this job's latest checkpoint so remote resume also keeps generations."""
    run = latest_run(output)
    if run is None:
        return None
    with tarfile.open(destination, "w:gz") as archive:
        for path in [run, *sorted(run.rglob("*"))]:
            if path.is_symlink() or path.suffix == ".tmp" or not (path.is_file() or path.is_dir()):
                continue
            name = str(path.relative_to(output))
            if path.is_file() and path.suffix in {".json", ".jsonl"}:
                original = path.read_text(encoding="utf-8")
                def rewrite(text):
                    try:
                        value = json.loads(text)
                        for source in {str(output.absolute()), str(output.resolve())}:
                            value = _relocate_paths(value, source, remote_output)
                        return json.dumps(value, ensure_ascii=False) + "\n"
                    except json.JSONDecodeError:
                        return text
                contents = (rewrite(original) if path.suffix == ".json" else
                            "".join(rewrite(line) for line in original.splitlines(keepends=True))).encode()
                info = archive.gettarinfo(str(path), arcname=name)
                info.size = len(contents)
                archive.addfile(info, io.BytesIO(contents))
            else:
                archive.add(path, arcname=name, recursive=False)
    return run.name


def unpack_artifacts(archive_path, output, remote_output):
    """Extract into staging, relocate structured paths, then merge job artifacts."""
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="srbench-artifacts-") as directory:
        staging = Path(directory)
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive:
                relative = PurePosixPath(member.name)
                if relative.is_absolute() or ".." in relative.parts or not (member.isdir() or member.isfile()):
                    raise RuntimeError(f"Invalid path/type in worker artifacts: {member.name}")
                path = staging.joinpath(*relative.parts)
                if member.isdir():
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as src, path.open("wb") as dst:
                        shutil.copyfileobj(src, dst)

        def relocate(value):
            return _relocate_paths(value, remote_output, str(output.resolve()))

        for path in staging.rglob("*"):
            if path.suffix not in {".json", ".jsonl"} or not path.is_file():
                continue
            original = path.read_text(encoding="utf-8")
            if path.suffix == ".json":
                try:
                    write_json(path, relocate(json.loads(original)))
                except json.JSONDecodeError:
                    pass  # Preserve an interrupted diagnostic file verbatim.
            else:
                lines = []
                for line in original.splitlines(keepends=True):
                    try:
                        lines.append(json.dumps(relocate(json.loads(line)), ensure_ascii=False) + "\n")
                    except json.JSONDecodeError:
                        lines.append(line)
                path.write_text("".join(lines), encoding="utf-8")
        # Existing local job directories may contain older, failed attempts.
        for path in staging.rglob("*"):
            target = output / path.relative_to(staging)
            if not target.resolve().is_relative_to(output.resolve()):
                raise RuntimeError(f"Artifact destination escapes job directory: {target}")
        shutil.copytree(staging, output, dirs_exist_ok=True)


def run_daytona(command, log_path, args, *, cancelled=None):
    """Create one sandbox, run one lineage, copy its artifacts, then delete it.

    A transfer failure retains a stopped sandbox for manual recovery, with its
    ID in the job's .daytona.*.json file. A running coordinator is required.
    """
    check_daytona(args.provider)
    from daytona import Daytona, CreateSandboxFromSnapshotParams, SessionExecuteRequest

    cancelled = cancelled or threading.Event()
    if cancelled.is_set():
        raise RuntimeError("Job cancelled before start")
    output = Path(command[command.index("--output-dir") + 1])
    source = Path(command[command.index("--input") + 1])
    equation_id = command[command.index("--id") + 1]
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [row for row in rows if row.get("scenario_id") == equation_id]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one gen0 for {equation_id}, found {len(rows)}")
    remote = "/tmp/srbench-worker"
    remote_output = remote + "/output"
    remote_command = list(command)
    remote_command[remote_command.index("--input") + 1] = remote + "/input.jsonl"
    remote_command[remote_command.index("--output-dir") + 1] = remote_output
    name = "srbench-" + uuid.uuid4().hex
    metadata_path = log_path.with_suffix(f".daytona.{name[8:16]}.json")
    meta = {"executor": "daytona", "name": name, "equation_id": equation_id,
            "output": str(output), "remote_output": remote_output, "status": "creating"}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(metadata_path, meta)
    client, sandbox, session = Daytona(), None, None
    downloaded, started, returncode = False, time.monotonic(), None
    log_offset = 0

    with tempfile.TemporaryDirectory(prefix="srbench-upload-") as directory, log_path.open("a", encoding="utf-8") as handle:
        directory = Path(directory)

        def save(status, **extra):
            meta.update(status=status, **extra)
            write_json(metadata_path, meta)

        def remote_exec(argv):
            response = sandbox.process.exec(shlex.join(argv), timeout=60)
            if response.exit_code != 0:
                raise RuntimeError(f"Sandbox utility failed ({response.exit_code}): {response.result}")
            return response

        def append_logs():
            nonlocal log_offset
            if session is not None and meta.get("command_id"):
                logs = sandbox.process.get_session_command_logs(session, meta["command_id"], request_timeout=30)
                content = logs.output or ((logs.stdout or "") + (logs.stderr or ""))
                if len(content) < log_offset:
                    log_offset = 0
                handle.write(content[log_offset:])
                handle.flush()
                log_offset = len(content)

        try:
            archive = directory / "source.tar.gz"
            meta["source_sha256"] = source_archive(archive)
            sandbox = client.create(CreateSandboxFromSnapshotParams(
                name=name, language="python", snapshot=getattr(args, "daytona_snapshot", None),
                env_vars=model_environment(args.provider), public=False,
                labels={"app": "srbench-v7", "run": args.run_name},
                auto_stop_interval=15, auto_delete_interval=1440,
            ), timeout=60)
            save("preparing", sandbox_id=sandbox.id)
            print(f"Daytona {sandbox.id}: {equation_id}; log: {log_path}", flush=True)
            handle.write(f"\nDaytona sandbox: {sandbox.id}\nCommand: {json.dumps(remote_command, ensure_ascii=False)}\n")
            handle.flush()
            remote_exec(["mkdir", "-p", remote + "/source", remote_output])
            sandbox.fs.upload_file(str(archive), remote + "/source.tar.gz", timeout=120)
            sandbox.fs.upload_file((json.dumps(rows[0], ensure_ascii=False) + "\n").encode(), remote + "/input.jsonl", timeout=60)
            sandbox.fs.upload_file(json.dumps({"command": remote_command}).encode(), remote + "/job.json", timeout=60)
            remote_exec(["tar", "-xzf", remote + "/source.tar.gz", "-C", remote + "/source"])
            if "--resume" in command:
                checkpoint_bundle = directory / "checkpoint.tar.gz"
                checkpoint = checkpoint_archive(checkpoint_bundle, output, remote_output)
                if checkpoint is not None:
                    sandbox.fs.upload_file(str(checkpoint_bundle), remote + "/checkpoint.tar.gz", timeout=120)
                    remote_exec(["tar", "-xzf", remote + "/checkpoint.tar.gz", "-C", remote_output])
                    save("preparing", resumed_checkpoint=checkpoint)
            if cancelled.is_set():
                raise RuntimeError("Daytona job cancelled during preparation")
            if time.monotonic() - started >= args.job_timeout:
                raise JobTimeoutError("Daytona job timed out during preparation")
            session = "lineage"
            sandbox.process.create_session(session, request_timeout=30)
            response = sandbox.process.execute_session_command(session, SessionExecuteRequest(
                command=shlex.join(["python3", "-u", remote + "/source/src/srbench/generation/remote_worker.py", remote + "/job.json"]),
                run_async=True,
            ), timeout=30)
            save("running", command_id=response.cmd_id)
            while True:
                if cancelled.is_set():
                    raise RuntimeError("Daytona job cancelled; collecting partial artifacts")
                if time.monotonic() - started >= args.job_timeout:
                    raise JobTimeoutError(f"Daytona job exceeded {args.job_timeout}s")
                status = sandbox.process.get_session_command(session, response.cmd_id, request_timeout=30)
                append_logs()
                if status.exit_code is not None:
                    returncode = int(status.exit_code)
                    break
                cancelled.wait(5)
            save("collecting", returncode=returncode)
        except BaseException as exc:
            # Exception strings are metadata only; credentials never enter a command.
            save("failed", error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            if sandbox is not None:
                try:
                    append_logs()
                except Exception as exc:
                    handle.write(f"\nCould not fetch final logs: {type(exc).__name__}\n")
                if returncode is None and session is not None:
                    try:
                        sandbox.process.delete_session(session, request_timeout=30)
                    except Exception:
                        pass
                try:
                    remote_exec(["tar", "-czf", remote + "/artifacts.tar.gz", "-C", remote_output, "."])
                    bundle = directory / "artifacts.tar.gz"
                    sandbox.fs.download_file(remote + "/artifacts.tar.gz", str(bundle), 120)
                    unpack_artifacts(bundle, output, remote_output)
                    downloaded = True
                    save("downloaded", returncode=returncode)
                except Exception as exc:
                    save("artifacts_retained", transfer_error=f"{type(exc).__name__}: {exc}")
                try:
                    if downloaded:
                        client.delete(sandbox, timeout=60)
                        save("deleted")
                    else:
                        client.stop(sandbox, timeout=60)
                except Exception as exc:
                    save("cleanup_failed", cleanup_error=f"{type(exc).__name__}: {exc}")
                    print(f"Daytona cleanup needs attention: {metadata_path}", flush=True)
            handle.flush()
            if sandbox is not None and not downloaded:
                # A timeout is deferrable only after its checkpoint is safely
                # local. A failed transfer needs explicit recovery instead.
                raise RuntimeError(f"Daytona artifacts could not be downloaded; recover sandbox listed in {metadata_path}")
    if not downloaded:
        raise RuntimeError(f"Daytona artifacts could not be downloaded; recover sandbox listed in {metadata_path}")
    return returncode
