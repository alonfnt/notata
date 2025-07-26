import json
import shutil
import tempfile
from pathlib import Path

import pytest

from notata import Experiment, Logbook


@pytest.fixture
def temp_dir():
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)


def test_add_creates_logbook(temp_dir):
    exp = Experiment("test_exp", base_dir=temp_dir)
    log = exp.add(omega=1.0, dt=0.01)
    assert log.path.exists()
    assert (log.path / "params.yaml").exists()


def test_record_writes_to_index(temp_dir):
    exp = Experiment("test_exp", base_dir=temp_dir)
    log = exp.add(alpha=0.5)

    metrics_path = log.path / "artifacts" / "metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump({"final_loss": 0.123}, f)

    exp.record(log)

    index_file = exp.index_file
    assert index_file.exists()
    with open(index_file) as f:
        lines = f.readlines()
    assert "run_id" in lines[0]
    assert "test_exp_alpha_0.5" in lines[1]


def test_select_filters_results(temp_dir):
    exp = Experiment("test_exp", base_dir=temp_dir)

    for a in [0.1, 0.2]:
        log = exp.add(a=a)
        metrics_path = log.path / "artifacts" / "metrics.json"
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, "w") as f:
            json.dump({"score": a * 10}, f)
        exp.record(log)

    df = exp.select(a=0.1)
    assert len(df) == 1
    assert df.iloc[0]["score"] == 1.0


def test_handles_missing_metrics(temp_dir):
    exp = Experiment("test_exp", base_dir=temp_dir)
    log = exp.add(b=5)
    exp.record(log)  # no metrics.json written
    df = exp.to_dataframe()
    assert df.iloc[0]["status"] == "missing"


def test_handles_corrupt_metrics(temp_dir):
    exp = Experiment("test_exp", base_dir=temp_dir)
    log = exp.add(c=3)
    path = log.path / "artifacts" / "metrics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not: valid json")
    exp.record(log)
    df = exp.to_dataframe()
    assert df.iloc[0]["status"] == "error"


def test_callback_invoked_on_mark_complete(temp_dir):
    exp = Experiment("callback_exp", base_dir=temp_dir)
    log = exp.add(x=42)

    metrics = {"accuracy": 0.99}
    metrics_path = log.path / "artifacts" / "metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics))

    log.mark_complete()

    index_df = exp.to_dataframe()
    assert len(index_df) == 1
    row = index_df.iloc[0]
    assert row["run_id"] == log.run_id
    assert row["status"] == "complete"
    assert row["accuracy"] == 0.99
    assert row["x"] == 42