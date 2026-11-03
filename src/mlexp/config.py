"""Strict, safe YAML configuration for a deliberately small experiment surface."""

import math
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, model_validator


class CSVDataConfig(BaseModel):
    """Explicit CSV schema; the target can never be a predictor."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["csv"] = "csv"
    path: Path
    target: str = Field(min_length=1)
    numeric_features: list[str] = Field(default_factory=list)
    categorical_features: list[str] = Field(default_factory=list)
    missing_values: Literal["impute", "error"] = "impute"

    @model_validator(mode="after")
    def validate_schema(self):
        features = self.numeric_features + self.categorical_features
        if not features or any(not name.strip() for name in features + [self.target]):
            raise ValueError("Provide nonempty feature names and a target")
        if len(set(features)) != len(features):
            raise ValueError("Feature names must be unique and numeric/categorical lists disjoint")
        if self.target in features:
            raise ValueError("The target must not be included in features")
        return self


def validate_parameters(model: str, parameters: dict[str, float | int]) -> None:
    allowed = {"logistic_regression": {"C", "max_iter"}, "ridge": {"alpha"}}
    for key, value in parameters.items():
        if key not in allowed.get(model, set()):
            raise ValueError(f"Unsupported parameter for {model}: {key}")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{key} must be finite and positive")
        if key == "max_iter" and (isinstance(value, bool) or int(value) != value):
            raise ValueError("max_iter must be a positive integer")


class SearchConfig(BaseModel):
    """Small exhaustive search; users cannot raise the CPU work limits."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    parameter_grid: dict[str, list[StrictFloat | StrictInt]] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_size(self):
        if any(not values or len(values) > 8 for values in self.parameter_grid.values()):
            raise ValueError("Each search parameter needs 1 to 8 candidate values")
        if any(len(set(values)) != len(values) for values in self.parameter_grid.values()):
            raise ValueError("Search candidate values must be unique")
        if math.prod(len(values) for values in self.parameter_grid.values()) > 32:
            raise ValueError("Search is limited to 32 candidate combinations")
        return self


class ExperimentConfig(BaseModel):
    """Validated configuration; unknown fields and incompatible models are errors."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment: str = Field(min_length=1, max_length=128, pattern=r"^[\w.-]+$")
    task: Literal["classification", "regression"]
    dataset: Literal["iris", "diabetes"] | CSVDataConfig
    model: Literal["logistic_regression", "ridge", "dummy"]
    seed: Annotated[StrictInt, Field(ge=0, le=2**32 - 1)] = 42
    test_size: Annotated[float, Field(strict=True, gt=0, lt=1, allow_inf_nan=False)] = 0.2
    validation_size: Annotated[float, Field(strict=True, ge=0, lt=1, allow_inf_nan=False)] = 0.0
    cv_folds: Annotated[StrictInt, Field(ge=2, le=20)] = 5
    parameters: dict[str, StrictFloat | StrictInt] = Field(default_factory=dict)
    search: SearchConfig | None = None
    tracking_uri: str = "sqlite:///mlflow.db"

    @model_validator(mode="after")
    def validate_protocol(self):
        if self.test_size + self.validation_size >= 1:
            raise ValueError("test_size + validation_size must be less than 1")
        if isinstance(self.dataset, str):
            expected_task = {"iris": "classification", "diabetes": "regression"}[self.dataset]
            if self.task != expected_task:
                raise ValueError(f"{self.dataset} requires task={expected_task}")
        allowed_models = {
            "classification": {"logistic_regression", "dummy"},
            "regression": {"ridge", "dummy"},
        }
        if self.model not in allowed_models[self.task]:
            raise ValueError(f"{self.model} is incompatible with {self.task}")
        validate_parameters(self.model, self.parameters)
        if self.search is not None:
            for key, values in self.search.parameter_grid.items():
                for value in values:
                    validate_parameters(self.model, {key: value})
            fits = (
                math.prod(len(values) for values in self.search.parameter_grid.values())
                * self.cv_folds
            )
            if fits > 128:
                raise ValueError("Search is limited to 128 cross-validation fits, plus one refit")
        # Tracking is local-only: no implicit remote services or credentials.
        validate_tracking_uri(self.tracking_uri)
        return self


def validate_tracking_uri(uri: str) -> None:
    """Require a persistent local SQLite backend for the initial release."""
    database = uri.removeprefix("sqlite:///")
    if (
        not uri.startswith("sqlite:///")
        or not database
        or database == ":memory:"
        or "?" in database
        or "#" in database
    ):
        raise ValueError("tracking_uri must be a persistent local sqlite:/// database URI")


def load_config(path: str | Path) -> ExperimentConfig:
    """Load one YAML mapping without executing YAML object constructors."""

    class UniqueKeyLoader(yaml.SafeLoader):
        def construct_mapping(self, node, deep=False):
            self.flatten_mapping(node)
            seen = set()
            for key_node, _ in node.value:
                key = self.construct_object(key_node, deep=deep)
                try:
                    if key in seen:
                        raise ValueError(f"Duplicate YAML key: {key}")
                    seen.add(key)
                except TypeError as exc:
                    raise ValueError("YAML mapping keys must be scalar values") from exc
            return super().construct_mapping(node, deep=deep)

    with Path(path).open(encoding="utf-8") as handle:
        data = yaml.load(handle, Loader=UniqueKeyLoader)
    if not isinstance(data, dict):
        raise ValueError("Experiment YAML must contain a mapping")
    config = ExperimentConfig.model_validate(data)
    if isinstance(config.dataset, CSVDataConfig):
        resolved = (Path(path).resolve().parent / config.dataset.path).resolve()
        config = config.model_copy(
            update={"dataset": config.dataset.model_copy(update={"path": resolved})}
        )
    return config
