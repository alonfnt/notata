Quickstart
==========

The ``Logbook`` is the core of ``notata``. It represents a single run of a simulation or experiment. When you create a ``Logbook``, it sets up a dedicated run directory, initializes metadata, and lets you persist all relevant outputs in a structured format.

To manage multiple related runs, you can use the ``Experiment`` object, which helps automate naming, logging, and indexing across parameter sweeps.

Basic Usage: Context Manager
----------------------------

The most convenient way to use a ``Logbook`` is with a context manager. This ensures that the run is either marked **complete** or **failed**, depending on the outcome.

.. code-block:: python

    from notata import Logbook
    import numpy as np

    omega = 2.0
    dt = 1e-3
    steps = 5000

    with Logbook("oscillator_dt1e-3", params={"omega": omega, "dt": dt, "steps": steps}) as log:
        x, v = 1.0, 0.0
        xs = []
        for n in range(steps):
            a = -omega**2 * x
            x += v * dt + 0.5 * a * dt**2
            a_new = -omega**2 * x
            v += 0.5 * (a + a_new) * dt
            xs.append(x)

        log.array("x_values", np.array(xs))
        log.json("final_state", {"x": float(x), "v": float(v)})

Sweep Runs with Experiment
--------------------------

To log many runs with different parameters:

.. code-block:: python

    from notata import Experiment

    exp = Experiment("oscillator_sweep")

    for omega in [1.0, 2.0]:
        for dt in [1e-3, 2e-3]:
            log = exp.add(omega=omega, dt=dt, steps=5000)
            with log:
                # simulate system with current parameters
                # as with a normal logbook
                ...

                # Save metrics or results to be indexed too
                log.json("metrics", {"final_energy": 0.991})

To see how to use `Experiment` in more detail, see: :doc:`experiment`

What gets saved
---------------

After this run, your output directory will contain:

.. code-block:: text

    log_oscillator_dt1e-3/
      log.txt
      metadata.json
      params.yaml
      data/
        x_values.npy
      artifacts/
        final_state.json

To see how to organize large outputs, see: :doc:`artifacts` and :doc:`../structure`.

Logging
-------

Inside the loop, you can use:

.. code-block:: python

    log.info("any message")
    log.debug(...)
    log.warning(...)
    log.error(...)

These will go into ``log.txt`` with timestamps and log levels.

You can read more on how to inspect logs in :doc:`shell_usage`.

Parameters
----------

Parameters passed via ``params=...`` are saved immediately to ``params.yaml``.

You can also write them later:

.. code-block:: python

    log.params(omega=2.0, dt=1e-3)

To inspect saved parameters:

.. code-block:: python

    print(log.params["omega"])

Using Readers
-------------

Once your runs are logged, you can use ``LogReader`` and ``ExperimentReader`` to access the data.

Example: Accessing a single run

.. code-block:: python

    from notata.reader import LogReader

    reader = LogReader("outputs/log_oscillator_dt1e-3")
    print("Run ID:", reader.run_id)
    print("Metadata:", reader.meta)
    print("Parameters:", reader.params)
    energy = reader.load_array("x_values")
    print("Energy array:", energy)

Example: Accessing multiple runs

.. code-block:: python

    from notata.reader import ExperimentReader

    exp = ExperimentReader("outputs/oscillator_sweep")
    for run in exp:
        print("Run ID:", run.run_id)
        print("Metadata:", run.meta)
        print("Parameters:", run.params)

Readers make it easy to query and analyze your logged data programmatically.
For more information you can check :doc:`readers`.

Next Steps
----------

- To see how to handle failures or manual control, see: :doc:`manual`
- For saving plots, see: :doc:`plotting`
- For organizing large outputs, see: :doc:`artifacts`
