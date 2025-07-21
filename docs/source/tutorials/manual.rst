Manual Lifecycle Control
========================

While the context manager is the preferred interface, ``Logbook`` can also be used manually.  
This is useful in scripts or programs where setup and teardown are more complex, or you want to control exactly when a run is marked complete or failed.

Basic Pattern
-------------

.. code-block:: python

    from notata import Logbook
    import numpy as np

    log = Logbook("manual_heat_run", params={"Nx": 64, "Ny": 64, "kappa": 0.01})

    try:
        Nx = Ny = 64
        T = np.ones((Nx, Ny))
        for step in range(500):
            # update T ...
            if (step + 1) % 100 == 0:
                log.info(f"step={step+1}")
        log.save_numpy("T_final", T)
        log.mark_complete()

    except Exception as e:
        log.mark_failed(str(e))

mark_complete
-------------

.. code-block:: python

    log.mark_complete()

Explicitly finalizes the run. Updates `metadata.json` with:

- ``status: complete``
- ``end_time``
- ``runtime_sec``

mark_failed
-----------

.. code-block:: python

    log.mark_failed("NaN detected in simulation")

Sets the run status to ``failed`` and records the reason. Use this when:

- You catch an exception but still want to finalize the run cleanly
- You detect invalid or unstable results manually
- You want to explicitly tag a run as invalid post-hoc

Checking status
---------------

.. code-block:: python

    log.current_status()

Returns one of:

- ``initialized``
- ``complete``
- ``failed``

This can be used in long workflows to checkpoint progress or resume logic.

Typical Use Case
----------------

This mode is common when:

- Using ``notata`` in larger scripts or frameworks
- Integrating with Jupyter notebooks where context managers are awkward
- Wanting to defer marking complete until validations are finished

Next Steps
----------

- To save diagnostics and outputs: see :doc:`artifacts`
- To handle plots and figures: see :doc:`plotting`
