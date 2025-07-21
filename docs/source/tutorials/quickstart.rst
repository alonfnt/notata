Quickstart
==========

The ``Logbook`` is the core of ``notata``. It represents a single run of a simulation or experiment. When you create a ``Logbook``, it sets up a dedicated run directory, initializes metadata, and lets you persist all relevant outputs in a structured format.

Basic Usage: Context Manager
----------------------------

The most convenient way to use a ``Logbook`` is with a context manager. This ensures that the run is either marked **complete** or **failed**, depending on the outcome.

.. code-block:: python

    from notata import Logbook
    import numpy as np

    with Logbook("oscillator_dt1e-3", params={"omega": 2.0, "dt": 1e-3, "steps": 10_000}) as log:
        omega = 2.0
        dt = 1e-3
        steps = 10_000
        x, v = 1.0, 0.0

        xs = np.empty(steps)
        vs = np.empty(steps)
        E  = np.empty(steps)

        for n in range(steps):
            a = -omega**2 * x
            x += v*dt + 0.5*a*dt*dt
            a_new = -omega**2 * x
            v += 0.5*(a + a_new)*dt
            xs[n], vs[n] = x, v
            E[n] = 0.5*(v**2 + (omega*x)**2)
            if (n+1) % 2000 == 0:
                log.info(f"step={n+1} x={x:.4f} v={v:.4f} E={E[n]:.6f}")

        log.save_arrays("trajectory", x=xs, v=vs)
        log.save_numpy("energy", E)
        log.save_json("final_state", {"x": float(x), "v": float(v), "E": float(E[-1])})

What gets saved
---------------

After this run, your output directory will contain:

.. code-block:: text

    log_oscillator_dt1e-3/
      log.txt
      metadata.json
      params.yaml
      data/
        trajectory.npz
        energy.npz
      artifacts/
        final_state.json

Logging
-------

Inside the loop, you can use:

.. code-block:: python

    log.info("any message")
    log.debug(...)
    log.warning(...)
    log.error(...)

These will go into ``log.txt`` with timestamps and log levels.

Parameters
----------

Parameters passed via ``params=...`` are saved immediately to ``params.yaml`` (or ``params.json``).

You can also save them later:

.. code-block:: python

    log.save_params({"dt": 1e-3, "omega": 2.0}, preferred="yaml")

Next Steps
----------

- To see how to handle failures or manual control, see: :doc:`manual`
- For saving plots, see: :doc:`plotting`
- For organizing large outputs, see: :doc:`artifacts`

