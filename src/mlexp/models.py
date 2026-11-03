"""Model factories with all learned preprocessing inside the pipeline."""

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from mlexp.config import CSVDataConfig, ExperimentConfig


def build_pipeline(config: ExperimentConfig) -> Pipeline:
    parameters = dict(config.parameters)
    if "max_iter" in parameters:
        parameters["max_iter"] = int(parameters["max_iter"])
    if config.model == "logistic_regression":
        parameters.setdefault("max_iter", 1000)
        estimator = LogisticRegression(random_state=config.seed, **parameters)
    elif config.model == "ridge":
        estimator = Ridge(random_state=config.seed, **parameters)
    elif config.task == "classification":
        estimator = DummyClassifier(strategy="most_frequent", random_state=config.seed)
    else:
        estimator = DummyRegressor(strategy="mean")
    if isinstance(config.dataset, CSVDataConfig):
        numeric = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                ("scaler", StandardScaler()),
            ]
        )
        categorical = Pipeline(
            [
                (
                    "imputer",
                    SimpleImputer(
                        strategy="constant",
                        fill_value="__mlexp_missing__",
                        keep_empty_features=True,
                    ),
                ),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )
        preprocessor = ColumnTransformer(
            [
                ("numeric", numeric, config.dataset.numeric_features),
                ("categorical", categorical, config.dataset.categorical_features),
            ]
        )
        return Pipeline([("preprocessor", preprocessor), ("model", estimator)])
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", estimator),
        ]
    )
