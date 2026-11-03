import pytest

from mlexp.tracking import compare_runs, local_client, render_report


@pytest.mark.parametrize(
    "task, metric, expected",
    [("classification", "cv_accuracy", "higher"), ("regression", "cv_rmse", "lower")],
)
def test_compare_orders_only_by_cv(config, task, metric, expected):
    client = local_client(config.tracking_uri)
    experiment_id = client.create_experiment("compare")
    ids = {}
    for name, cv, test in [("higher", 0.9, 0.1), ("lower", 0.2, 0.99)]:
        run_id = client.create_run(experiment_id, tags={"mlexp.comparison_key": "same"}).info.run_id
        ids[name] = run_id
        client.log_param(run_id, "task", task)
        client.log_param(run_id, "model", "dummy")
        client.log_metric(run_id, metric, cv)
        client.log_metric(run_id, "test_accuracy", test)
        client.set_terminated(run_id)
    unfinished = client.create_run(experiment_id)
    client.log_metric(unfinished.info.run_id, metric, 100)
    rows = compare_runs("compare", config.tracking_uri)
    assert len(rows) == 2
    assert rows[0]["run_id"] == ids[expected]
    assert all("test_accuracy" not in row for row in rows)


def test_compare_rejects_mismatched_protocols(config):
    client = local_client(config.tracking_uri)
    experiment_id = client.create_experiment("mismatch")
    for key in ("first", "second"):
        run = client.create_run(experiment_id, tags={"mlexp.comparison_key": key})
        client.set_terminated(run.info.run_id)
    with pytest.raises(ValueError, match="incompatible"):
        compare_runs("mismatch", config.tracking_uri)


def test_unknown_experiment(config):
    with pytest.raises(ValueError, match="Unknown experiment"):
        compare_runs("missing", config.tracking_uri)


def test_empty_experiment(config):
    client = local_client(config.tracking_uri)
    client.create_experiment("empty")
    assert compare_runs("empty", config.tracking_uri) == []


def test_report_uses_tracked_values(completed_iris):
    config, result, _ = completed_iris
    report = render_report(result["run_id"], config.tracking_uri)
    assert result["run_id"] in report
    assert "FINISHED" in report
    assert "test_accuracy" in report
    assert "do not use them to select" in report
