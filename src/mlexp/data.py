"""Built-in data and deterministic, untouched test partitions."""

import hashlib
import json
from dataclasses import dataclass

import numpy as np
from sklearn.datasets import load_diabetes, load_iris
from sklearn.model_selection import train_test_split

from mlexp.config import ExperimentConfig


@dataclass(frozen=True)
class DatasetSplit:
    X: np.ndarray
    y: np.ndarray
    train_indices: np.ndarray
    test_indices: np.ndarray
    fingerprint: str
    feature_names: list[str]


def load_split(config: ExperimentConfig) -> DatasetSplit:
    """Reserve test rows before any fitting; never download external data."""
    # Raw Diabetes features avoid using the loader's full-dataset standardization.
    dataset = load_iris() if config.dataset == "iris" else load_diabetes(scaled=False)
    X, y = dataset.data, dataset.target
    digest = hashlib.sha256()
    for array in (X, y):
        digest.update(str(array.dtype).encode())
        digest.update(str(array.shape).encode())
        digest.update(np.ascontiguousarray(array).tobytes())
    digest.update(json.dumps(list(dataset.feature_names)).encode())
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
    return DatasetSplit(X, y, train, test, digest.hexdigest(), list(dataset.feature_names))
