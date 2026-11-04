import io
import json
import subprocess
import sys

import pytest
import yaml

from mlexp.cli import main


@pytest.mark.parametrize("encoding", ["ascii", "cp1252", "utf-8"])
@pytest.mark.parametrize("filename", ["report.md", "report-試験-é.md"])
def test_report_output_encoding(encoding, filename, tmp_path, monkeypatch):
    content = "# Report\nOriginal Unicode content: 試験 café\n"
    monkeypatch.setattr("mlexp.cli.render_report", lambda *_: content)
    stdout_bytes, stderr_bytes = io.BytesIO(), io.BytesIO()
    stdout = io.TextIOWrapper(stdout_bytes, encoding=encoding, errors="strict")
    stderr = io.TextIOWrapper(stderr_bytes, encoding=encoding, errors="strict")
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    destination = tmp_path / "reports" / filename
    args = ["report", "completed-run", "--output", str(destination)]

    assert main(args) == 0
    stdout.flush()
    stderr.flush()
    expected_path = str(destination).encode(encoding, errors="backslashreplace").decode(encoding)
    assert stdout_bytes.getvalue().decode(encoding).splitlines() == [expected_path]
    assert stderr_bytes.getvalue() == b""
    assert stdout.encoding == stderr.encoding == encoding
    assert destination.read_text(encoding="utf-8") == content
    original = destination.read_bytes()

    assert main(args) == 1
    stderr.flush()
    assert "mlexp:" in stderr_bytes.getvalue().decode(encoding)
    assert "Traceback" not in stderr_bytes.getvalue().decode(encoding)
    assert destination.read_bytes() == original


def test_run_compare_report_cli(config, tmp_path, capsys):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config.model_dump()), encoding="utf-8")
    assert main(["run", str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["metrics"]["test_accuracy"] >= 0.8
    assert (
        main(["compare", "--experiment", config.experiment, "--tracking-uri", config.tracking_uri])
        == 0
    )
    assert json.loads(capsys.readouterr().out)[0]["run_id"] == result["run_id"]
    destination = tmp_path / "reports" / "run.md"
    args = [
        "report",
        result["run_id"],
        "--tracking-uri",
        config.tracking_uri,
        "--output",
        str(destination),
    ]
    assert main(args) == 0
    capsys.readouterr()
    original = destination.read_text(encoding="utf-8")
    assert result["run_id"] in original
    assert main(args) == 1
    assert destination.read_text(encoding="utf-8") == original
    assert "mlexp:" in capsys.readouterr().err
    assert main(["report", result["run_id"], "--tracking-uri", config.tracking_uri]) == 0
    assert result["run_id"] in capsys.readouterr().out


def test_cli_errors_are_actionable(tmp_path, capsys):
    assert main(["run", str(tmp_path / "missing.yaml")]) == 1
    assert "mlexp:" in capsys.readouterr().err
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("experiment: invalid\ntask: wrong\n", encoding="utf-8")
    assert main(["run", str(invalid)]) == 1
    assert "validation errors" in capsys.readouterr().err


def test_module_entry_point():
    completed = subprocess.run(
        [sys.executable, "-m", "mlexp.cli", "--help"], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0
    assert "run,compare,report" in completed.stdout
