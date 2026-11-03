"""Small wrappers around MLflow's tracking and search APIs."""

import json
import math
from pathlib import Path

from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from mlexp.config import validate_tracking_uri

DEFAULT_TRACKING_URI = "sqlite:///mlflow.db"


def local_client(tracking_uri: str) -> MlflowClient:
    validate_tracking_uri(tracking_uri)
    return MlflowClient(tracking_uri=tracking_uri)


def get_or_create_experiment(client: MlflowClient, name: str, tracking_uri: str) -> str:
    experiment = client.get_experiment_by_name(name)
    if experiment is not None:
        return experiment.experiment_id
    database = Path(tracking_uri.removeprefix("sqlite:///")).resolve()
    artifacts = database.parent / "mlartifacts" / database.stem
    try:
        return client.create_experiment(name, artifact_location=artifacts.as_uri())
    except MlflowException:
        # Another process may have created this experiment in the meantime.
        experiment = client.get_experiment_by_name(name)
        if experiment is None:
            raise
        return experiment.experiment_id


def compare_runs(experiment: str, tracking_uri: str = DEFAULT_TRACKING_URI) -> list[dict]:
    """Rank comparable finished runs by training-only CV, never final test scores."""
    client = local_client(tracking_uri)
    record = client.get_experiment_by_name(experiment)
    if record is None:
        raise ValueError(f"Unknown experiment: {experiment}")
    runs = []
    page_token = None
    while True:
        page = client.search_runs(
            [record.experiment_id],
            filter_string="attributes.status = 'FINISHED'",
            max_results=1000,
            page_token=page_token,
        )
        runs.extend(page)
        page_token = page.token
        if not page_token:
            break
    if not runs:
        return []
    cohorts = {run.data.tags.get("mlexp.comparison_key") for run in runs}
    if None in cohorts or len(cohorts) != 1:
        raise ValueError("Runs use incompatible evaluation protocols; use separate experiments")
    tasks = {run.data.params.get("task") for run in runs}
    if len(tasks) != 1 or not tasks <= {"classification", "regression"}:
        raise ValueError("Runs do not have a common supported task")
    metric = "cv_accuracy" if tasks == {"classification"} else "cv_rmse"
    if any(not math.isfinite(run.data.metrics.get(metric, float("nan"))) for run in runs):
        raise ValueError(f"Completed runs must have a finite {metric}")
    ordered = sorted(
        runs,
        key=lambda run: (
            -run.data.metrics[metric] if metric == "cv_accuracy" else run.data.metrics[metric],
            run.info.run_id,
        ),
    )
    return [
        {
            "run_id": run.info.run_id,
            "model": run.data.params.get("model"),
            "selection_metric": metric,
            "selection_score": run.data.metrics[metric],
        }
        for run in ordered
    ]


def render_report(run_id: str, tracking_uri: str = DEFAULT_TRACKING_URI) -> str:
    """Render tracked metadata without loading a model or touching the dataset."""
    run = local_client(tracking_uri).get_run(run_id)
    lines = [
        "# ML experiment report",
        "",
        f"Run: {run.info.run_id}",
        f"Status: {run.info.status}",
        "",
        "## Configuration",
        "",
        "```json",
        json.dumps(dict(sorted(run.data.params.items())), indent=2),
        "```",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {key} | {value:.6g} |" for key, value in sorted(run.data.metrics.items()))
    lines.extend(
        [
            "",
            "CV metrics use training rows only. Final test metrics are for final evaluation;",
            "do not use them to select models, parameters, features, or thresholds.",
            "Optional validation metrics are diagnostics. Only training rows fit the pipeline.",
            "Repeated test inspection compromises the held-out estimate.",
            "",
            f"Artifacts: {run.info.artifact_uri}",
            "",
        ]
    )
    return "\n".join(lines)
