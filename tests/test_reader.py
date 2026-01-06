import json
import pytest
from pathlib import Path
from notata.reader import LogReader, ExperimentReader
from notata import Logbook

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

# Test LogReader

def test_logreader_missing_path(temp_dir):
    # When the logbook directory does not exist, LogReader should raise FileNotFoundError
    missing = temp_dir / "log_missing"
    assert not missing.exists()
    with pytest.raises(FileNotFoundError):
        LogReader(missing)

def test_logreader_missing_metadata(temp_dir):
    # When the directory exists but is not a valid logbook (no metadata.json), it should raise ValueError
    d = temp_dir / "log_no_meta"
    d.mkdir()
    with pytest.raises(ValueError):
        LogReader(d)

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

def test_logreader_params_json_via_logbook(temp_dir):
    # Write params via Logbook API using JSON and verify LogReader can load them
    log = Logbook("json_via_logbook", base_dir=temp_dir)
    log.params(ext="json", alpha=0.2, beta=3)
    reader = LogReader(log.path)
    assert reader.params["alpha"] == 0.2
    assert reader.params["beta"] == 3

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


def test_logreader_arrays_empty_when_missing_data(temp_dir):
    log_dir = temp_dir / "log_arrays_missing_data"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    reader = LogReader(log_dir)
    assert reader.arrays == []


def test_logreader_arrays_from_npz_listing(temp_dir):
    log_dir = temp_dir / "log_arrays_npz"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    data_dir = log_dir / "data"
    data_dir.mkdir()
    import numpy as np
    np.savez(data_dir / "bundle.npz", a=np.array([1]), b=np.array([2, 3]))
    reader = LogReader(log_dir)
    assert set(reader.arrays) == {"bundle:a", "bundle:b"}


def test_logreader_arrays_skips_corrupted_npz(temp_dir):
    log_dir = temp_dir / "log_arrays_corrupted_npz"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    data_dir = log_dir / "data"
    data_dir.mkdir()
    # Write an invalid npz file that will cause numpy.load to fail
    (data_dir / "broken.npz").write_text("not a valid npz")
    import numpy as np
    np.save(data_dir / "good.npy", np.array([4, 5, 6]))
    reader = LogReader(log_dir)
    assert reader.arrays == ["good"]

def test_logreader_params_empty_when_missing(temp_dir):
    # No params.yaml or params.json should result in empty dict
    log_dir = temp_dir / "log_no_params"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    reader = LogReader(log_dir)
    assert reader.params == {}

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

def test_logreader_load_array_from_npz(temp_dir):
    log_dir = temp_dir / "log_npz_load"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    data_dir = log_dir / "data"
    data_dir.mkdir()
    import numpy as np
    a = np.array([1, 2, 3])
    b = np.array([4, 5])
    np.savez(data_dir / "bundle.npz", a=a, b=b)
    reader = LogReader(log_dir)
    loaded_a = reader.load_array("bundle:a")
    loaded_b = reader.load_array("bundle:b")
    assert loaded_a.tolist() == [1, 2, 3]
    assert loaded_b.tolist() == [4, 5]

def test_logreader_load_array_missing_bundle(temp_dir):
    log_dir = temp_dir / "log_npz_missing_bundle"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    # No data/bundle.npz created
    reader = LogReader(log_dir)
    with pytest.raises(FileNotFoundError):
        reader.load_array("bundle:missingkey")

def test_logreader_load_array_missing_key_in_npz(temp_dir):
    log_dir = temp_dir / "log_npz_missing_key"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    data_dir = log_dir / "data"
    data_dir.mkdir()
    import numpy as np
    np.savez(data_dir / "bundle.npz", a=np.array([1, 2]))
    reader = LogReader(log_dir)
    with pytest.raises(KeyError):
        reader.load_array("bundle:other")

def test_logreader_load_array_missing_npy(temp_dir):
    log_dir = temp_dir / "log_npy_missing"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    # data/test.npy not created
    reader = LogReader(log_dir)
    with pytest.raises(FileNotFoundError):
        reader.load_array("test")

def test_logreader_artifacts_loading(temp_dir):
    log_dir = temp_dir / "log_artifacts"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    artifacts_dir = log_dir / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "metrics.json").write_text(json.dumps({"acc": 0.91}))
    (artifacts_dir / "config.json").write_text(json.dumps({"omega": 2.0, "dt": 1e-3}))

    reader = LogReader(log_dir)
    names = reader.artifacts
    assert "metrics" in names
    assert "config" in names

    metrics = reader.load_json("metrics")
    config = reader.load_json("config")
    assert metrics["acc"] == 0.91
    assert config["omega"] == 2.0


def test_logreader_artifacts_missing_returns_empty(temp_dir):
    log_dir = temp_dir / "log_artifacts_missing"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    reader = LogReader(log_dir)
    assert reader.artifacts == []


def test_logreader_load_json_missing_returns_empty(temp_dir):
    # If the JSON artifact file does not exist, load_json should return an empty dict
    log_dir = temp_dir / "log_json_missing"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    reader = LogReader(log_dir)
    assert reader.load_json("nonexistent") == {}

def test_logreader_plots_listing(temp_dir):
    log_dir = temp_dir / "log_plots"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    plots_dir = log_dir / "plots"
    plots_dir.mkdir()
    # Create dummy plot files
    (plots_dir / "trajectory.png").write_bytes(b"PNGDATA")
    (plots_dir / "phase_space.pdf").write_bytes(b"PDFDATA")

    reader = LogReader(log_dir)
    names = reader.plots
    assert "trajectory.png" in names
    assert "phase_space.pdf" in names


def test_logreader_plots_missing_returns_empty(temp_dir):
    log_dir = temp_dir / "log_plots_missing"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "initialized"}))
    reader = LogReader(log_dir)
    assert reader.plots == []

def test_logreader_str_includes_sections(temp_dir):
    log_dir = temp_dir / "log_str"
    log_dir.mkdir()
    (log_dir / "metadata.json").write_text(json.dumps({"status": "complete"}))
    (log_dir / "params.yaml").write_text("omega: 1.0\ndt: 0.01")
    data_dir = log_dir / "data"
    data_dir.mkdir()
    import numpy as np
    np.save(data_dir / "arr.npy", np.array([1]))
    artifacts_dir = log_dir / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "metrics.json").write_text(json.dumps({"acc": 0.9}))
    plots_dir = log_dir / "plots"
    plots_dir.mkdir()
    (plots_dir / "plot.png").write_bytes(b"PNG")

    reader = LogReader(log_dir)
    s = str(reader)
    assert "<LogReader 'str'>" in s
    assert "params: omega=1.0" in s
    assert "meta: status=complete" in s
    assert "arrays:" in s and "arr" in s
    assert "artifacts:" in s and "metrics" in s
    assert "plots:" in s and "plot.png" in s

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

def test_experimentreader_missing_runs_directory(temp_dir):
    exp_dir = temp_dir / "experiment_no_runs_dir"
    exp_dir.mkdir()
    # Deliberately do not create runs/ subdir
    with pytest.raises(FileNotFoundError):
        ExperimentReader(exp_dir)

def test_experimentreader_index_iterator(temp_dir):
    exp_dir = temp_dir / "experiment_index_iter"
    runs_dir = exp_dir / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "log_1").mkdir()
    (runs_dir / "log_1" / "metadata.json").write_text(json.dumps({"status": "complete"}))
    (runs_dir / "log_2").mkdir()
    (runs_dir / "log_2" / "metadata.json").write_text(json.dumps({"status": "failed"}))

    index = exp_dir / "index.csv"
    index.write_text("run_id,status,score\n1,complete,0.9\n2,failed,0.1\n")

    reader = ExperimentReader(exp_dir)
    rows = list(reader.index())
    assert rows[0]["run_id"] == "1"
    assert rows[0]["status"] == "complete"
    assert rows[0]["score"] == "0.9"
    assert rows[1]["run_id"] == "2"
    assert rows[1]["status"] == "failed"

def test_experimentreader_getitem_errors(temp_dir):
    exp_dir = temp_dir / "experiment_getitem_errors"
    runs_dir = exp_dir / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "log_0").mkdir()
    (runs_dir / "log_0" / "metadata.json").write_text(json.dumps({"status": "complete"}))

    reader = ExperimentReader(exp_dir)
    # Index out of range
    with pytest.raises(IndexError):
        _ = reader[5]
    # Wrong type
    with pytest.raises(TypeError):
        _ = reader[3.14]  # type: ignore[arg-type]
    # Missing string ID
    with pytest.raises(KeyError):
        _ = reader["missing_run"]

def test_experimentreader_str_lists_runs_and_fields(temp_dir):
    exp_dir = temp_dir / "experiment_str"
    runs_dir = exp_dir / "runs"
    runs_dir.mkdir(parents=True)
    # run A
    run_a = runs_dir / "log_A"
    run_a.mkdir()
    (run_a / "metadata.json").write_text(json.dumps({"status": "complete"}))
    # run B
    run_b = runs_dir / "log_B"
    run_b.mkdir()
    (run_b / "metadata.json").write_text(json.dumps({"status": "failed"}))
    # index.csv with fields
    (exp_dir / "index.csv").write_text("run_id,status\nA,complete\nB,failed\n")

    reader = ExperimentReader(exp_dir)
    s = str(reader)
    assert "<ExperimentReader 'experiment_str'>" in s
    assert "Index file: index.csv" in s
    assert "Fields: run_id, status" in s
    assert "Runs directory: runs" in s
    assert "- A: complete" in s
    assert "- B: failed" in s