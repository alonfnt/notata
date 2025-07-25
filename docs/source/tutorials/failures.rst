Handling Failures
=================

``notata`` makes it easy to track failed runs explicitly — including crash reasons, partial outputs, and logs.  
This ensures reproducibility even when a run doesn't complete successfully.

Automatic Failure Detection
---------------------------

When using a context manager:

.. code-block:: python

    with Logbook("unstable") as log:
        raise RuntimeError("Something broke")

The run will automatically be marked as ``failed`` in `metadata.json` if any exception is raised.  
No need to call `mark_failed()` manually.

Manual Failure Capture
----------------------

If you're not using a context manager — or want to catch and report failures explicitly — use:

.. code-block:: python

    try:
        log = Logbook("run_may_fail")
        simulate()
        log.mark_complete()
    except Exception as e:
        log.mark_failed(str(e))

This records the failure reason and prevents partial runs from being marked as complete.

Failure Metadata
----------------

When a run fails, `metadata.json` includes:

.. code-block:: json

    {
      "status": "failed",
      "start_time": "...",
      "end_time": "...",
      "runtime_sec": ...,
      "failure_reason": "Something broke",
      "run_id": "unstable"
    }

This allows you to grep or filter failed runs easily.

Capturing Tracebacks
--------------------

You can log a full traceback for postmortem analysis:

.. code-block:: python

    import traceback

    try:
        ...
    except Exception as e:
        tb = traceback.format_exc()
        log.text("artifacts/debug/traceback", tb)
        log.mark_failed(str(e))

This saves:

.. code-block:: text

    artifacts/debug/traceback.txt

Searching for Failed Runs
-------------------------

Use standard tools to identify failed runs:

.. code-block:: bash

    grep -l '"status": "failed"' outputs/log_*/metadata.json

Or extract failure reasons:

.. code-block:: bash

    jq '.failure_reason' outputs/log_*/metadata.json

Use Cases
---------

- Simulation crashes
- Numerical instability (e.g., `nan`, `inf`)
- Invalid inputs or out-of-bounds parameters
- Runtime exceptions from third-party libraries

Best Practices
--------------

- Always call `mark_failed()` when catching exceptions manually
- Include a meaningful reason message
- Save a traceback or diagnostic artifact if debugging is needed
- Never `mark_complete()` if results are invalid

Next Steps
----------

- For saving diagnostics and tracebacks: see :doc:`artifacts`
- For programmatically resuming failed runs: see :doc:`sweeps`
