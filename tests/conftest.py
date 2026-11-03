import pytest

from mlexp.config import ExperimentConfig
from mlexp.experiment import run_experiment
from mlexp.tracking import local_client


@pytest.fixture
def config(tmp_path):
    return ExperimentConfig(
        experiment="test-iris",
        task="classification",
        dataset="iris",
        model="logistic_regression",
        cv_folds=3,
        tracking_uri=f"sqlite:///{(tmp_path / 'tracking.db').as_posix()}",
    )


@pytest.fixture(scope="module")
def completed_iris(tmp_path_factory):
    directory = tmp_path_factory.mktemp("completed-iris")
    config = ExperimentConfig(
        experiment="iris",
        task="classification",
        dataset="iris",
        model="logistic_regression",
        cv_folds=3,
        tracking_uri=f"sqlite:///{(directory / 'tracking.db').as_posix()}",
    )
    result = run_experiment(config)
    return config, result, local_client(config.tracking_uri)
