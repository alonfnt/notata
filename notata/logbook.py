import json
import logging
import time
import yaml
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Union, Iterable, Callable

try:
    from matplotlib.figure import Figure
except ImportError:
    Figure = Any


class Logbook:
    """
    Structured log directory for a single scientific run.

    Each Logbook instance creates an isolated folder under the base directory,
    where parameters, metadata, logs, arrays, plots, and other artifacts can be saved.
    Supports context-manager semantics to automatically mark success/failure.

    Example structure::

        log_<run_id>/
            log.txt
            metadata.json
            params.yaml
            data/
                states.npz
            plots/
                loss.png
            artifacts/
                config.json
                model.pkl

    Note:
        Logbook methods are not thread- or process-safe. Use external coordination
        when logging from multiple workers.

    Args:
        run_id: Unique string or int identifying the run.
        base_dir: Parent directory under which to create the log directory.
        params: Optional parameters to save immediately.
        overwrite: If True, overwrite any existing run directory.
        preallocate: If True, pre-create standard subdirectories.
        callback: Optional function to call when marking the run as complete or failed.
                    It receives the Logbook instance as the only argument.
    """

    def __init__(
        self,
        run_id: Union[str, int],
        base_dir: Union[str, Path] = "outputs",
        params: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
        preallocate: bool = False,
        callback: Optional[Callable] = None
        ):
        self.run_id = str(run_id)
        self.path = Path(base_dir) / f"log_{self.run_id}"
        self.callback = callback

        if self.path.exists() and not overwrite:
            raise FileExistsError(f"Run directory {self.path} already exists.")
        self.path.mkdir(parents=True, exist_ok=True)

        self.log_path = self.path / "log.txt"
        self.logger = self._init_logging()

        self.datadir = self.path / "data"
        self.plotdir = self.path / "plots"
        self.artifactsdir = self.path / "artifacts"

        if preallocate:
            for d in (self.datadir, self.plotdir, self.artifactsdir):
                d.mkdir(parents=True, exist_ok=True)

        self._start_time = time.time()

        if params:
            self.params(**params)

        self.meta(status="initialized", start_time=self._now, run_id=self.run_id)
        self.info("Logbook initialized")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            if self.status not in ("complete", "failed"):
                self.mark_complete()
        else:
            reason = str(exc_value) or f"{exc_type.__name__}: {exc_value}"
            self.mark_failed(reason)

    def mark_complete(self):
        """Mark the run as complete and finalize metadata."""
        runtime = round(self.elapsed, 6)
        self.meta(status="complete", end_time=self._now, runtime_sec=runtime)
        self.info("Marked complete")
        if self.callback:
            self.callback(self)

    def mark_failed(self, reason: str):
        """Mark the run as failed.

        Args:
            reason: Brief description of the failure cause.
        """
        runtime = round(self.elapsed, 6)
        self.meta(status="failed", end_time=self._now, runtime_sec=runtime, failure_reason=reason)
        self.info(f"Marked failed: {reason}")
        if self.callback:
            self.callback(self)

    @property
    def _now(self) -> str:
        """Return current timestamp as ISO 8601 string (seconds resolution)."""
        return datetime.now().isoformat(timespec="seconds")

    @property
    def elapsed(self) -> float:
        """Elapsed wall time in seconds since initialization."""
        return time.time() - self._start_time

    @property
    def status(self) -> str:
        """Current run status.
        ['initialized', 'complete', 'failed', 'unknown']
        """
        return self._read_metadata().get("status", "unknown")

    def _init_logging(self) -> logging.Logger:
        logger = logging.getLogger(f"notata.logbook.{self.run_id}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        self._install_file_handler(logger)
        return logger

    def _install_file_handler(self, logger: logging.Logger):
        if any(getattr(h, "_notata_tag", None) == self.run_id for h in logger.handlers):
            return
        fh = logging.FileHandler(self.log_path, encoding="utf-8")
        fmt = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
        fh.setFormatter(fmt)
        fh.setLevel(logging.INFO)
        fh._notata_tag = self.run_id  # type: ignore[attr-defined]
        logger.addHandler(fh)

    def note(self, message: str, level: int = logging.INFO):
            self.logger.log(level, message)

    def info(self, msg): self.logger.info(msg)
    def debug(self, msg): self.logger.debug(msg)
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg): self.logger.error(msg)

    def meta(self, **fields: Any):
        """Update metadata.json with new fields (atomic merge)."""
        meta = self._read_metadata()
        meta.update(fields)
        tmp = self.path / "metadata.tmp"
        with open(tmp, "w") as f:
            json.dump(meta, f, indent=2, sort_keys=True)
        target_path = self.path / "metadata.json"
        tmp.replace(target_path)


    def _load_params(self) -> Dict[str, Any]:
        """Load parameters from params.yaml or params.json (if present)."""
        yaml_path = self.path / "params.yaml"
        json_path = self.path / "params.json"

        if yaml_path.exists():
            with open(yaml_path) as f:
                return yaml.safe_load(f) or {}

        elif json_path.exists():
            with open(json_path) as f:
                return json.load(f)

        return {}

    def params(self, ext: str = "yaml", **kwargs: Any):
        """Write run parameters in YAML or JSON.

        Args:
            ext: Either 'yaml' or 'json'.
            **kwargs: Parameters to save.

        Raises:
            ValueError: If ext is not one of the supported formats.
        """
        path = self.path / f"params.{ext}"
        existing = self._load_params()
        updated = {**existing, **kwargs}
        with open(path, "w") as f:
            if ext == "yaml":
                yaml.dump(updated, f, sort_keys=True)
            elif ext == "json":
                json.dump(updated, f, indent=2, sort_keys=True)
            else:
                raise ValueError("ext must be 'yaml' or 'json'")
        self.info(f"Saved params ({ext}) in {path.relative_to(self.path)}")

    def _read_metadata(self) -> Dict[str, Any]:
        """Read metadata from disk."""
        path = self.path / "metadata.json"
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def _target_dir(self, category: Optional[str], fallback: Path) -> Path:
        if category is None:
            return fallback
        p = self.path / category
        p.mkdir(parents=True, exist_ok=True)
        return p

    def array(self, name: str, array: np.ndarray):
        """Save a single NumPy array in .npy format.

        Args:
            name: Base filename without extension.
            array: Numpy array to save.

        Example:
            >>> log.array("velocity", np.array([0, 1, 2]))
        """
        path = self.datadir / f"{name}.npy"
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, array)
        self.info(f"Saved array {name} in {path.relative_to(self.path)}")

    def arrays(self, name: str, compressed: bool = True, **arrays: np.ndarray):
        """Save multiple arrays into one compressed .npz archive.

        Args:
            name: Base filename without extension.
            compressed: If True, use compressed format.
            **arrays: Named arrays (keys become archive keys).
         """
        path = self.datadir / f"{name}.npz"
        path.parent.mkdir(parents=True, exist_ok=True)
        saver = np.savez_compressed if compressed else np.savez
        saver(path, **arrays)
        self.info(f"Saved arrays {name} in {path.relative_to(self.path)}")

    def plot(
        self,
        name: str,
        fig: Optional[Figure] = None,
        dpi: int = 200,
        formats: Iterable[str] = ("png",)
    ):
        """Save a matplotlib figure to `plots/{name}.{ext}`.

        If no figure is provided, the current active figure (`plt.gcf()`) is used.
        Supports saving in multiple formats simultaneously (e.g., PNG and PDF).

        Args:
            name: Base filename without extension.
            fig: Matplotlib figure to save. Defaults to current figure.
            dpi: Resolution (dots per inch) for raster formats like PNG.
            formats: List or tuple of file extensions to save (e.g., ("png", "pdf")).

        Raises:
            RuntimeError: If matplotlib is not installed.

        Example:
            >>> log.plot("trajectory", fig=fig, formats=("png", "pdf"))
        """
        if fig is None:
            try:
                import matplotlib.pyplot as plt
            except ImportError:
                raise RuntimeError("matplotlib is required to save plots. Install it with `pip install matplotlib`.")
            fig = plt.gcf()

        for ext in formats:
            path = self.plotdir / f"{name}.{ext}"
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, dpi=dpi, bbox_inches="tight")

        self.info(f"Saved plot {name} ({'/'.join(formats)}) in {self.plotdir.relative_to(self.path)}")

    def text(self, name: str, content: str):
        """Save plain text to artifacts/{name}.txt.

        Args:
            name: Base filename without extension.
            content: Text content to write.

        Example:
            >>> log.text("stdout", "Simulation complete.")
        """
        path = self.artifactsdir / f"{name}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        self.info(f"Saved text {name} in {path.relative_to(self.path)}")

    def json(self, name: str, data: Dict[str, Any]):
        """Save a JSON file in artifacts/{name}.json.

        Args:
            name: Base filename without extension.
            data: Dictionary to serialize as JSON.

        Example:
            >>> log.json("metrics", {"loss": 0.01})
        """
        path = self.artifactsdir / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        self.info(f"Saved JSON {name} in {path.relative_to(self.path)}")

    def pickle(self, name: str, obj: Any, protocol: int = pickle.HIGHEST_PROTOCOL):
        """Serialize a Python object with pickle to artifacts/{name}.pkl.

        Args:
            name: Base filename without extension.
            obj: Object to serialize.
            protocol: Pickle protocol version to use.

        Example:
            >>> log.pickle("model", model_object)
        """
        path = self.artifactsdir / f"{name}.pkl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(obj, f, protocol=protocol)
        self.info(f"Saved pickle {name} in {path.relative_to(self.path)}")

    def bytes(self, name: str, data: bytes):
        """Save raw bytes to artifacts/{name}.

        Args:
            name: Output filename (with extension).
            data: Byte content to write.

        Example:
            >>> log.bytes("weights.bin", b"\x00\x01")
        """
        path = self.artifactsdir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        self.info(f"Saved bytes {name} in {path.relative_to(self.path)}")

    def __getitem__(self, relative: str) -> Path:
        """Get a path inside the run directory.

        Args:
            relative: Relative path from the run root.

        Returns:
            Path object for that file or directory (not checked for existence).

        Example:
            >>> log["artifacts/config.json"].read_text()
        """
        path = self.path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
