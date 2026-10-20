from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
if sys.platform == "win32":
    BASH = next((str(path) for path in [
        Path.home() / "AppData/Local/Programs/Git/bin/bash.exe",
        Path(r"C:\Program Files\Git\bin\bash.exe"),
    ] if path.exists()), BASH)


def shell_path(path):
    value = str(path).replace("\\", "/")
    if sys.platform == "win32" and len(value) > 2 and value[1] == ":":
        return "/" + value[0].lower() + value[2:]
    return value


@unittest.skipUnless(BASH, "Bash is needed for real shell-wrapper regression checks")
class CheckpointTemplateTests(unittest.TestCase):
    def run_wrapper(self, *, signal=False, checkpoint_status=85, normal_status=0, limit=1, restarts=0):
        with tempfile.TemporaryDirectory(prefix="vsc template test ") as folder:
            root = Path(folder)
            templates = root / "vsc-library/slurm templates"
            templates.mkdir(parents=True)
            shutil.copyfile(ROOT / "slurm templates/environment.sh", templates / "environment.sh")
            binary = root / "fake bin"
            binary.mkdir()
            fake_python = binary / "fake-python"
            fake_python.write_text('#!/bin/bash\nif [[ "$1" == --version ]]; then echo "test interpreter"; exit 0; fi\nexec bash "$@"\n', newline="\n")
            controller = binary / "scontrol"
            controller.write_text('#!/bin/bash\nprintf "%s\\n" "$*" > "$REQUEUE_LOG"\n', newline="\n")
            application = root / "application with spaces.sh"
            if signal:
                application.write_text(
                    '#!/bin/bash\ntrap \'echo complete > "$MARKER"; exit ' + str(checkpoint_status) + '\' USR1\n'
                    'echo ready > "$READY"\nwhile true; do sleep 0.05; done\n', newline="\n")
            else:
                application.write_text(f"#!/bin/bash\nexit {normal_status}\n", newline="\n")
            for path in (fake_python, controller, application):
                path.chmod(0o755)
            env = dict(os.environ, SLURM_SUBMIT_DIR=shell_path(root), SLURM_JOB_ID="12345678",
                       SLURM_CPUS_PER_TASK="2", SLURM_CLUSTER_NAME="wice",
                       SLURM_RESTART_COUNT=str(restarts), VSC_SCRATCH=shell_path(root / "scratch"),
                       REQUEUE_LOG=shell_path(root / "requeue"), MARKER=shell_path(root / "checkpoint"),
                       READY=shell_path(root / "ready"))
            harness = '''
export PATH="$1:$PATH"
script="$2"; project="$3"; interpreter="$4"; limit="$5"; application="$6"; send="$7"
bash "$script" "$project" "$interpreter" "$limit" "$application" &
batch=$!
if [[ "$send" == yes ]]; then
    for i in $(seq 1 100); do
        [[ -f "$READY" ]] && break
        sleep 0.05
    done
    if [[ ! -f "$READY" ]]; then kill "$batch"; exit 99; fi
    kill -USR1 "$batch"
fi
wait "$batch"
'''
            command = [BASH, "-c", harness, "harness", shell_path(binary),
                       shell_path(ROOT / "slurm templates/checkpoint.slurm"), shell_path(root),
                       shell_path(fake_python), str(limit), shell_path(application), "yes" if signal else "no"]
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
            requeue = (root / "requeue").read_text() if (root / "requeue").exists() else ""
            marker = (root / "checkpoint").exists()
            return result, requeue, marker

    def test_normal_completion_never_requeues(self):
        result, requeue, _ = self.run_wrapper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(requeue)

    def test_real_application_failure_is_retained(self):
        result, requeue, _ = self.run_wrapper(normal_status=7)
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertFalse(requeue)

    def test_status_85_without_checkpoint_request_does_not_requeue(self):
        result, requeue, _ = self.run_wrapper(normal_status=85)
        self.assertEqual(result.returncode, 85, result.stderr)
        self.assertFalse(requeue)

    def test_confirmed_checkpoint_requeues_only_after_application_exit(self):
        result, requeue, marker = self.run_wrapper(signal=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(marker)
        self.assertIn("--clusters=wice requeue 12345678", requeue)

    def test_checkpoint_failure_is_not_requeued(self):
        result, requeue, _ = self.run_wrapper(signal=True, checkpoint_status=7)
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertFalse(requeue)

    def test_opt_out_does_not_requeue(self):
        result, requeue, marker = self.run_wrapper(signal=True, limit=0)
        self.assertEqual(result.returncode, 85, result.stdout + result.stderr)
        self.assertTrue(marker)
        self.assertFalse(requeue)

    def test_restart_limit_is_enforced(self):
        result, requeue, _ = self.run_wrapper(signal=True, limit=1, restarts=1)
        self.assertEqual(result.returncode, 85, result.stdout + result.stderr)
        self.assertFalse(requeue)


@unittest.skipUnless(BASH, "Bash is needed for transfer-path regression checks")
class TransferTemplateTests(unittest.TestCase):
    def run_transfer(self, mode):
        with tempfile.TemporaryDirectory(prefix="vsc transfer test ") as folder:
            root = Path(folder)
            source = root / "source with spaces"
            source.mkdir()
            destination = root / "destination with spaces"
            binary = root / "bin"
            binary.mkdir()
            stub = binary / "rsync"
            stub.write_text('#!/bin/bash\nprintf "%s\\0" "$@" > "$COPY_LOG"\n', newline="\n")
            stub.chmod(0o755)
            src = shell_path(source)
            dst = shell_path(destination)
            if mode == "source-root":
                src = "/"
            elif mode == "same":
                dst = src
            elif mode == "nested":
                dst = src + "/child"
            elif mode == "destination-root":
                dst = "/tmp/.."
            env = dict(os.environ, COPY_LOG=shell_path(root / "copy-log"))
            command = [BASH, "-c", 'export PATH="$1:$PATH"; exec bash "$2" "$3" "$4"',
                       "harness", shell_path(binary), shell_path(ROOT / "slurm templates/transfer.slurm"), src, dst]
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
            args = (root / "copy-log").read_bytes().decode().split("\0")[:-1] if (root / "copy-log").exists() else []
            return result, args

    def test_root_source_is_refused(self):
        result, args = self.run_transfer("source-root")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(args)

    def test_same_source_and_destination_is_refused(self):
        result, args = self.run_transfer("same")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(args)

    def test_recursive_destination_is_refused(self):
        result, args = self.run_transfer("nested")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(args)

    def test_root_destination_after_normalization_is_refused(self):
        result, args = self.run_transfer("destination-root")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(args)

    def test_valid_quoted_copy_does_not_delete_or_preserve_old_timestamps(self):
        result, args = self.run_transfer("valid")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(args)
        self.assertNotIn("--delete", args)
        self.assertNotIn("-a", args)
        self.assertNotIn("-t", args)
        self.assertIn("source with spaces/", args[-2])
        self.assertIn("destination with spaces/", args[-1])


if __name__ == "__main__":
    unittest.main()
