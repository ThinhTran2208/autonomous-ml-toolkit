import json
from collections import Counter
from dataclasses import replace
from functools import wraps
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from mlexp.config import ExperimentConfig
from mlexp.data import load_split
from mlexp.experiment import run_experiment
from mlexp.tracking import compare_runs, local_client


@pytest.mark.parametrize(
    "changes",
    [
        {"search": {"parameter_grid": {}}},
        {"search": {"parameter_grid": {"C": []}}},
        {"search": {"parameter_grid": {"C": [1, 1]}}},
        {"search": {"parameter_grid": {"C": [True]}}},
        {"search": {"parameter_grid": {"C": ["1"]}}},
        {"search": {"parameter_grid": {"C": [-1]}}},
        {"search": {"parameter_grid": {"C": [float("nan")]}}},
        {"search": {"parameter_grid": {"max_iter": [1.5]}}},
        {"search": {"parameter_grid": {"alpha": [1]}}},
        {"search": {"parameter_grid": {"random_state": [1]}}},
        {"search": {"parameter_grid": {"C": list(range(1, 10))}}},
        {"search": {"parameter_grid": {"C": list(range(1, 9)), "max_iter": list(range(1, 9))}}},
        {"cv_folds": 20, "search": {"parameter_grid": {"C": list(range(1, 9))}}},
        {"model": "dummy", "search": {"parameter_grid": {"C": [1]}}},
        {"search": {"parameter_grid": {"C": [1]}, "scoring": "test_accuracy"}},
    ],
)
def test_invalid_or_unbounded_search_rejected(config, changes):
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(config.model_dump() | changes)


@pytest.mark.parametrize(
    "task,dataset,model,key",
    [
        ("classification", "iris", "logistic_regression", "C"),
        ("regression", "diabetes", "ridge", "alpha"),
    ],
)
def test_search_cannot_observe_test_rows_or_adversarial_targets(
    config, monkeypatch, tmp_path, task, dataset, model, key
):
    import mlexp.experiment as experiment

    config = ExperimentConfig.model_validate(
        config.model_dump()
        | {
            "task": task,
            "dataset": dataset,
            "model": model,
            "search": {"parameter_grid": {key: [0.1, 10.0]}},
        }
    )
    split = load_split(config)
    X = split.X.copy()
    # A unique row marker makes even duplicate original observations distinguishable.
    X[:, 0] = np.arange(len(X)) + 100
    split = replace(split, X=X)
    monkeypatch.setattr(experiment, "load_split", lambda _: split)
    fits, test_predictions = [], []
    imputer_fit, predict = SimpleImputer.fit, Pipeline.predict

    @wraps(imputer_fit)
    def track_fit(self, X, y=None):
        rows = (X[:, 0] - 100).astype(int)
        assert set(rows) <= set(split.train_indices)
        assert set(rows).isdisjoint(split.test_indices)
        np.testing.assert_array_equal(y, split.y[rows])
        fits.append(frozenset(rows))
        return imputer_fit(self, X, y)

    @wraps(predict)
    def track_predict(self, X, **kwargs):
        rows = set((X[:, 0] - 100).astype(int))
        if rows & set(split.test_indices):
            assert rows == set(split.test_indices)
            test_predictions.append(rows)
        return predict(self, X, **kwargs)

    monkeypatch.setattr(SimpleImputer, "fit", track_fit)
    monkeypatch.setattr(Pipeline, "predict", track_predict)
    original = run_experiment(config)
    client = local_client(config.tracking_uri)

    def artifact(result, name):
        file = client.download_artifacts(result["run_id"], name, str(tmp_path))
        return json.loads(Path(file).read_text(encoding="utf-8"))

    manifest = artifact(original, "split.json")
    selection = artifact(original, "selection.json")
    expected = Counter({frozenset(fold["train_indices"]): 2 for fold in manifest["cv_folds"]})
    expected[frozenset(split.train_indices)] = 1
    assert Counter(fits) == expected
    assert len(test_predictions) == 1
    assert selection["candidate_count"] == 2
    assert selection["cv_fits"] == 2 * config.cv_folds
    assert len(selection["candidates"]) == 2
    assert selection["candidates"][selection["selected_index"]]["rank"] == 1
    run = client.get_run(original["run_id"])
    assert float(run.data.params[f"selected.{key}"]) == selection["selected_parameters"][key]
    assert (
        json.loads(run.data.params["resolved_model_parameters"])[key]
        == selection["selected_parameters"][key]
    )

    adversarial = split.y.copy()
    adversarial[split.test_indices] = (
        (adversarial[split.test_indices] + 1) % 3 if task == "classification" else 1e9
    )
    split = replace(split, y=adversarial)
    fits.clear()
    second = run_experiment(config)
    assert Counter(fits) == expected
    assert len(test_predictions) == 2  # Once per run, including the adversarial run.
    assert artifact(second, "selection.json") == selection
    for name, value in original["metrics"].items():
        if name.startswith("cv_"):
            assert second["metrics"][name] == pytest.approx(value, abs=1e-12)


def test_comparison_rejects_actual_fold_protocol_mismatch(config):
    run_experiment(config)
    changed = ExperimentConfig.model_validate(config.model_dump() | {"cv_folds": 4})
    run_experiment(changed)
    with pytest.raises(ValueError, match="incompatible evaluation protocols"):
        compare_runs(config.experiment, config.tracking_uri)


def test_integral_iteration_grid_and_fixed_parameters_are_preserved(config):
    config = ExperimentConfig.model_validate(
        config.model_dump()
        | {
            "parameters": {"C": 0.75},
            "search": {"parameter_grid": {"max_iter": [500.0]}},
        }
    )
    result = run_experiment(config)
    run = local_client(config.tracking_uri).get_run(result["run_id"])
    resolved = json.loads(run.data.params["resolved_model_parameters"])
    assert resolved["C"] == 0.75
    assert resolved["max_iter"] == 500
    assert run.data.params["selected.max_iter"] == "500"
