Experiment Management
===========================================

The ``Experiment`` object in ``notata`` is designed to organize and track multiple related runs using ``Logbook``. It simplifies the process of sweeping parameters, aggregating metrics, and building an index of all results.

Quickstart
----------

.. code-block:: python

    from notata import Experiment

    exp = Experiment("oscillator_sweep")

    for omega in [1.0, 2.0]:
        for dt in [1e-3, 2e-3]:
            log = exp.add(omega=omega, dt=dt, steps=10_000, skip_existing=True)

            if log is None:
                continue  # skip if this run already exists

            with log:
                # Your simulation code here
                ...
                log.json("metrics", {"final_energy": 0.993})
            # Exiting the context manager automatically marks the run as complete.

Manual Logging (without context manager)
----------------------------------------

You can also explicitly call ``mark_complete()`` after your run logic:

.. code-block:: python

    log = exp.add(omega=3.0, dt=1e-3, steps=5000)

    try:
        # run your simulation
        ...
        log.json("metrics", {"final_energy": 0.998})
        log.mark_complete()  # explicitly mark success
    except Exception as e:
        log.mark_failed(str(e))

What it does
------------

The ``Experiment`` handles:

- Constructing unique log directories per parameter set.
- Attaching a callback so that calling ``log.mark_complete()`` or ``log.mark_failed()`` auto-updates an ``index.csv``.
- Persisting parameters and user-defined metrics for each run.

Directory Layout
----------------

.. code-block:: text

    outputs/oscillator_sweep/
      index.csv
      runs/
        log_oscillator_sweep_dt_0.001_omega_1.0/
        log_oscillator_sweep_dt_0.002_omega_1.0/
        log_oscillator_sweep_dt_0.001_omega_2.0/
        log_oscillator_sweep_dt_0.002_omega_2.0/

Each run gets its own ``Logbook`` with full logging, metadata, and artifacts.

Inspecting Results
------------------

You can convert the index to a pandas dataframe and filter completed runs:

.. code-block:: python

    df = exp.to_dataframe()
    complete = df[df["status"] == "complete"]
    print(complete[["omega", "dt", "final_energy"]])

Example **index** after running one log:

.. list-table::
   :header-rows: 1

   * - run_id
     - omega
     - dt
     - steps
     - status
     - final_energy
   * - oscillator_sweep_dt_0.001_omega_1.0
     - 1.0
     - 0.001
     - 10000
     - complete
     - 0.993

Convenience
-----------

The key benefit of ``Experiment`` is that it removes the need for manual bookkeeping across many runs. Just:

- Use ``exp.add(...)`` instead of manually constructing directories.
- Store metrics in ``artifacts/metrics.json``.
- Use ``log.mark_complete()`` or ``with log: ...``.

The index is built incrementally and is ready for downstream analysis or re-running filtered subsets.
