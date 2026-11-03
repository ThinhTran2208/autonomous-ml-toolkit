import pytest
import yaml
from pydantic import ValidationError

from mlexp.config import CSVDataConfig, ExperimentConfig, load_config
from mlexp.data import load_split


def test_csv_schema_and_missing_values(csv_config):
    split = load_split(csv_config)
    assert len(split.y) == 60
    assert list(split.X.columns) == ["number", "category"]
    assert split.X.isna().sum().sum() == 2
    assert split.X.loc[0, "category"] == "NA"
    assert "label" not in split.feature_names
    assert split.schema["target"] == "label"
    assert set(split.train_indices).isdisjoint(split.test_indices)


@pytest.mark.parametrize(
    "changes",
    [
        {"numeric_features": ["label"]},
        {"numeric_features": ["number", "number"]},
        {"categorical_features": ["number"]},
        {"numeric_features": [], "categorical_features": []},
        {"numeric_features": [" "]},
        {"missing_values": "drop"},
    ],
)
def test_invalid_csv_schema(csv_config, changes):
    with pytest.raises(ValidationError):
        CSVDataConfig.model_validate(csv_config.dataset.model_dump() | changes)


@pytest.mark.parametrize(
    "content, message",
    [
        ("number,number,label\n1,2,yes\n", "duplicate columns"),
        ("number,category\n1,A\n", "target column is absent"),
        ("number,category,label\n1,A,\n", "target contains missing"),
        ("number,category,label\nwrong,A,yes\n", "must contain numeric"),
        ("number,category,label\nTrue,A,yes\n", "must contain numeric"),
        ("number,category,label\ninf,A,yes\n", "infinite"),
        ("number,category,label,secret\n1,A,yes,2\n", "match the explicit feature schema"),
        ("number,category,label\n1,A,yes,extra\n", "fields; expected"),
        ("number,category,label\n", "no data rows"),
        ("number,,label\n1,A,yes\n", "nonempty column names"),
        ("", "nonempty column names"),
        ("number,category,label\n1,A,yes\n2,B,yes\n", "at least two target classes"),
    ],
)
def test_invalid_csv_rows_fail_without_dropping(csv_config, content, message):
    csv_config.dataset.path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_split(csv_config)


def test_missing_value_error_policy(csv_config):
    data = csv_config.model_dump()
    data["dataset"]["missing_values"] = "error"
    with pytest.raises(ValueError, match="missing_values=error"):
        load_split(ExperimentConfig.model_validate(data))


def test_fingerprint_changes_with_file_content(csv_config):
    original = load_split(csv_config)
    content = csv_config.dataset.path.read_text(encoding="utf-8")
    csv_config.dataset.path.write_text(content.replace("south", "west"), encoding="utf-8")
    changed = load_split(csv_config)
    assert original.fingerprint != changed.fingerprint


def test_csv_paths_are_relative_to_config(csv_config, tmp_path, monkeypatch):
    data = csv_config.model_dump(mode="json")
    data["dataset"]["path"] = csv_config.dataset.path.name
    path = tmp_path / "experiment.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    loaded = load_config(path)
    assert loaded.dataset.path == csv_config.dataset.path
    assert len(load_split(loaded).y) == 60


def test_csv_classification_labels_preserve_lexical_identity(csv_config):
    labels = ["001", "1", "TRUE", "True"] * 15
    rows = [f"{index},north,{label}" for index, label in enumerate(labels)]
    csv_config.dataset.path.write_text(
        "number,category,label\n" + "\n".join(rows), encoding="utf-8"
    )
    split = load_split(csv_config)
    assert split.y.tolist() == labels
    assert len(set(split.y)) == 4
