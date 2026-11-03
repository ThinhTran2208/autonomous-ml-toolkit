"""Built-in data and deterministic, untouched test partitions."""

import csv
import hashlib
import json
from dataclasses import dataclass, field
from io import StringIO

import numpy as np
import pandas as pd
from sklearn.datasets import load_diabetes, load_iris
from sklearn.model_selection import train_test_split

from mlexp.config import CSVDataConfig, ExperimentConfig


@dataclass(frozen=True)
class DatasetSplit:
    X: np.ndarray | pd.DataFrame
    y: np.ndarray
    train_indices: np.ndarray
    test_indices: np.ndarray
    fingerprint: str
    feature_names: list[str]
    schema: dict = field(default_factory=dict)


def take_rows(X: np.ndarray | pd.DataFrame, indices: np.ndarray):
    """Preserve named columns for CSV pipelines without changing built-in arrays."""
    return X.iloc[indices] if isinstance(X, pd.DataFrame) else X[indices]


def load_csv(source: CSVDataConfig, task: str) -> tuple[pd.DataFrame, np.ndarray, str, dict]:
    """Validate all rows without dropping data or learning preprocessing statistics."""
    content = source.path.read_bytes()
    text = content.decode("utf-8-sig")
    with StringIO(text, newline="") as handle:
        reader = csv.reader(handle, strict=True)
        header = next(reader, None)
        if not header or any(not name.strip() for name in header):
            raise ValueError("CSV requires nonempty column names")
        if len(header) != len(set(header)):
            raise ValueError("CSV contains duplicate columns")
        if source.target not in header:
            raise ValueError(f"CSV target column is absent: {source.target}")
        features = source.numeric_features + source.categorical_features
        if set(header) != set(features + [source.target]):
            raise ValueError(
                "CSV columns must match the explicit feature schema and target exactly"
            )
        for line, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(f"CSV row {line} has {len(row)} fields; expected {len(header)}")
    frame = pd.read_csv(
        StringIO(text),
        keep_default_na=False,
        na_values=[""],
        dtype={name: object for name in source.categorical_features},
    ).replace(r"^\s*$", np.nan, regex=True)
    if frame.empty:
        raise ValueError("CSV contains no data rows")
    if frame[source.target].isna().any():
        raise ValueError("CSV target contains missing values; targets are never imputed or dropped")
    for name in source.numeric_features + ([source.target] if task == "regression" else []):
        try:
            frame[name] = pd.to_numeric(frame[name], errors="raise").astype(float)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"CSV column {name!r} must contain numeric values") from exc
        if np.isinf(frame[name].to_numpy()).any():
            raise ValueError(f"CSV column {name!r} contains infinite values")
    X = frame[features].copy()
    if source.missing_values == "error" and X.isna().any().any():
        raise ValueError("CSV features contain missing values under missing_values=error")
    # Uniform string categories avoid mixed numeric/string labels in sklearn.
    for name in source.categorical_features:
        X[name] = (
            X[name].map(lambda value: str(value) if pd.notna(value) else np.nan).astype(object)
        )
    y = (
        frame[source.target].astype(str).to_numpy()
        if task == "classification"
        else frame[source.target].to_numpy()
    )
    if task == "classification" and len(np.unique(y)) < 2:
        raise ValueError("Classification requires at least two target classes")
    schema = {
        "target": source.target,
        "numeric_features": source.numeric_features,
        "categorical_features": source.categorical_features,
        "missing_values": source.missing_values,
        "target_type": "string" if task == "classification" else "number",
    }
    fingerprint = hashlib.sha256(content + json.dumps(schema, sort_keys=True).encode()).hexdigest()
    return X, y, fingerprint, schema


def load_split(config: ExperimentConfig) -> DatasetSplit:
    """Reserve test rows before any fitting; never download external data."""
    if isinstance(config.dataset, CSVDataConfig):
        X, y, fingerprint, schema = load_csv(config.dataset, config.task)
        feature_names = list(X.columns)
    else:
        # Raw Diabetes features avoid the loader's full-dataset standardization.
        dataset = load_iris() if config.dataset == "iris" else load_diabetes(scaled=False)
        X, y = dataset.data, dataset.target
        feature_names = list(dataset.feature_names)
        digest = hashlib.sha256()
        for array in (X, y):
            digest.update(str(array.dtype).encode())
            digest.update(str(array.shape).encode())
            digest.update(np.ascontiguousarray(array).tobytes())
        digest.update(json.dumps(feature_names).encode())
        fingerprint = digest.hexdigest()
        schema = {"numeric_features": feature_names, "categorical_features": [], "target": "target"}
    train, test = train_test_split(
        np.arange(len(y)),
        test_size=config.test_size,
        random_state=config.seed,
        stratify=y if config.task == "classification" else None,
    )
    if len(test) < 2:
        raise ValueError("The held-out partition must contain at least two rows")
    if config.task == "classification":
        _, counts = np.unique(y[train], return_counts=True)
        if counts.min() < config.cv_folds:
            raise ValueError("Each training class must have at least cv_folds rows")
    elif len(train) // config.cv_folds < 2:
        raise ValueError("Each regression CV validation fold must contain at least two rows")
    return DatasetSplit(X, y, train, test, fingerprint, feature_names, schema)
