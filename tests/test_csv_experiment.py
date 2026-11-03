import json
from dataclasses import replace
from functools import wraps
from pathlib import Path

import mlflow.sklearn
import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer

from mlexp.config import ExperimentConfig
from mlexp.data import load_split, take_rows
from mlexp.experiment import run_experiment
from mlexp.tracking import local_client


@pytest.mark.parametrize(
    "task,model", [("classification", "logistic_regression"), ("regression", "ridge")]
)
def test_csv_experiments_track_schema_and_model(csv_config, task, model, tmp_path):
    if task == "regression":
        frame = pd.read_csv(csv_config.dataset.path)
        frame["label"] = np.arange(len(frame), dtype=float) * 2 + 1
        frame.to_csv(csv_config.dataset.path, index=False)
    config = ExperimentConfig.model_validate(
        csv_config.model_dump() | {"task": task, "model": model}
    )
    result = run_experiment(config)
    client = local_client(config.tracking_uri)
    assert client.get_run(result["run_id"]).info.status == "FINISHED"
    manifest = json.loads(
        Path(client.download_artifacts(result["run_id"], "split.json", str(tmp_path))).read_text()
    )
    assert manifest["schema"]["target"] == "label"
    model_path = client.download_artifacts(result["run_id"], "model", str(tmp_path))
    model = mlflow.sklearn.load_model(model_path)
    split = load_split(config)
    preprocessing = model.named_steps["preprocessor"]
    expected_median = split.X.iloc[split.train_indices]["number"].median()
    assert (
        preprocessing.named_transformers_["numeric"].named_steps["imputer"].statistics_[0]
        == expected_median
    )
    # Target is absent even after one-hot feature construction.
    assert not any("label" in name for name in preprocessing.get_feature_names_out())
    unseen = take_rows(split.X, split.test_indices).copy()
    unseen["category"] = "previously-unseen"
    predictions = model.predict(unseen)
    assert len(predictions) == len(unseen)
    if task == "regression":
        assert np.isfinite(predictions).all()


def test_csv_folds_fit_only_training_rows_and_ignore_heldout_categories(csv_config, monkeypatch):
    import mlexp.experiment as experiment

    split = load_split(csv_config)
    X = split.X.copy()
    X.loc[split.test_indices, "category"] = "heldout-only"
    monkeypatch.setattr(experiment, "load_split", lambda _: replace(split, X=X))
    fitted_rows, learned_categories = [], []
    original = ColumnTransformer.fit_transform

    @wraps(original)
    def track(self, X, y=None, **params):
        fitted_rows.append(set(X.index))
        output = original(self, X, y, **params)
        learned_categories.extend(
            self.named_transformers_["categorical"].named_steps["encoder"].categories_[0]
        )
        return output

    monkeypatch.setattr(ColumnTransformer, "fit_transform", track)
    result = run_experiment(csv_config)
    assert len(fitted_rows) == csv_config.cv_folds + 1
    assert all(rows <= set(split.train_indices) for rows in fitted_rows)
    assert all(rows.isdisjoint(split.test_indices) for rows in fitted_rows)
    assert "heldout-only" not in learned_categories
    assert local_client(csv_config.tracking_uri).get_run(result["run_id"]).info.status == "FINISHED"


@pytest.mark.parametrize("numeric,categorical", [(["number"], []), ([], ["category"])])
def test_single_type_and_all_missing_features(csv_config, numeric, categorical):
    frame = pd.read_csv(csv_config.dataset.path)
    frame = frame[numeric + categorical + ["label"]]
    frame[numeric + categorical] = np.nan
    frame.to_csv(csv_config.dataset.path, index=False)
    data = csv_config.model_dump()
    data["dataset"].update(numeric_features=numeric, categorical_features=categorical)
    result = run_experiment(ExperimentConfig.model_validate(data))
    assert np.isfinite(list(result["metrics"].values())).all()
