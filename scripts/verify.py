"""Run local/CI checks, build a wheel, then accept it in a fresh isolated venv.

All generated environments, tracking stores, logs, and reports stay in .cache/.
Existing verification results are never removed or overwritten.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import tomllib
import uuid
import venv
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / ".cache" / "verification" / uuid.uuid4().hex
    output.mkdir(parents=True)
    environment = os.environ | {
        "PYTHONUTF8": "1",
        "PYTHONNOUSERSITE": "1",
        "MLFLOW_DISABLE_AGENT_HINT": "1",
        "MLFLOW_ENABLE_TELEMETRY": "false",
    }
    # Avoid inheriting an editable source path into the independent environment.
    environment.pop("PYTHONPATH", None)
    result = {"status": "RUNNING", "steps": []}

    def run(name, command, cwd=root):
        print(f"Running {name}", flush=True)
        log = output / f"{name}.log"
        started = time.monotonic()
        errors = output / f"{name}.stderr.log"
        with (
            log.open("w", encoding="utf-8") as handle,
            errors.open("w", encoding="utf-8") as stderr,
        ):
            completed = subprocess.run(
                [str(value) for value in command],
                cwd=cwd,
                env=environment,
                stdout=handle,
                stderr=stderr,
                check=False,
                timeout=1200,
            )
        step = {
            "name": name,
            "command": [str(value) for value in command],
            "exit_code": completed.returncode,
            "seconds": round(time.monotonic() - started, 2),
        }
        result["steps"].append(step)
        (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        if completed.returncode:
            details = log.read_text(encoding="utf-8", errors="replace") + errors.read_text(
                encoding="utf-8", errors="replace"
            )
            raise RuntimeError(f"{name} failed:\n{details[-10000:]}")
        print(f"Passed {name} ({step['seconds']}s)", flush=True)
        return log.read_text(encoding="utf-8")

    try:
        run("lint", [sys.executable, "-m", "ruff", "check", "."])
        run("format", [sys.executable, "-m", "ruff", "format", "--check", "."])
        run("pytest", [sys.executable, "-m", "pytest", "--tb=short"])
        run("build", [sys.executable, "-m", "build"])
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        name = project["name"].replace("-", "_")
        wheel = root / "dist" / f"{name}-{project['version']}-py3-none-any.whl"
        if not wheel.is_file():
            raise RuntimeError(f"Expected built wheel: {wheel.name}")
        print("Creating fresh wheel environment", flush=True)
        target = output / "venv"
        venv.EnvBuilder(with_pip=True).create(target)
        scripts = target / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        cli = scripts / ("mlexp.exe" if os.name == "nt" else "mlexp")
        run(
            "install-wheel",
            [
                python,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                wheel,
                "pytest>=8.3,<10",
            ],
        )
        run("freeze-wheel", [python, "-m", "pip", "freeze", "--all"])
        outside = output / "outside-checkout"
        outside.mkdir()
        run(
            "acceptance",
            [
                python,
                "-m",
                "pytest",
                root / "acceptance",
                "-c",
                root / "pyproject.toml",
                "--tb=short",
                "-o",
                f"cache_dir={output / 'pytest-cache'}",
            ],
            cwd=outside,
        )
        shutil.copytree(root / "examples", outside / "examples")
        for name in ("csv-classification", "csv-regression"):
            response = run(f"smoke-{name}", [cli, "run", f"examples/{name}.yaml"], cwd=outside)
            run_id = json.loads(response)["run_id"]
            run(
                f"report-{name}",
                [cli, "report", run_id, "--output", f"reports/{name}.md"],
                cwd=outside,
            )
            run(f"compare-{name}", [cli, "compare", "--experiment", name], cwd=outside)
        result["status"] = "PASSED"
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        result["status"] = "FAILED"
        result["error"] = str(exc)
        print(exc, file=sys.stderr)
    finally:
        (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Verification evidence: {output / 'result.json'}", flush=True)
    return 0 if result["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
