"""Training-only cross-validation followed by a single held-out evaluation."""

import hashlib
import json
import math
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import mlflow.sklearn
import numpy as np
from mlflow.models import infer_signature
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import KFold, StratifiedKFold, cross_validate

from mlexp.config import ExperimentConfig
from mlexp.data import load_split, take_rows
from mlexp.models import build_pipeline
from mlexp.tracking import get_or_create_experiment, local_client


def run_experiment(config: ExperimentConfig) -> dict:
    """Run one fixed model; no tuning or selection consumes held-out data."""
    split = load_split(config)
    train, test = split.train_indices, split.test_indices
    X_train, y_train = take_rows(split.X, train), split.y[train]
    pipeline = build_pipeline(config)
    classification = config.task == "classification"
    splitter = StratifiedKFold if classification else KFold
    cv = splitter(n_splits=config.cv_folds, shuffle=True, random_state=config.seed)
    folds = list(cv.split(X_train, y_train))
    scoring = (
        {"accuracy": "accuracy", "f1_macro": "f1_macro"}
        if classification
        else {"rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error", "r2": "r2"}
    )
    versions = {
        name: version(name)
        for name in (
            "scikit-learn",
            "numpy",
            "pandas",
            "scipy",
            "mlflow",
            "pydantic",
            "PyYAML",
            "cloudpickle",
            "joblib",
            "threadpoolctl",
            "ml-experiment-evaluation-toolkit",
        )
    }
    versions["python"] = platform.python_version()
    dataset_name = config.dataset if isinstance(config.dataset, str) else "csv"
    manifest = {
        "dataset": dataset_name,
        "dataset_sha256": split.fingerprint,
        "feature_names": split.feature_names,
        "schema": split.schema,
        "train_indices": train.tolist(),
        "test_indices": test.tolist(),
        "cv_folds": [
            {"train_indices": train[a].tolist(), "validation_indices": train[b].tolist()}
            for a, b in folds
        ],
    }
    protocol = {
        "protocol_version": 2,
        "task": config.task,
        "split": manifest,
        "scoring": scoring,
        "versions": versions,
    }
    comparison_key = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()
    client = local_client(config.tracking_uri)
    experiment_id = get_or_create_experiment(client, config.experiment, config.tracking_uri)
    run = client.create_run(
        experiment_id,
        tags={"mlexp.comparison_key": comparison_key, "mlexp.protocol_version": "2"},
        run_name=f"{dataset_name}-{config.model}-seed{config.seed}",
    )
    run_id = run.info.run_id
    try:
        with tempfile.TemporaryDirectory(prefix="mlexp-") as temporary:
            directory = Path(temporary)
            for name, value in {
                "config.json": config.model_dump(mode="json"),
                "split.json": manifest,
                "environment.json": versions,
                "protocol.json": protocol,
            }.items():
                (directory / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
                client.log_artifact(run_id, str(directory / name))
            params = config.model_dump(mode="json", exclude={"parameters", "tracking_uri"})
            params.update({f"model.{key}": value for key, value in config.parameters.items()})
            params.update({"train_rows": len(train), "test_rows": len(test)})
            # Include defaults as well as explicit overrides for reproducibility.
            params["resolved_model_parameters"] = json.dumps(
                pipeline.named_steps["model"].get_params(), sort_keys=True
            )
            for name, value in params.items():
                client.log_param(run_id, name, value)
            scores = cross_validate(
                pipeline, X_train, y_train, cv=folds, scoring=scoring, n_jobs=1, error_score="raise"
            )
            metrics = {}
            fold_scores = {}
            for name in scoring:
                values = scores[f"test_{name}"]
                if name in {"rmse", "mae"}:
                    values = -values
                metrics[f"cv_{name}"] = float(np.mean(values))
                metrics[f"cv_{name}_std"] = float(np.std(values))
                fold_scores[name] = values.tolist()
            pipeline.fit(X_train, y_train)
            # The only held-out prediction; everything above uses training rows only.
            predictions = pipeline.predict(take_rows(split.X, test))
            y_test = split.y[test]
            if classification:
                metrics.update(
                    test_accuracy=float(accuracy_score(y_test, predictions)),
                    test_f1_macro=float(
                        f1_score(y_test, predictions, average="macro", zero_division=0)
                    ),
                )
            else:
                metrics.update(
                    test_rmse=float(root_mean_squared_error(y_test, predictions)),
                    test_mae=float(mean_absolute_error(y_test, predictions)),
                    test_r2=float(r2_score(y_test, predictions)),
                )
            if not all(math.isfinite(value) for value in metrics.values()):
                raise ValueError("Evaluation produced a non-finite metric")
            for name, value in metrics.items():
                client.log_metric(run_id, name, value)
            (directory / "fold_scores.json").write_text(
                json.dumps(fold_scores, indent=2), encoding="utf-8"
            )
            client.log_artifact(run_id, str(directory / "fold_scores.json"))
            model_path = directory / "model"
            mlflow.sklearn.save_model(
                pipeline,
                path=str(model_path),
                serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
                signature=infer_signature(X_train, y_train),
                pip_requirements=[
                    f"{name}=={versions[name]}"
                    for name in (
                        "scikit-learn",
                        "numpy",
                        "pandas",
                        "scipy",
                        "cloudpickle",
                        "joblib",
                        "threadpoolctl",
                    )
                ],
            )
            client.log_artifacts(run_id, str(model_path), artifact_path="model")
        client.set_terminated(run_id, status="FINISHED")
    except BaseException as exc:
        client.set_terminated(
            run_id, status="KILLED" if isinstance(exc, KeyboardInterrupt) else "FAILED"
        )
        raise
    return {"run_id": run_id, "experiment": config.experiment, "metrics": metrics}
