"""Independent acceptance checks for an installed wheel, using public interfaces only.

No mlexp implementation modules or repository test helpers are imported here.
Run this suite with the clean wheel environment created by scripts/verify.py.
"""

import json
import os
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path

import mlflow.sklearn
import numpy as np
import pytest
from mlflow.tracking import MlflowClient
from sklearn.datasets import load_diabetes, load_iris
from sklearn.metrics import accuracy_score, root_mean_squared_error


@pytest.fixture(scope="session")
def cli():
    metadata = distribution("ml-experiment-evaluation-toolkit")
    direct = json.loads(metadata.read_text("direct_url.json") or "{}")
    assert not direct.get("dir_info", {}).get("editable"), "Acceptance requires a wheel install"
    executable = Path(sys.executable).parent / ("mlexp.exe" if os.name == "nt" else "mlexp")
    assert executable.is_file()
    return executable


def invoke(cli, directory, *arguments, expected=0):
    environment = os.environ | {
        "PYTHONUTF8": "1",
        "PYTHONNOUSERSITE": "1",
        "MLFLOW_DISABLE_AGENT_HINT": "1",
        "MLFLOW_ENABLE_TELEMETRY": "false",
    }
    completed = subprocess.run(
        [str(cli), *arguments],
        cwd=directory,
        env=environment,
        capture_output=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )
    assert completed.returncode == expected, completed.stdout + completed.stderr
    if expected != 0:
        assert "mlexp:" in completed.stderr
        assert "Traceback" not in completed.stderr
    return completed.stdout


def write_config(directory, task, dataset, model, **extra):
    config = {
        "experiment": f"acceptance-{dataset}",
        "task": task,
        "dataset": dataset,
        "model": model,
        "seed": 42,
        "test_size": 0.2,
        "cv_folds": 3,
        "tracking_uri": "sqlite:///acceptance.db",
    } | extra
    path = directory / f"{model}.yaml"
    # JSON is a YAML subset and keeps this independent of the toolkit's loader.
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path.name


def test_wheel_import_is_isolated_from_checkout(cli, tmp_path):
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", "-I", "-c", "import mlexp; print(mlexp.__file__)"],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    module = Path(completed.stdout.strip()).resolve()
    assert module.is_relative_to(Path(sys.prefix).resolve())
    assert "site-packages" in module.parts
    assert "run,compare,report" in invoke(cli, tmp_path, "--help")


@pytest.mark.parametrize(
    "task,dataset,model,metric",
    [
        ("classification", "iris", "logistic_regression", "accuracy"),
        ("regression", "diabetes", "ridge", "rmse"),
    ],
)
def test_builtin_workflow_and_reproducible_baselines(cli, tmp_path, task, dataset, model, metric):
    path = write_config(tmp_path, task, dataset, model)
    first = json.loads(invoke(cli, tmp_path, "run", path))
    repeated = json.loads(invoke(cli, tmp_path, "run", path))
    dummy_path = write_config(tmp_path, task, dataset, "dummy")
    dummy = json.loads(invoke(cli, tmp_path, "run", dummy_path))
    assert first["run_id"] != repeated["run_id"]
    assert first["metrics"] == pytest.approx(repeated["metrics"], abs=1e-12)
    assert np.isfinite(list(first["metrics"].values())).all()

    uri = f"sqlite:///{(tmp_path / 'acceptance.db').as_posix()}"
    client = MlflowClient(tracking_uri=uri)
    run = client.get_run(first["run_id"])
    assert run.info.status == "FINISHED"
    assert run.data.metrics == first["metrics"]
    artifacts = {item.path for item in client.list_artifacts(first["run_id"])}
    assert {
        "config.json",
        "environment.json",
        "split.json",
        "protocol.json",
        "selection.json",
        "model",
    } <= artifacts
    download = tmp_path / "download"
    download.mkdir()
    split_path = client.download_artifacts(first["run_id"], "split.json", str(download))
    manifest = json.loads(Path(split_path).read_text(encoding="utf-8"))
    data = load_iris() if dataset == "iris" else load_diabetes(scaled=False)
    train, test = manifest["train_indices"], manifest["test_indices"]
    assert set(train).isdisjoint(test)
    assert set(train) | set(test) == set(range(len(data.target)))
    validation_rows = []
    for fold in manifest["cv_folds"]:
        a, b = set(fold["train_indices"]), set(fold["validation_indices"])
        assert a.isdisjoint(b)
        assert a | b == set(train)
        assert (a | b).isdisjoint(test)
        validation_rows.extend(b)
    assert sorted(validation_rows) == sorted(train)
    fitted = mlflow.sklearn.load_model(
        client.download_artifacts(first["run_id"], "model", str(download))
    )
    np.testing.assert_allclose(fitted.named_steps["scaler"].mean_, data.data[train].mean(axis=0))
    predictions = fitted.predict(data.data[test])
    oracle = (
        accuracy_score(data.target[test], predictions)
        if task == "classification"
        else root_mean_squared_error(data.target[test], predictions)
    )
    assert first["metrics"][f"test_{metric}"] == pytest.approx(oracle, abs=1e-12)
    if task == "classification":
        assert first["metrics"]["cv_accuracy"] > dummy["metrics"]["cv_accuracy"]
    else:
        assert first["metrics"]["cv_rmse"] < dummy["metrics"]["cv_rmse"]

    comparison = json.loads(
        invoke(
            cli, tmp_path, "compare", "--experiment", f"acceptance-{dataset}", "--tracking-uri", uri
        )
    )
    assert {row["run_id"] for row in comparison} == {
        first["run_id"],
        repeated["run_id"],
        dummy["run_id"],
    }
    scores = [row["selection_score"] for row in comparison]
    assert scores == sorted(scores, reverse=task == "classification")
    assert all(row["selection_metric"] == f"cv_{metric}" for row in comparison)
    assert all(not key.startswith("test_") for row in comparison for key in row)
    report = invoke(cli, tmp_path, "report", first["run_id"], "--tracking-uri", uri)
    assert first["run_id"] in report and f"test_{metric}" in report
    invoke(cli, tmp_path, "report", first["run_id"], "--tracking-uri", uri, "--output", "report.md")
    saved = (tmp_path / "report.md").read_text(encoding="utf-8")
    invoke(
        cli,
        tmp_path,
        "report",
        first["run_id"],
        "--tracking-uri",
        uri,
        "--output",
        "report.md",
        expected=1,
    )
    assert (tmp_path / "report.md").read_text(encoding="utf-8") == saved


@pytest.mark.parametrize(
    "task,dataset,model,key",
    [
        ("classification", "iris", "logistic_regression", "C"),
        ("regression", "diabetes", "ridge", "alpha"),
    ],
)
def test_builtin_search_artifacts(cli, tmp_path, task, dataset, model, key):
    path = write_config(
        tmp_path, task, dataset, model, search={"parameter_grid": {key: [0.1, 10.0]}}
    )
    result = json.loads(invoke(cli, tmp_path, "run", path))
    client = MlflowClient(tracking_uri=f"sqlite:///{(tmp_path / 'acceptance.db').as_posix()}")
    file = client.download_artifacts(result["run_id"], "selection.json", str(tmp_path))
    selection = json.loads(Path(file).read_text(encoding="utf-8"))
    assert selection["method"] == "grid_search"
    assert selection["candidate_count"] == 2 and selection["cv_fits"] == 6
    assert selection["scorer"] in {"accuracy", "neg_root_mean_squared_error"}
    chosen = selection["candidates"][selection["selected_index"]]
    assert chosen["rank"] == 1
    metric = "accuracy" if task == "classification" else "rmse"
    assert result["metrics"][f"cv_{metric}"] == pytest.approx(chosen["mean_scores"][metric])
    assert all("test" not in key for key in selection["selected_parameters"])


def test_yaml_validation_failure_is_actionable(cli, tmp_path):
    path = write_config(tmp_path, "classification", "iris", "logistic_regression", unexpected=True)
    invoke(cli, tmp_path, "run", path, expected=1)
    (tmp_path / "unsafe.yaml").write_text(
        "!!python/object/apply:builtins.eval ['1+1']", encoding="utf-8"
    )
    invoke(cli, tmp_path, "run", "unsafe.yaml", expected=1)
