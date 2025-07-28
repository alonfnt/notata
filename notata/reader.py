import json
import csv
from pathlib import Path
from typing import Any, Dict, Union, Iterator, List


class LogReader:
    """
    Provides access to data and metadata from a single Logbook run directory.

    This class allows users to retrieve parameters, metadata, arrays, artifacts,
    and plots associated with a specific run.

    Example:
        >>> reader = LogReader("outputs/log_my_run")
        >>> print(reader.params)

    Args:
        path: Path to the Logbook run directory.
    """

    def __init__(self, path: Union[str, Path]):
        """
        Initialize a LogReader instance.

        Args:
            path (Union[str, Path]): Path to the Logbook run directory.

        Raises:
            FileNotFoundError: If the specified path does not exist.
            ValueError: If the directory does not contain a valid Logbook run.
        """
        self.path = Path(path) if isinstance(path, str) else path
        if not self.path.exists():
            raise FileNotFoundError(f"No such path: {self.path}")
        if not (self.path / "metadata.json").exists():
            raise ValueError(f"{self.path} is not a valid Logbook run")

    @property
    def run_id(self) -> str:
        """
        Get the unique identifier for the run.

        Returns:
            str: The run ID, derived from the directory name.
        """
        return self.path.name.replace("log_", "")

    @property
    def meta(self) -> Dict[str, Any]:
        """
        Load the metadata of the run.

        Returns:
            Dict[str, Any]: Metadata loaded from `metadata.json`.
        """
        return self._read_json("metadata.json")

    @property
    def params(self) -> Dict[str, Any]:
        """
        Load the parameters of the run.

        Returns:
            Dict[str, Any]: Parameters loaded from `params.yaml` or `params.json`.
        """
        yml = self.path / "params.yaml"
        jsn = self.path / "params.json"
        if yml.exists():
            import yaml
            return yaml.safe_load(yml.read_text()) or {}
        if jsn.exists():
            return json.loads(jsn.read_text())
        return {}

    @property
    def arrays(self) -> List[str]:
        keys = []
        data_path = self.path / "data"
        if not data_path.exists():
            return keys

        for file in data_path.rglob("*.npy"):
            keys.append(file.stem)

        for file in data_path.rglob("*.npz"):
            import numpy as np
            try:
                with np.load(file) as bundle:
                    for key in bundle.files:
                        keys.append(f"{file.stem}:{key}")
            except Exception:
                continue

        return sorted(keys)

    @property
    def artifacts(self) -> List[str]:
        artifacts_path = self.path / "artifacts"
        if not artifacts_path.exists():
            return []
        return sorted(f.stem for f in artifacts_path.glob("*.json"))

    @property
    def plots(self) -> List[str]:
        plots_path = self.path / "plots"
        if not plots_path.exists():
            return []
        return sorted(f.name for f in plots_path.iterdir() if f.is_file())

    def load_array(self, name: str):
        """
        Load an array by name.

        Supports:
            - 'foo' -> loads data/foo.npy
            - 'bundle:key' -> loads key from data/bundle.npz

        Raises:
            FileNotFoundError, KeyError if missing.
        """
        import numpy as np

        if ":" in name:
            bundle, key = name.split(":", 1)
            path = self.path / "data" / f"{bundle}.npz"
            if not path.exists():
                raise FileNotFoundError(f"No such bundle: {bundle}.npz")
            with np.load(path) as data:
                if key not in data:
                    raise KeyError(f"No key '{key}' in bundle '{bundle}.npz'")
                return data[key]
        else:
            path = self.path / "data" / f"{name}.npy"
            if not path.exists():
                raise FileNotFoundError(f"No such array: {name}.npy")
            return np.load(path)

    def load_json(self, name: str) -> Dict[str, Any]:
        return self._read_json(f"artifacts/{name}.json")

    def _read_json(self, relpath: str) -> Dict[str, Any]:
        full = self.path / relpath
        if not full.exists():
            return {}
        return json.loads(full.read_text())

    def __str__(self) -> str:
        lines = [f"<LogReader '{self.run_id}'>"]

        if self.params:
            param_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
            lines.append(f"  params: {param_str}")
        else:
            lines.append("  params: (missing)")

        lines.append(f"  meta: status={self.meta.get('status', 'unknown')}")

        def block(label: str, items: list[str]):
            if items:
                lines.append(f"  {label}:")
                lines.extend(f"    - {i}" for i in items)

        block("arrays", self.arrays)
        block("artifacts", self.artifacts)
        block("plots", self.plots)

        return "\n".join(lines)


class ExperimentReader:
    """
    Facilitates access to multiple Logbook runs within an experiment directory.

    This class enables iteration over runs, retrieval of parameters and metadata,
    and querying the experiment index.

    Example:
        >>> exp = ExperimentReader("outputs/my_experiment")
        >>> for run in exp:
        >>>     print(run.meta)

    Args:
        path: Path to the experiment directory.
        base_dir: Base directory for experiments, defaults to "outputs".
    """

    def __init__(self, path: Union[str, Path]):
        """
        Initialize an ExperimentReader instance.

        Args:
            path (Union[str, Path]): Path to the experiment directory.

        Raises:
            FileNotFoundError: If the specified path does not exist.
        """
        self.path = Path(path) if isinstance(path, str) else path
        self.index_path = self.path / "index.csv"
        self.runs_path = self.path / "runs"
        if not self.path.exists():
            raise FileNotFoundError(f"No such path: {self.path}")

        self.runs = sorted([d for d in self.runs_path.iterdir()
                            if d.is_dir() and (d / "metadata.json").exists()])

    def __iter__(self) -> Iterator[LogReader]:
        """
        Iterate over all runs in the experiment.

        Yields:
            LogReader: A `LogReader` instance for each run.
        """
        for run_dir in self.runs:
            yield LogReader(run_dir)

    def __len__(self) -> int:
        """
        Get the number of runs in the experiment.

        Returns:
            int: The number of runs.
        """
        return len(self.runs)

    def __getitem__(self, run_id: Union[str, int]) -> LogReader:
        """
        Retrieve a single run by its ID or index.

        Args:
            run_id (Union[str, int]): The run ID (without the `log_` prefix) or index.

        Returns:
            LogReader: A `LogReader` instance for the specified run.

        Raises:
            IndexError: If the index is out of range.
            KeyError: If no run is found with the specified ID.
            TypeError: If the run ID is not a string or integer.
        """
        if isinstance(run_id, int):
            if run_id < 0 or run_id >= len(self.runs):
                raise IndexError(f"Run index {run_id} out of range")
            return LogReader(self.runs[run_id])
        elif isinstance(run_id, str):
            for run in self:
                if run.run_id == run_id:
                    return run
            raise KeyError(f"No run found with ID '{run_id}'")
        else:
            raise TypeError("Run ID must be an integer or string")

    def index(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate over rows in the `index.csv` file.

        Yields:
            Dict[str, Any]: A dictionary representing a row in the index file.
        """
        if not self.index_path.exists():
            return
        with self.index_path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

    @property
    def params(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the parameters of all the runs in this experiment.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary mapping run IDs to their parameters.
        """
        return {run.run_id: run.params for run in self}

    @property
    def meta(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the metadata of all the runs in this experiment.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary mapping run IDs to their metadata.
        """
        return {run.run_id: run.meta for run in self}

    def __str__(self) -> str:
        lines = [f"<ExperimentReader '{self.path.name}'>"]
        lines.append(f"Index file: {self.index_path.name} with {len(self)} entries")
        if self.index_path.exists():
            with self.index_path.open() as f:
                reader = csv.reader(f)
                fields = next(reader, [])
                lines.append(f"Fields: {', '.join(fields)}")
        else:
            lines.append("Fields: (missing)")
        lines.append(f"Runs directory: {self.runs_path.name} with {len(self)} runs")
        for run in self:
            status = run.meta.get("status", "unknown")
            lines.append(f"- {run.run_id}: {status}")
        return "\n".join(lines)