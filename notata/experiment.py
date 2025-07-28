from functools import partial
import csv
import json
from pathlib import Path
from typing import Any, Dict

from notata.logbook import Logbook


class Experiment:
    """
    Structured manager for organizing and accessing multiple scientific runs.

    Each Experiment instance creates an isolated folder under the base directory,
    where individual runs are stored as subdirectories. Supports adding new runs,
    recording metrics, and querying results.

    Example structure::

        experiment_name/
            index.csv
            runs/
                log_<run_id>/
                    metadata.json
                    params.yaml
                    data/
                        states.npz
                    plots/
                        loss.png
                    artifacts/
                        config.json
                        model.pkl

    Args:
        name: Name of the experiment.
        base_dir: Parent directory under which to create the experiment directory.
    """

    def __init__(self, name: str, base_dir: Path | str = "outputs"):
        self.name = name
        self.base_dir = Path(base_dir)
        self.exp_dir = self.base_dir / name
        self.runs_dir = self.exp_dir / "runs"
        self.index_file = self.exp_dir / "index.csv"

        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def add(self, skip_existing = False, **params) -> Logbook | None:
        run_id = self._generate_run_id(params)
        logdir = logdir = self.runs_dir / f"log_{run_id}"

        if skip_existing and logdir.exists():
            return None

        log = Logbook(
            run_id=run_id,
            base_dir=self.runs_dir,
            params=params,
            overwrite=False,
            preallocate=True,
            callback = partial(self.record, metrics_file="artifacts/metrics.json")
        )
        return log

    def record(self, log: Logbook, metrics_file: str = "artifacts/metrics.json"):
        run_data = {
            "run_id": log.run_id,
            **log._load_params(),
            "status": log.status,
            **self._read_metrics(log.path / metrics_file),
        }
        self._append_to_index(run_data)

    def _generate_run_id(self, params: Dict[str, Any]) -> str:
        parts = [f"{k}_{self._safe_str(v)}" for k, v in sorted(params.items())]
        return f"{self.name}_" + "_".join(parts)

    def _safe_str(self, val) -> str:
        if isinstance(val, float):
            return f"{val:.5g}"
        return str(val).replace("/", "_").replace(" ", "_")

    def _read_metrics(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"status": "missing"}
        try:
            with open(path) as f:
                data = json.load(f)
            return {"status": "complete", **data}
        except Exception as e:
            return {"status": "error", "error_reason": str(e)}

    def _append_to_index(self, row: Dict[str, Any]):
        header_exists = self.index_file.exists()

        with self.index_file.open("a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=row.keys())
            if not header_exists:
                writer.writeheader()
            writer.writerow(row)

    def to_dataframe(self):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required to convert experiment data to a DataFrame.")
        if not self.index_file.exists():
            return pd.DataFrame()
        return pd.read_csv(self.index_file)

    def select(self, **filters):
        df = self.to_dataframe()
        for key, val in filters.items():
            df = df[df[key] == val]
        return df
