import json
import pytest
from pathlib import Path
from notata.reader import LogReader, ExperimentReader

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

# Test LogReader

def test_logreader_initialization(temp_dir):
    log_dir = temp_dir / "log_test"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    reader = LogReader(log_dir)
    assert reader.run_id == "test"
    assert reader.meta["status"] == "initialized"

def test_logreader_params_loading(temp_dir):
    log_dir = temp_dir / "log_params"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    (log_dir / "params.yaml").write_text("omega: 1.0\ndt: 0.01")
    reader = LogReader(log_dir)
    assert reader.params["omega"] == 1.0
    assert reader.params["dt"] == 0.01

def test_logreader_arrays(temp_dir):
    log_dir = temp_dir / "log_arrays"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    data_dir = log_dir / "data"
    data_dir.mkdir()
    import numpy as np
    np.save(data_dir / "array.npy", np.array([1, 2, 3]))
    reader = LogReader(log_dir)
    assert "array" in reader.arrays

def test_logreader_load_array(temp_dir):
    log_dir = temp_dir / "log_load_array"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    data_dir = log_dir / "data"
    data_dir.mkdir()
    import numpy as np
    np.save(data_dir / "test.npy", np.array([1, 2, 3]))
    reader = LogReader(log_dir)
    array = reader.load_array("test")
    assert array.tolist() == [1, 2, 3]

# Test ExperimentReader

def test_experimentreader_initialization(temp_dir):
    exp_dir = temp_dir / "experiment_test"
    runs_dir = exp_dir / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "log_1").mkdir()
    (runs_dir / "log_1" / "metadata.json").write_text(json.dumps({"status": "complete"}))
    (runs_dir / "log_2").mkdir()
    (runs_dir / "log_2" / "metadata.json").write_text(json.dumps({"status": "failed"}))

    reader = ExperimentReader(exp_dir)
    assert len(reader) == 2
    assert reader["1"].meta["status"] == "complete"
    assert reader["2"].meta["status"] == "failed"

def test_experimentreader_iteration(temp_dir):
    exp_dir = temp_dir / "experiment_iter"
    runs_dir = exp_dir / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "log_1").mkdir()
    (runs_dir / "log_1" / "metadata.json").write_text(json.dumps({"status": "complete"}))
    (runs_dir / "log_2").mkdir()
    (runs_dir / "log_2" / "metadata.json").write_text(json.dumps({"status": "failed"}))

    reader = ExperimentReader(exp_dir)
    statuses = [run.meta["status"] for run in reader]
    assert statuses == ["complete", "failed"]

def test_experimentreader_params(temp_dir):
    exp_dir = temp_dir / "experiment_params"
    runs_dir = exp_dir / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "log_1").mkdir()
    (runs_dir / "log_1" / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    (runs_dir / "log_1" / "params.yaml").write_text("omega: 1.0\ndt: 0.01")
    (runs_dir / "log_2").mkdir()
    (runs_dir / "log_2" / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    (runs_dir / "log_2" / "params.yaml").write_text("omega: 2.0\ndt: 0.02")

    reader = ExperimentReader(exp_dir)
    assert reader.params["1"]["omega"] == 1.0
    assert reader.params["2"]["omega"] == 2.0

def test_experimentreader_missing_runs(temp_dir):
    exp_dir = temp_dir / "experiment_empty"
    exp_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        ExperimentReader(exp_dir)