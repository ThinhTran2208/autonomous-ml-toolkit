import json
from dataclasses import replace
from functools import wraps
from pathlib import Path

import mlflow.sklearn
import numpy as np
import pytest
from sklearn.datasets import load_diabetes
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mlexp.config import ExperimentConfig
from mlexp.data import load_split
from mlexp.experiment import run_experiment
from mlexp.tracking import compare_runs, local_client


def test_split_disjoint_and_reproducible(config):
    first, second = load_split(config), load_split(config)
    assert not set(first.train_indices) & set(first.test_indices)
    assert set(first.train_indices) | set(first.test_indices) == set(range(150))
    np.testing.assert_array_equal(first.train_indices, second.train_indices)
    np.testing.assert_array_equal(first.test_indices, second.test_indices)
    assert first.fingerprint == second.fingerprint
    changed = load_split(ExperimentConfig.model_validate(config.model_dump() | {"seed": 1}))
    assert not np.array_equal(first.test_indices, changed.test_indices)


def test_mlflow_artifacts_and_trained_model(completed_iris, tmp_path):
    config, result, client = completed_iris
    run = client.get_run(result["run_id"])
    assert run.info.status == "FINISHED"
    assert 0.8 <= result["metrics"]["test_accuracy"] <= 1
    assert run.data.metrics == result["metrics"]
    paths = {artifact.path for artifact in client.list_artifacts(run.info.run_id)}
    assert {
        "model",
        "config.json",
        "split.json",
        "environment.json",
        "protocol.json",
        "fold_scores.json",
    } <= paths
    model_path = client.download_artifacts(run.info.run_id, "model", str(tmp_path))
    pipeline = mlflow.sklearn.load_model(model_path)
    split = load_split(config)
    np.testing.assert_allclose(
        pipeline.named_steps["scaler"].mean_, split.X[split.train_indices].mean(axis=0)
    )
    for artifact_name in ("config.json", "split.json", "environment.json"):
        path = client.download_artifacts(run.info.run_id, artifact_name, str(tmp_path))
        assert json.loads(Path(path).read_text(encoding="utf-8"))
    assert "random_state" in run.data.params["resolved_model_parameters"]


@pytest.mark.parametrize(
    "task, dataset, model",
    [
        ("classification", "iris", "dummy"),
        ("regression", "diabetes", "dummy"),
        ("regression", "diabetes", "ridge"),
    ],
)
def test_supported_models(config, task, dataset, model):
    config = ExperimentConfig.model_validate(
        config.model_dump() | {"task": task, "dataset": dataset, "model": model}
    )
    result = run_experiment(config)
    assert all(np.isfinite(value) for value in result["metrics"].values())
    if task == "regression":
        assert result["metrics"]["cv_rmse"] > 0
        assert result["metrics"]["cv_mae"] > 0
        np.testing.assert_array_equal(load_split(config).X, load_diabetes(scaled=False).data)
    else:
        assert result["metrics"]["test_accuracy"] == pytest.approx(1 / 3)


def test_metrics_reproduce(completed_iris):
    config, first, _ = completed_iris
    second = run_experiment(config)
    assert first["run_id"] != second["run_id"]
    assert second["metrics"] == pytest.approx(first["metrics"], abs=1e-12)


def test_preprocessing_never_fits_test_or_cv_validation_rows(config, monkeypatch):
    split = load_split(config)
    fitted_imputer_rows, fitted_scaler_rows, test_predictions = [], [], []
    imputer_fit, scaler_fit, predict = SimpleImputer.fit, StandardScaler.fit, Pipeline.predict

    def track_imputer(self, X, y=None):
        fitted_imputer_rows.append(np.array(X, copy=True))
        return imputer_fit(self, X, y)

    def track_scaler(self, X, y=None, **kwargs):
        fitted_scaler_rows.append(np.array(X, copy=True))
        return scaler_fit(self, X, y, **kwargs)

    @wraps(predict)
    def track_predict(self, X, **kwargs):
        if np.array_equal(X, split.X[split.test_indices]):
            test_predictions.append(len(X))
        return predict(self, X, **kwargs)

    monkeypatch.setattr(SimpleImputer, "fit", track_imputer)
    monkeypatch.setattr(StandardScaler, "fit", track_scaler)
    monkeypatch.setattr(Pipeline, "predict", track_predict)
    result = run_experiment(config)
    client = local_client(config.tracking_uri)
    # Read the recorded actual folds, rather than duplicating splitter logic.
    path = client.download_artifacts(result["run_id"], "split.json")
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = [split.X[fold["train_indices"]] for fold in manifest["cv_folds"]]
    expected.append(split.X[split.train_indices])
    assert len(fitted_imputer_rows) == len(expected) == len(fitted_scaler_rows)
    for imputer_rows, scaler_rows, training_rows in zip(
        fitted_imputer_rows, fitted_scaler_rows, expected, strict=True
    ):
        np.testing.assert_array_equal(imputer_rows, training_rows)
        np.testing.assert_array_equal(scaler_rows, training_rows)
    assert test_predictions == [len(split.test_indices)]


def test_test_data_cannot_change_cv_metrics_or_fitted_preprocessing(completed_iris, monkeypatch):
    import mlexp.experiment as experiment

    config, original, client = completed_iris
    split = load_split(config)
    perturbed = split.X.copy()
    perturbed[split.test_indices] += 100000
    monkeypatch.setattr(experiment, "load_split", lambda _: replace(split, X=perturbed))
    result = run_experiment(config)
    for name, value in original["metrics"].items():
        if name.startswith("cv_"):
            assert result["metrics"][name] == value
    assert client.get_run(result["run_id"]).info.status == "FINISHED"


def test_failed_training_is_recorded(config, monkeypatch):
    import mlexp.experiment as experiment

    def fail(*args, **kwargs):
        raise ValueError("deliberate estimator failure")

    monkeypatch.setattr(experiment, "cross_validate", fail)
    with pytest.raises(ValueError, match="deliberate estimator failure"):
        run_experiment(config)
    client = local_client(config.tracking_uri)
    record = client.get_experiment_by_name(config.experiment)
    runs = client.search_runs([record.experiment_id])
    assert len(runs) == 1
    assert runs[0].info.status == "FAILED"
    assert compare_runs(config.experiment, config.tracking_uri) == []


@pytest.mark.parametrize("changes", [{"test_size": 0.99}, {"test_size": 0.001}])
def test_unusable_partition_rejected(config, changes):
    config = ExperimentConfig.model_validate(config.model_dump() | changes)
    with pytest.raises(ValueError):
        load_split(config)
