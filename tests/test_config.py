import pytest
from pydantic import ValidationError

from mlexp.config import ExperimentConfig, load_config


@pytest.mark.parametrize(
    "changes",
    [
        {"unknown": True},
        {"task": "regression"},
        {"model": "ridge"},
        {"seed": -1},
        {"seed": True},
        {"seed": 2**32},
        {"test_size": 0},
        {"test_size": 1},
        {"test_size": float("nan")},
        {"validation_size": -0.1},
        {"validation_size": 1.0},
        {"validation_size": float("nan")},
        {"validation_size": True},
        {"validation_size": "0.2"},
        {"validation_size": 0.8},
        {"test_size": 0.7, "validation_size": 0.4},
        {"cv_folds": 1},
        {"cv_folds": 2.5},
        {"parameters": {"random_state": 7}},
        {"parameters": {"C": -1}},
        {"parameters": {"C": float("inf")}},
        {"parameters": {"C": True}},
        {"parameters": {"C": "1.0"}},
        {"parameters": {"max_iter": 1.5}},
        {"model": "dummy", "parameters": {"C": 1}},
        {"tracking_uri": "https://example.com"},
        {"tracking_uri": "sqlite:///:memory:"},
    ],
)
def test_invalid_config_rejected(config, changes):
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(config.model_dump() | changes)


@pytest.mark.parametrize(
    "path",
    [
        "examples/iris.yaml",
        "examples/diabetes.yaml",
        "examples/iris-dummy.yaml",
        "examples/diabetes-dummy.yaml",
    ],
)
def test_example_configs(path):
    assert load_config(path).cv_folds == 5


@pytest.mark.parametrize(
    "content", ["[]", "", "[broken", "!!python/object/apply:os.system ['echo unsafe']"]
)
def test_non_mapping_or_unsafe_yaml(tmp_path, content):
    import yaml

    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises((ValueError, yaml.YAMLError)):
        load_config(path)


def test_duplicate_yaml_keys_rejected(tmp_path):
    path = tmp_path / "duplicate.yaml"
    path.write_text("seed: 42\nseed: 7\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate YAML key"):
        load_config(path)
