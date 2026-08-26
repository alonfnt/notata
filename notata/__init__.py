"""Structured filesystem logging for scientific runs.

Each run is written to its own directory of plain files. No server, no
database, no hidden state::

    log_<run_id>/
        log.txt            timestamped messages
        metadata.json      status, start/end time, runtime_sec
        params.yaml        parameter snapshot
        data/              .npy (one array) and .npz (bundles)
        plots/             saved matplotlib figures
        artifacts/         .json, .txt, .pkl and raw bytes

Log a single run. The context manager marks it ``complete`` on exit, or
``failed`` with the exception message if one propagates::

    from notata import Logbook

    with Logbook("oscillator", params={"omega": 2.0, "dt": 1e-3}) as log:
        log.info("integrating")
        log.array("energy", E)              # data/energy.npy
        log.arrays("trajectory", x=x, v=v)  # data/trajectory.npz
        log.json("metrics", {"drift": 1e-9})
        log.plot("energy")                  # plots/energy.png

Sweep parameters with `Experiment`. Each run gets its own directory and a
row in ``index.csv`` holding its parameters, status and metrics::

    from notata import Experiment

    exp = Experiment("convergence")
    for dt in (1e-2, 1e-3, 1e-4):
        with exp.add(dt=dt) as log:
            log.json("metrics", {"error": solve(dt)})

    exp.to_dataframe()          # pandas view of index.csv

Read runs back without handling paths yourself::

    from notata import ExperimentReader, LogReader

    for run in ExperimentReader("outputs/convergence"):
        print(run.run_id, run.params, run.meta["status"])
        energy = run.load_array("energy")
        x = run.load_array("trajectory:x")   # key inside an .npz bundle

    LogReader("outputs/log_oscillator").load_json("metrics")

Everything is a plain file, so the usual tools still work::

    grep -r "Marked failed" outputs/
    cat outputs/log_oscillator/params.yaml

Documentation: https://notata.readthedocs.io
"""

from notata.logbook import Logbook
from notata.experiment import Experiment
from notata.reader import LogReader, ExperimentReader

__version__ = "0.3.0"

__all__ = [
    "Logbook",
    "Experiment",
    "LogReader",
    "ExperimentReader",
    "__version__",
      ]
