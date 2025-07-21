Parameter Sweeps
================

``notata`` is well-suited for automated parameter sweeps, such as varying hyperparameters, initial conditions, or simulation settings.  
Each run is isolated in its own directory, with its own log, outputs, and metadata.

Basic Sweep Loop
----------------

Here’s how to structure a sweep over multiple parameter combinations:

.. code-block:: python

    from notata import Logbook
    import numpy as np
    import itertools

    omegas = [1.0, 2.0, 3.0]
    dts = [1e-2, 1e-3]

    for omega, dt in itertools.product(omegas, dts):
        run_id = f"omega{omega}_dt{dt}"
        params = {"omega": omega, "dt": dt, "steps": 1000}

        with Logbook(run_id, params=params) as log:
            x, v = 1.0, 0.0
            xs = np.empty(params["steps"])

            for n in range(params["steps"]):
                a = -omega**2 * x
                x += v*dt + 0.5*a*dt*dt
                a_new = -omega**2 * x
                v += 0.5*(a + a_new)*dt
                xs[n] = x

            log.save_numpy("x", xs)
            log.save_json("final_state", {"x": float(x), "v": float(v)})

Organizing Sweep Outputs
------------------------

Each run creates a directory like:

.. code-block:: text

    outputs/
      log_omega1.0_dt0.01/
      log_omega1.0_dt0.001/
      log_omega2.0_dt0.01/
      ...

You can then grep, tabulate, or plot sweep results directly from the filesystem.

Saving Results in Structured Form
---------------------------------

To compare sweep results later, save a final summary metric for each run:

.. code-block:: python

    energy = 0.5 * (v**2 + (omega * x)**2)
    log.save_json("final_metrics", {"E": float(energy)})

Then collect across runs:

.. code-block:: bash

    jq '.E' outputs/log_*/artifacts/final_metrics.json

Tips for Large Sweeps
---------------------

- Use compact, informative `run_id`s (avoid slashes or long floats)
- Use `category=...` to group intermediate outputs or diagnostics
- Set `overwrite=True` if re-running a sweep with the same IDs
- Track failures with `current_status()` or grep on metadata

Example: Resuming only failed runs
----------------------------------

.. code-block:: python

    import json
    from pathlib import Path

    for path in Path("outputs").glob("log_*"):
        meta = path / "metadata.json"
        if not meta.exists():
            continue
        status = json.loads(meta.read_text()).get("status")
        if status != "complete":
            print(f"Will re-run: {path.name}")
