import json
import pickle
import re
import numpy as np
import pytest
from pathlib import Path
from notata import Logbook

try:
    import matplotlib
    matplotlib.use("Agg")  # Use non-interactive backend for tests
except ImportError:
    matplotlib = None


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def listdir(p: Path):
    return sorted([x.name for x in p.iterdir()])


# ---------- Basic Initialization ----------

def test_init_creates_directory_and_metadata(tmp_path: Path):
    log = Logbook("runA", base_dir=tmp_path, params={"alpha": 0.1})
    run_dir = tmp_path / "log_runA"
    assert run_dir.is_dir()
    assert (run_dir / "params.yaml").is_file()
    m = json.loads((run_dir / "metadata.json").read_text())
    assert m["status"] == "initialized"
    assert m["run_id"] == "runA"
    assert "start_time" in m
    assert (run_dir / "log.txt").is_file()


def test_init_overwrite_flag(tmp_path: Path):
    Logbook("dup", base_dir=tmp_path)
    with pytest.raises(FileExistsError):
        Logbook("dup", base_dir=tmp_path)
    Logbook("dup", base_dir=tmp_path, overwrite=True)  # should succeed


# ---------- Context Manager Lifecycle ----------

def test_context_manager_marks_complete(tmp_path: Path):
    with Logbook("ctx1", base_dir=tmp_path):
        pass
    meta = json.loads((tmp_path / "log_ctx1" / "metadata.json").read_text())
    assert meta["status"] == "complete"
    assert "end_time" in meta
    assert "runtime_sec" in meta


def test_context_manager_marks_failed(tmp_path: Path):
    with pytest.raises(RuntimeError):
        with Logbook("ctx_fail", base_dir=tmp_path):
            raise RuntimeError("boom")
    meta = json.loads((tmp_path / "log_ctx_fail" / "metadata.json").read_text())
    assert meta["status"] == "failed"
    assert meta["failure_reason"] == "boom"


# ---------- Logging ----------

def test_log_appends_lines(tmp_path: Path):
    log = Logbook("logging", base_dir=tmp_path)
    log.log("First")
    log.log("Second")
    content = read_text(log.log_path)
    assert "First" in content
    assert "Second" in content
    lines = [ln for ln in content.strip().splitlines() if ln]
    assert all(re.match(r"\[\d{4}-\d{2}-\d{2}T", ln) for ln in lines)


# ---------- Parameter Saving ----------

def test_save_params_yaml_and_json(tmp_path: Path):
    log = Logbook("params", base_dir=tmp_path)
    log.save_params({"a": 1}, preferred="yaml")
    assert (log.path / "params.yaml").is_file()
    log.save_params({"a": 2}, preferred="json")
    assert (log.path / "params.json").is_file()
    with pytest.raises(ValueError):
        log.save_params({"x": 3}, preferred="txt")


# ---------- Metadata Helpers ----------

def test_current_status_and_elapsed(tmp_path: Path):
    log = Logbook("status", base_dir=tmp_path)
    assert log.current_status() == "initialized"
    assert log.elapsed() >= 0.0
    log.mark_complete()
    assert log.current_status() == "complete"


def test_mark_failed_sets_fields(tmp_path: Path):
    log = Logbook("failmark", base_dir=tmp_path)
    log.mark_failed("reasonX")
    m = json.loads((log.path / "metadata.json").read_text())
    assert m["status"] == "failed"
    assert m["failure_reason"] == "reasonX"
    assert "runtime_sec" in m


# ---------- Array Saving ----------

def test_save_numpy_creates_npz(tmp_path: Path):
    log = Logbook("arrays", base_dir=tmp_path)
    arr = np.arange(10)
    log.save_numpy("vec", arr)
    f = log.datadir / "vec.npz"
    assert f.is_file()
    loaded = np.load(f)
    assert np.array_equal(loaded["data"], arr)


def test_save_arrays_multiple_keys(tmp_path: Path):
    log = Logbook("multiarrays", base_dir=tmp_path)
    a = np.ones(5)
    b = np.zeros(3)
    log.save_arrays("bundle", a=a, b=b)
    z = np.load(log.datadir / "bundle.npz")
    assert np.array_equal(z["a"], a)
    assert np.array_equal(z["b"], b)


# ---------- Plot Saving ----------

def test_save_plot_png_and_pdf(tmp_path: Path):
    import matplotlib.pyplot as plt
    log = Logbook("plots", base_dir=tmp_path)
    plt.figure()
    plt.plot([0, 1], [0, 1])
    log.save_plot("line", formats=("png", "pdf"))
    assert (log.plotdir / "line.png").is_file()
    assert (log.plotdir / "line.pdf").is_file()


# ---------- Generic Artifact Saving ----------

def test_save_text_json_pickle_bytes(tmp_path: Path):
    log = Logbook("artifacts", base_dir=tmp_path)
    log.save_text("note", "hello")
    assert (log.artifactsdir / "note.txt").read_text().strip() == "hello"

    log.save_json("meta_extra", {"k": 7})
    data = json.loads((log.artifactsdir / "meta_extra.json").read_text())
    assert data["k"] == 7

    obj = {"a": [1, 2, 3]}
    log.save_pickle("obj", obj)
    with open(log.artifactsdir / "obj.pkl", "rb") as f:
        restored = pickle.load(f)
    assert restored == obj

    log.save_bytes("raw.bin", b"\x00\x01")
    assert (log.artifactsdir / "raw.bin").read_bytes() == b"\x00\x01"


# ---------- artifact_path and exists ----------

def test_artifact_path_creation_and_exists(tmp_path: Path):
    log = Logbook("artifact", base_dir=tmp_path)
    p = log.artifact_path("nested", "dir", "file.txt")
    p.write_text("data")
    assert log.exists("nested/dir/file.txt")
    assert not log.exists("nested/dir/missing.txt")


def test_artifact_path_no_create_flag(tmp_path: Path):
    log = Logbook("artifact2", base_dir=tmp_path)
    p = log.artifact_path("new", "sub", "a.txt", create=False)
    # parent not created yet
    assert not p.parent.exists()
    p.parent.mkdir(parents=True)
    p.write_text("ok")
    assert log.exists("new/sub/a.txt")


# ---------- mark_complete & mark_failed idempotency safety ----------

def test_mark_complete_multiple_calls(tmp_path: Path):
    log = Logbook("idempotent", base_dir=tmp_path)
    log.mark_complete()
    first_meta = json.loads((log.path / "metadata.json").read_text())
    assert first_meta["status"] == "complete"
    log.mark_complete()
    second_meta = json.loads((log.path / "metadata.json").read_text())
    assert second_meta["status"] == "complete"  # unchanged semantics


def test_mark_failed_after_complete(tmp_path: Path):
    log = Logbook("complete_then_fail", base_dir=tmp_path)
    log.mark_complete()
    # If user forces a failure afterwards (not recommended) it overwrites status
    log.mark_failed("forced")
    meta = json.loads((log.path / "metadata.json").read_text())
    assert meta["status"] == "failed"
    assert meta["failure_reason"] == "forced"


# ---------- Overwrite behavior for run directory ----------

def test_overwrite_true_allows_reuse(tmp_path: Path):
    Logbook("reuse", base_dir=tmp_path)
    Logbook("reuse", base_dir=tmp_path, overwrite=True)
    assert (tmp_path / "log_reuse").is_dir()


# ---------- Logging timestamps monotonic (coarse check) ----------

def test_log_timestamp_order(tmp_path: Path):
    log = Logbook("ts_order", base_dir=tmp_path)
    log.log("A")
    time1 = read_text(log.log_path).splitlines()[-1]
    log.log("B")
    time2 = read_text(log.log_path).splitlines()[-1]
    # Basic lexical timestamp ordering: second line should be >= first
    ts1 = time1.split("]")[0].strip("[")
    ts2 = time2.split("]")[0].strip("[")
    assert ts2 >= ts1
