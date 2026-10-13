import contextlib
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from srbench.generation import batch, executors
from test_candidate_batch import options, write_candidate


def prepare_round(root, count):
    rnd = root / "_checkpoints" / "biology" / "round_001"
    batch._write_json(rnd / "round.json", {"n_scenarios": count})
    batch._write_json(rnd / "generation_complete.json", {"n_equations": count})
    path = rnd / "gen0" / "Equations" / "biology" / "equations.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("".join(json.dumps({"scenario_id": f"item_{i}"}) + "\n" for i in range(count)))
    return rnd, path


class ParallelBatchTests(unittest.TestCase):
    def test_rejection_after_executor_switch_does_not_use_filename_timezone(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            local = output / "candidate_item_20260917-220000"
            remote = output / "candidate_item_20260917-140100"
            for directory, status in [(local, "pipeline_error"), (remote, "reject_not_novel")]:
                directory.mkdir()
                batch._append_jsonl(directory / "lineage_attempts.jsonl", {"status": status})
            os.utime(local, (100, 100))
            os.utime(remote, (200, 200))
            self.assertTrue(batch.expected_rejection(output))

    def test_bounded_concurrent_jobs_single_writer_and_no_excess_generation(self):
        lock, barrier = threading.Lock(), threading.Barrier(3)
        active, peak, calls, writers = 0, 0, [], []
        append = batch._append_jsonl

        def capture_append(path, record):
            if path.name in {"formulas.jsonl", "attempts.jsonl"}:
                writers.append(threading.get_ident())
            return append(path, record)

        def fake_run(command, log, **kwargs):
            nonlocal active, peak
            i = int(command[command.index("--id") + 1].split("_")[-1])
            with lock:
                active += 1
                peak = max(peak, active)
                calls.append((i, int(command[command.index("--seed") + 1])))
            try:
                if i < 3:
                    barrier.wait(timeout=3)
                write_candidate(Path(command[command.index("--output-dir") + 1]), f"a*x+{i}")
                return 0
            finally:
                with lock:
                    active -= 1

        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            prepare_round(root, 7)
            args = options(workers=3, batch_size=7, target_per_subject=5)
            with patch.object(batch, "_run", side_effect=fake_run), patch.object(batch, "_append_jsonl", side_effect=capture_append):
                batch.collect_subject(args, "biology", root)
                batch.collect_subject(args, "biology", root)
            self.assertEqual(peak, 3)
            self.assertEqual(len(calls), 5)
            self.assertEqual(len({seed for _, seed in calls}), 5)
            for index, seed in calls:
                self.assertEqual(seed, batch.job_seed(args, "biology", 0, index + 1))
            self.assertEqual(set(writers), {threading.get_ident()})
            rows = batch._read_jsonl(root / "01_generated" / "index.jsonl")
            self.assertEqual({row["candidate_id"] for row in rows}, {f"biology_{i:03d}" for i in range(1, 6)})

    def test_error_stops_new_jobs_but_collects_running_job_then_resume_skips_it(self):
        release, barrier, calls = threading.Event(), threading.Barrier(2), []

        class ErrorStream(io.StringIO):
            def write(self, text):
                if "No new jobs will start" in text:
                    release.set()
                return super().write(text)

        def fake_run(command, log, **kwargs):
            item = command[command.index("--id") + 1]
            calls.append(item)
            barrier.wait(timeout=3)
            if item == "item_0":
                return 1
            self.assertTrue(release.wait(timeout=3))
            write_candidate(Path(command[command.index("--output-dir") + 1]), "a*x+1")
            return 0

        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(ErrorStream()):
            root = Path(tmp)
            prepare_round(root, 3)
            args = options(workers=2, target_per_subject=3)
            with patch.object(batch, "_run", side_effect=fake_run), self.assertRaisesRegex(RuntimeError, "completed results are saved"):
                batch.collect_subject(args, "biology", root)
            self.assertEqual(set(calls), {"item_0", "item_1"})
            self.assertEqual(batch.candidate_counts(root)["biology"], 1)

            def resumed(command, log, **kwargs):
                item = command[command.index("--id") + 1]
                self.assertNotEqual(item, "item_1")
                write_candidate(Path(command[command.index("--output-dir") + 1]), "a*x+" + item[-1])
                return 0

            with patch.object(batch, "_run", side_effect=resumed):
                batch.collect_subject(args, "biology", root)
            self.assertEqual(batch.candidate_counts(root)["biology"], 3)

    def test_resume_old_config_can_change_workers_and_executor_without_changing_science(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(batch, "collect_subject"), patch.object(executors, "check_daytona"):
            argv = ["--run-name", "offline", "--output-dir", tmp, "--provider", "openai", "--model", "gpt-5.6-sol"]
            batch.main(argv)
            root = Path(tmp) / "offline"
            original = (root / "batch_config.json").read_bytes()
            self.assertNotIn("workers", json.loads(original))
            batch.main(argv + ["--resume", "--workers", "30", "--executor", "daytona",
                              "--job-timeout", "2700", "--on-request-error", "stop",
                              "--max-consecutive-request-errors", "2"])
            self.assertEqual((root / "batch_config.json").read_bytes(), original)
            self.assertEqual(json.loads((root / "execution.json").read_text())["workers"], 30)
            self.assertEqual(json.loads((root / "execution.json").read_text())["on_request_error"], "stop")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                batch.main(argv + ["--resume", "--seed", "999"])

    def test_local_cancellation_terminates_the_child(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            pid_path = root / "child.pid"
            command = [sys.executable, "-c", "import os,time,sys; from pathlib import Path; "
                       "Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)", str(pid_path)]
            with self.assertRaisesRegex(RuntimeError, "exceeded"):
                executors.run_local(command, root / "job.log", timeout=0.5)
            pid = int(pid_path.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)


class DaytonaTransferTests(unittest.TestCase):
    def test_only_selected_model_credentials_are_forwarded(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-model-key", "OPENAI_BASE_URL": "https://example.test/v1",
                                    "SRBENCH_OPENAI_READ_TIMEOUT": "300", "SRBENCH_OPENAI_MAX_RETRIES": "1",
                                    "DAYTONA_API_KEY": "test-cloud-key", "ANTHROPIC_API_KEY": "unrelated-key"}, clear=True):
            env = executors.model_environment("openai")
        self.assertEqual(env["OPENAI_API_KEY"], "test-model-key")
        self.assertEqual(env["SRBENCH_OPENAI_READ_TIMEOUT"], "300")
        self.assertEqual(env["SRBENCH_OPENAI_MAX_RETRIES"], "1")
        self.assertNotIn("DAYTONA_API_KEY", env)
        self.assertNotIn("ANTHROPIC_API_KEY", env)

    def test_source_upload_excludes_env_outputs_and_bytecode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ["pyproject.toml", "src/srbench/demo.py", "src/srbench/__pycache__/demo.pyc",
                         "src/srbench/.env", ".env", "outputs/secret.json"]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test")
            archive = root / "source.tar.gz"
            executors.source_archive(archive, root)
            with tarfile.open(archive) as stream:
                self.assertEqual(set(stream.getnames()), {"pyproject.toml", "src/srbench/demo.py"})

    def test_remote_paths_are_relocated_and_candidate_is_publishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote, local = root / "remote", root / "local"
            write_candidate(remote, "a*x")
            archive = root / "artifacts.tar.gz"
            with tarfile.open(archive, "w:gz") as stream:
                stream.add(remote, arcname=".")
            executors.unpack_artifacts(archive, local, str(remote))
            shutil.rmtree(remote)
            candidate = batch.completed_candidate(local)
            self.assertIsNotNone(candidate)
            run, equation, result = candidate
            paths = batch.publish_candidate(root, "biology", 1, run, result, equation)
            self.assertTrue((root / paths["data_csv"]).exists())
            self.assertEqual(equation["expression"], "a*x")

    def test_artifact_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bad.tar.gz"
            with tarfile.open(archive, "w:gz") as stream:
                info = tarfile.TarInfo("../outside")
                info.size = 1
                stream.addfile(info, io.BytesIO(b"x"))
            with self.assertRaisesRegex(RuntimeError, "Invalid path"):
                executors.unpack_artifacts(archive, root / "output", "/remote")
            self.assertFalse((root / "outside").exists())

    def test_checkpoint_archive_keeps_latest_lineage_and_relocates_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "local"
            old, latest = output / "candidate_old", output / "candidate_latest"
            for directory in (old, latest):
                batch._write_json(directory / "manifest.json", {"base_id": "demo"})
            progress = latest / "lineage_attempt_01/progress.json"
            batch._write_json(progress, {"completed_generations": 6})
            batch._append_jsonl(latest / "lineage_attempts.jsonl", {"attempt": 1, "progress": str(progress)})
            (latest / "partial.tmp").write_text("interrupted")
            (latest / "outside").symlink_to(root)
            os.utime(old, (100, 100))
            os.utime(latest, (200, 200))
            archive = root / "checkpoint.tar.gz"
            self.assertEqual(executors.checkpoint_archive(archive, output, "/worker/output"), latest.name)
            with tarfile.open(archive) as stream:
                names = stream.getnames()
                self.assertTrue(all(name.startswith("candidate_latest") for name in names))
                self.assertNotIn("candidate_latest/partial.tmp", names)
                self.assertNotIn("candidate_latest/outside", names)
                row = json.loads(stream.extractfile("candidate_latest/lineage_attempts.jsonl").read())
                self.assertEqual(row["progress"], "/worker/output/candidate_latest/lineage_attempt_01/progress.json")
            remote_copy = root / "remote_copy"
            executors.unpack_artifacts(archive, remote_copy, "/worker/output")
            self.assertEqual(json.loads((remote_copy / "candidate_latest/lineage_attempt_01/progress.json").read_text())["completed_generations"], 6)

    def run_mock_cloud(self, transfer_failure=False, cancel=False, resume=False, timeout=False):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            rnd, equations = prepare_round(root, 2)
            remote = root / "remote"
            write_candidate(remote, "a*x")
            result_path = remote / "candidate_test" / "final_result.json"
            result_path.write_text(result_path.read_text().replace(str(remote), "/tmp/srbench-worker/output"))
            archive = root / "bundle.tar.gz"
            with tarfile.open(archive, "w:gz") as stream:
                stream.add(remote, arcname=".")
            sandbox, client = Mock(), Mock()
            sandbox.id = "fake-sandbox"
            client.create.return_value = sandbox
            sandbox.process.exec.return_value = SimpleNamespace(exit_code=0, result="")
            sandbox.process.execute_session_command.return_value = SimpleNamespace(cmd_id="cmd")
            sandbox.process.get_session_command_logs.return_value = SimpleNamespace(output="worker output\n")
            cancelled = threading.Event()

            def status(*args, **kwargs):
                if timeout:
                    raise executors.JobTimeoutError("Daytona job exceeded time limit")
                if cancel:
                    cancelled.set()
                return SimpleNamespace(exit_code=None if cancel else 0)

            sandbox.process.get_session_command.side_effect = status

            def download(remote_path, destination, timeout):
                if transfer_failure:
                    raise RuntimeError("simulated network outage")
                shutil.copy2(archive, destination)

            sandbox.fs.download_file.side_effect = download
            sdk = SimpleNamespace(Daytona=Mock(return_value=client), CreateSandboxFromSnapshotParams=SimpleNamespace,
                                  SessionExecuteRequest=SimpleNamespace)
            args = options(provider="openai", executor="daytona", job_timeout=60, resume=resume)
            output = rnd / "evolved" / "job_001"
            if resume:
                batch._write_json(output / "candidate_resume/manifest.json", {"base_id": "item_0"})
            command = batch.evolution_command(args, "biology", 0, 0, equations, "item_0", output)
            with patch.dict(sys.modules, {"daytona": sdk}), patch.dict(os.environ, {"OPENAI_API_KEY": "model-key", "DAYTONA_API_KEY": "cloud-key"}):
                if transfer_failure or cancel or timeout:
                    with self.assertRaisesRegex(RuntimeError, "could not be downloaded|cancelled|exceeded") as caught:
                        executors.run_daytona(command, rnd / "evolve_001.log", args, cancelled=cancelled)
                    if transfer_failure:
                        self.assertNotIsInstance(caught.exception, executors.JobTimeoutError)
                    elif timeout:
                        self.assertIsInstance(caught.exception, executors.JobTimeoutError)
                else:
                    self.assertEqual(executors.run_daytona(command, rnd / "evolve_001.log", args), 0)
            metadata = json.loads(next(rnd.glob("*.daytona.*.json")).read_text())
            if transfer_failure:
                client.delete.assert_not_called()
                client.stop.assert_called_once()
                self.assertEqual(metadata["status"], "artifacts_retained")
            else:
                client.delete.assert_called_once()
                self.assertEqual(metadata["status"], "deleted")
                self.assertIsNotNone(batch.completed_candidate(output))
            if cancel:
                sandbox.process.delete_session.assert_called_once()
            params = client.create.call_args.args[0]
            self.assertNotIn("DAYTONA_API_KEY", params.env_vars)
            uploads = sandbox.fs.upload_file.call_args_list
            submitted = next(item.args[0] for item in uploads if item.args[1].endswith("input.jsonl"))
            self.assertEqual(json.loads(submitted)["scenario_id"], "item_0")
            self.assertEqual(len(submitted.decode().splitlines()), 1)
            if resume:
                self.assertTrue(any(item.args[1].endswith("checkpoint.tar.gz") for item in uploads))
                self.assertEqual(metadata["resumed_checkpoint"], "candidate_resume")

    def test_cloud_lifecycle_downloads_before_deleting(self):
        self.run_mock_cloud()

    def test_cloud_resume_uploads_checkpoint_before_starting(self):
        self.run_mock_cloud(resume=True)

    def test_cloud_transfer_failure_preserves_sandbox_for_recovery(self):
        self.run_mock_cloud(transfer_failure=True)

    def test_cloud_timeout_with_failed_transfer_stops_instead_of_deferring(self):
        self.run_mock_cloud(transfer_failure=True, timeout=True)

    def test_cloud_timeout_collects_checkpoints_before_deferring(self):
        self.run_mock_cloud(timeout=True)

    def test_cloud_cancellation_collects_artifacts_and_cleans_up(self):
        self.run_mock_cloud(cancel=True)


if __name__ == "__main__":
    unittest.main()
