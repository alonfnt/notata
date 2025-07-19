import json
import logging
import time
import yaml
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Any, Dict, Optional, Union, Iterable, List


class Logbook:
    """Structured container for a single scientific run or experiment.

    A `Logbook` creates an isolated run directory and provides atomic, explicit
    methods to persist parameters, arrays, plots, checkpoints, arbitrary
    artifacts, and lifecycle metadata. It also records a chronological plain
    text log and supports context manager semantics that automatically mark
    completion or failure.

    Run directory layout (illustrative):
        log_<run_id>/
            log.txt
            metadata.json
            params.yaml | params.json
            checkpoints/
                step_00001000.npz
                step_00002000.npz
            <user artifacts>.npz/.png/.pkl/.txt/.json

    Concurrency:
        Methods are not internally synchronized; external coordination is
        required if multiple threads or processes access the same instance.

    Args:
        run_id: Identifier for the run; incorporated into the directory name
            as `log_<run_id>`.
        base_dir: Parent directory under which the run directory is created.
        params: Optional parameter dictionary to persist immediately.
        overwrite: If False and the target directory exists, raises
            `FileExistsError`.
        preallocate: If True, creates an `artifacts` subdirectory eagerly.

    Attributes:
        run_id: String identifier of the run.
        path: Path object pointing to the run directory.
        log_path: Path to the chronological log file.
    """

    def __init__(
        self,
        run_id: Union[str, int],
        base_dir: Union[str, Path] = "outputs",
        params: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
        preallocate: bool = False
    ):
        self.run_id = str(run_id)
        self.path = Path(base_dir) / f"log_{self.run_id}"
        if self.path.exists() and not overwrite:
            raise FileExistsError(f"Run directory {self.path} already exists.")
        self.path.mkdir(parents=True, exist_ok=True)

        self.log_path = self.path / "log.txt"
        self.logger = self._init_logging()

        self.datadir = self.path / "data"
        self.plotdir = self.path / "plots"
        self.artifactsdir = self.path / "artifacts"
        for d in (self.datadir, self.plotdir, self.artifactsdir):
            d.mkdir(parents=True, exist_ok=True)

        self._start_time = time.time()
        if params is not None:
            self.save_params(params)


        self._write_metadata({
            "status": "initialized",
            "start_time": self._now(),
            "run_id": self.run_id
        }, replace=True)

        self.log("Logbook initialized")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            if self.current_status() not in ("complete", "failed"):
                self.mark_complete()
        else:
            self.mark_failed(str(exc_value))

    def mark_complete(self):
        """Mark the run as complete and finalize metadata."""
        runtime = round(time.time() - self._start_time, 6)
        self._write_metadata({
            "status": "complete",
            "end_time": self._now(),
            "runtime_sec": runtime
        })
        self.log("Marked complete")

    def mark_failed(self, reason: str):
        """Mark the run as failed.

        Args:
            reason: Brief description of the failure cause.
        """
        runtime = round(time.time() - self._start_time, 6)
        self._write_metadata({
            "status": "failed",
            "end_time": self._now(),
            "runtime_sec": runtime,
            "failure_reason": reason
        })
        self.log(f"Marked failed: {reason}")

    def _now(self) -> str:
        """Return current timestamp as ISO 8601 string (seconds resolution).

        Returns:
            str: Current timestamp.
        """
        return datetime.now().isoformat(timespec="seconds")

    def elapsed(self) -> float:
        """Return elapsed wall time since initialization.

        Returns:
            float: Elapsed seconds.
        """
        return time.time() - self._start_time

    def current_status(self) -> str:
        """Return the current run status.

        Returns:
            str: Status value from metadata, or 'unknown' if absent.
        """
        return self._read_metadata().get("status", "unknown")

    def _init_logging(self) -> logging.Logger:
        logger = logging.getLogger(f"notata.logbook.{self.run_id}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        self._install_file_handler(logger)
        return logger

    def _install_file_handler(self, logger: logging.Logger):
        for h in logger.handlers:
            if getattr(h, "_notata_tag", None) == self.run_id:
                return
        fh = logging.FileHandler(self.log_path, encoding="utf-8")
        # Bracketed ISO 8601 format for log messages
        fmt = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
        fh.setFormatter(fmt)
        fh.setLevel(logging.INFO)
        fh._notata_tag = self.run_id  # type: ignore[attr-defined]
        logger.addHandler(fh)

    def log(self, message: str, level: int = logging.INFO):
            self.logger.log(level, message)

    def info(self, msg): self.logger.info(msg)
    def debug(self, msg): self.logger.debug(msg)
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg): self.logger.error(msg)


    def save_params(self, params: Dict[str, Any], preferred: str = "yaml"):
        """Persist run parameters in YAML or JSON.

        Args:
            params: Parameter dictionary.
            preferred: Either 'yaml' or 'json'.

        Raises:
            ValueError: If preferred is not one of the supported formats.
        """
        if preferred == "yaml":
            with open(self.path / "params.yaml", "w") as f:
                yaml.dump(params, f, sort_keys=True)
        elif preferred == "json":
            with open(self.path / "params.json", "w") as f:
                json.dump(params, f, indent=2, sort_keys=True)
        else:
            raise ValueError("preferred must be 'yaml' or 'json'")
        self.log(f"Saved params ({preferred})")

    def _metadata_path(self) -> Path:
        """Return the metadata file path.

        Returns:
            Path: Path to metadata.json.
        """
        return self.path / "metadata.json"

    def _read_metadata(self) -> Dict[str, Any]:
        """Read metadata from disk.

        Returns:
            dict: Metadata dictionary (empty if file absent).
        """
        p = self._metadata_path()
        if not p.exists():
            return {}
        with open(p) as f:
            return json.load(f)

    def _write_metadata(self, new_data: Dict[str, Any], replace: bool = False):
        """Write metadata atomically.

        Args:
            new_data: Fields to write (or replace with).
            replace: If True, overwrite existing metadata; else merge.
        """
        merged = new_data if replace else {**self._read_metadata(), **new_data}
        tmp = self.path / "metadata.tmp"
        with open(tmp, "w") as f:
            json.dump(merged, f, indent=2, sort_keys=True)
        tmp.replace(self._metadata_path())

    def _target_dir(self, category: Optional[str], fallback: Path) -> Path:
        if category is None:
            return fallback
        p = self.path / category
        p.mkdir(parents=True, exist_ok=True)
        return p

    def save_numpy(self, name: str, array: np.ndarray, *, compressed: bool = True, category: Optional[str] = None):
        """Save a single numpy array in an .npz archive under key 'data'.

        Args:
            name: Base filename without extension.
            array: Numpy array to save.
            compressed: If True, use compressed format.
        """
        p = self._target_dir(category, self.datadir) / f"{name}.npz"
        (np.savez_compressed if compressed else np.savez)(p, data=array)
        self.log(f"Saved numpy array {name} -> {p.relative_to(self.path)}")

    def save_arrays(self, name: str, compressed: bool = True, category: Optional[str] = None, **arrays: np.ndarray):
        """Save multiple arrays into one compressed .npz archive.

        Args:
            name: Base filename without extension.
            **arrays: Named arrays (keys become archive keys).
        """
        p = self._target_dir(category, self.datadir) / f"{name}.npz"
        (np.savez_compressed if compressed else np.savez)(p, **arrays)
        self.log(f"Saved multiple arrays {name} -> {p.relative_to(self.path)}")

    def save_plot(
        self,
        name: str,
        fig: Optional[Figure] = None,
        dpi: int = 200,
        formats: Iterable[str] = ("png",),
        category: Optional[str] = None
    ):
        """Save a matplotlib figure in one or more formats.

        Args:
            name: Base filename without extension.
            fig: Figure instance; if None uses current active figure.
            dpi: DPI for raster outputs.
            formats: Iterable of file extensions (e.g., ('png','pdf')).
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError as e:
            raise RuntimeError("matplotlib not installed; install it to use save_plot()") from e

        if fig is None:
            fig = plt.gcf()

        d = self._target_dir(category, self.plotdir)
        for ext in formats:
            filename = d / f"{name}.{ext}"
            fig.savefig(str(filename), dpi=dpi, bbox_inches="tight")
        self.log(f"Saved plot {name} ({'/'.join(formats)}) -> {d.relative_to(self.path)}")

    def save_text(self, name: str, text: str, category: Optional[str] = None):
        """Save plain text.

        Args:
            name: Base filename without extension.
            text: Content to write.
        """
        p = self._target_dir(category, self.artifactsdir) / f"{name}.txt"
        with open(p, "w") as f:
            f.write(text)
        self.log(f"Saved text {name} -> {p.relative_to(self.path)}")

    def save_json(self, name: str, data: Dict[str, Any], category: Optional[str] = None):
        """Save a JSON artifact.

        Args:
            name: Base filename without extension.
            data: JSON-serializable dictionary.
        """
        p = self._target_dir(category, self.artifactsdir) / f"{name}.json"
        with open(p, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        self.log(f"Saved json {name} -> {p.relative_to(self.path)}")

    def save_pickle(self, name: str, obj: Any, protocol: int = pickle.HIGHEST_PROTOCOL, category: Optional[str] = None):
        """Serialize an object with pickle.

        Args:
            name: Base filename without extension.
            obj: Python object to serialize.
            protocol: Pickle protocol version.
        """
        p = self._target_dir(category, self.artifactsdir) / f"{name}.pkl"
        with open(p, "wb") as f:
            pickle.dump(obj, f, protocol=protocol)
        self.log(f"Saved pickle {name} -> {p.relative_to(self.path)}")

    def save_bytes(self, name: str, data: bytes, category: Optional[str] = None):
        """Save raw bytes to a file.

        Args:
            name: Filename (may include extension).
            data: Bytes to write.
        """
        p = self._target_dir(category, self.artifactsdir) / name
        with open(p, "wb") as f:
            f.write(data)
        self.log(f"Saved bytes {name} -> {p.relative_to(self.path)}")

    def artifact_path(self, *parts: str, create: bool = True) -> Path:
        """Return a path inside the run directory for custom artifacts.

        Args:
            *parts: Path components relative to the run directory.
            create: If True, ensures parent directories exist.

        Returns:
            Path: Fully qualified artifact path.
        """
        p = self.path.joinpath(*parts)
        if create:
            p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def exists(self, relative: str) -> bool:
        """Check if a relative path exists inside the run directory.

        Args:
            relative: Relative path string.

        Returns:
            bool: True if path exists, else False.
        """
        return (self.path / relative).exists()
