"""Bounded parameter selection using only the already reserved training rows."""

import numpy as np
from sklearn.model_selection import GridSearchCV

from mlexp.config import ExperimentConfig


def fit_search(pipeline, X_train, y_train, folds, scoring, config: ExperimentConfig):
    """Refit the best CV pipeline once; this function never receives test rows."""
    primary = "accuracy" if config.task == "classification" else "rmse"
    grid = {
        f"model__{key}": [int(value) for value in values] if key == "max_iter" else values
        for key, values in config.search.parameter_grid.items()
    }
    search = GridSearchCV(
        pipeline,
        grid,
        scoring=scoring,
        refit=primary,
        cv=folds,
        n_jobs=1,
        error_score="raise",
        return_train_score=False,
    )
    search.fit(X_train, y_train)
    results = search.cv_results_
    selected = search.best_index_
    scores = {
        f"test_{metric}": np.array(
            [results[f"split{fold}_test_{metric}"][selected] for fold in range(len(folds))]
        )
        for metric in scoring
    }
    candidates = []
    for index, parameters in enumerate(results["params"]):
        fold_scores = {
            metric: [
                float(results[f"split{fold}_test_{metric}"][index])
                * (-1 if metric in {"rmse", "mae"} else 1)
                for fold in range(len(folds))
            ]
            for metric in scoring
        }
        candidates.append(
            {
                "parameters": {
                    key.removeprefix("model__"): value for key, value in parameters.items()
                },
                "rank": int(results[f"rank_test_{primary}"][index]),
                "fold_scores": fold_scores,
                "mean_scores": {key: float(np.mean(values)) for key, values in fold_scores.items()},
                "std_scores": {key: float(np.std(values)) for key, values in fold_scores.items()},
            }
        )
    details = {
        "method": "grid_search",
        "parameter_grid": config.search.parameter_grid,
        "scorer": scoring[primary],
        "selection_metric": f"cv_{primary}",
        "selected_index": int(selected),
        "selected_parameters": candidates[selected]["parameters"],
        "candidate_count": len(candidates),
        "cv_fits": len(candidates) * len(folds),
        "refit_rows": len(y_train),
        "candidates": candidates,
    }
    return search.best_estimator_, scores, details
