"""Three-way partitions must never enter training, preprocessing, or selection."""

import json
from dataclasses import replace
from functools import wraps
from pathlib import Path

import mlflow.sklearn
import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from mlexp.config import ExperimentConfig
from mlexp.data import load_split
from mlexp.experiment import run_experiment
from mlexp.tracking import compare_runs, local_client


def test_three_way_split_reproducible_and_test_reserved_first(config):
    config = ExperimentConfig.model_validate(config.model_dump() | {"validation_size": 0.2})
    first, repeated = load_split(config), load_split(config)
    parts = [first.train_indices, first.validation_indices, first.test_indices]
    assert list(map(len, parts)) == [90, 30, 30]
    assert len(set(np.concatenate(parts))) == 150
    for name in ("train_indices", "validation_indices", "test_indices"):
        np.testing.assert_array_equal(getattr(first, name), getattr(repeated, name))
    no_validation = load_split(config.model_copy(update={"validation_size": 0.0}))
    np.testing.assert_array_equal(first.test_indices, no_validation.test_indices)
    changed = load_split(config.model_copy(update={"seed": 9}))
    assert not np.array_equal(first.validation_indices, changed.validation_indices)


def test_tiny_validation_partition_rejected(config):
    config = ExperimentConfig.model_validate(
        config.model_dump()
        | {"task": "regression", "dataset": "diabetes", "model": "ridge", "validation_size": 0.001}
    )
    with pytest.raises(ValueError, match="validation partition must contain at least two"):
        load_split(config)


@pytest.mark.parametrize(
    "task,model,key",
    [("classification", "logistic_regression", "C"), ("regression", "ridge", "alpha")],
)
@pytest.mark.parametrize("search", [False, True])
def test_validation_and_test_never_affect_fits_or_selection(
    csv_config, monkeypatch, tmp_path, task, model, key, search
):
    import mlexp.experiment as experiment

    if task == "regression":
        frame = pd.read_csv(csv_config.dataset.path)
        frame["label"] = np.arange(len(frame), dtype=float) * 1.5
        frame.to_csv(csv_config.dataset.path, index=False)
    config = ExperimentConfig.model_validate(
        csv_config.model_dump()
        | {
            "task": task,
            "model": model,
            "validation_size": 0.2,
            "search": {"parameter_grid": {key: [0.1, 10.0]}} if search else None,
        }
    )
    split = load_split(config)
    fits, evaluations = [], []
    fit_transform, predict = ColumnTransformer.fit_transform, Pipeline.predict

    @wraps(fit_transform)
    def track_fit(self, X, y=None, **params):
        fits.append((X.index.tolist(), np.array(y, copy=True)))
        return fit_transform(self, X, y, **params)

    @wraps(predict)
    def track_predict(self, X, **params):
        rows = set(X.index)
        if rows & set(split.validation_indices):
            assert rows == set(split.validation_indices)
            evaluations.append("validation")
        if rows & set(split.test_indices):
            assert rows == set(split.test_indices)
            evaluations.append("test")
        return predict(self, X, **params)

    monkeypatch.setattr(ColumnTransformer, "fit_transform", track_fit)
    monkeypatch.setattr(Pipeline, "predict", track_predict)
    original = run_experiment(config)
    assert evaluations == ["validation", "test"]
    client = local_client(config.tracking_uri)

    def artifact(result, name):
        path = client.download_artifacts(result["run_id"], name, str(tmp_path))
        return json.loads(Path(path).read_text(encoding="utf-8"))

    manifest = artifact(original, "split.json")
    expected = [fold["train_indices"] for fold in manifest["cv_folds"]] * (2 if search else 1)
    expected.append(split.train_indices.tolist())
    assert len(fits) == len(expected)
    for (rows, targets), permitted in zip(fits, expected, strict=True):
        assert rows == permitted
        np.testing.assert_array_equal(targets, split.y[permitted])
        assert set(rows).isdisjoint(split.validation_indices)
        assert set(rows).isdisjoint(split.test_indices)

    heldout = np.concatenate([split.validation_indices, split.test_indices])
    X, y = split.X.copy(), split.y.copy()
    X.loc[heldout, "number"] = 1e6
    X.loc[heldout, "category"] = "heldout-only"
    y[heldout] = np.where(y[heldout] == "yes", "no", "yes") if task == "classification" else 1e9
    monkeypatch.setattr(experiment, "load_split", lambda _: replace(split, X=X, y=y))
    evaluations.clear()
    changed = run_experiment(config)
    assert evaluations == ["validation", "test"]
    assert artifact(original, "selection.json") == artifact(changed, "selection.json")
    for name, value in original["metrics"].items():
        if name.startswith("cv_"):
            assert changed["metrics"][name] == value
    fitted = mlflow.sklearn.load_model(
        client.download_artifacts(changed["run_id"], "model", str(tmp_path))
    )
    preprocessing = fitted.named_steps["preprocessor"]
    assert (
        "heldout-only"
        not in preprocessing.named_transformers_["categorical"]
        .named_steps["encoder"]
        .categories_[0]
    )
    assert (
        preprocessing.named_transformers_["numeric"].named_steps["imputer"].statistics_[0]
        == split.X.loc[split.train_indices, "number"].median()
    )


def test_compare_rejects_different_validation_partitions(config):
    first = run_experiment(config)
    config = ExperimentConfig.model_validate(config.model_dump() | {"validation_size": 0.2})
    second = run_experiment(config)
    assert first["run_id"] != second["run_id"]
    with pytest.raises(ValueError, match="incompatible"):
        compare_runs(config.experiment, config.tracking_uri)
