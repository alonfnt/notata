Shell-Based Run Exploration
===========================

One of ``notata``’s design goals is to make runs **inspectable using standard shell tools**.  
Since all logs, parameters, and metadata are plain text or JSON, you can search, filter, and analyze results without writing custom scripts.

Inspecting Run Directories
--------------------------

List all runs:

.. code-block:: bash

    ls outputs/log_*

Check size of each run:

.. code-block:: bash

    du -sh outputs/log_*

Find oldest or largest runs:

.. code-block:: bash

    ls -lt outputs/log_*        # by modification time
    du -shc outputs/log_* | sort -h  # by size

Finding Completed or Failed Runs
--------------------------------

**List all completed runs:**

.. code-block:: bash

    grep -l '"status": "complete"' outputs/log_*/metadata.json

**List all failed runs:**

.. code-block:: bash

    grep -l '"status": "failed"' outputs/log_*/metadata.json

Extracting Parameters
---------------------

If using YAML for parameter storage:

.. code-block:: bash

    grep 'dt:' outputs/log_*/params.yaml

If using JSON:

.. code-block:: bash

    jq '.dt' outputs/log_*/params.json

Extract multiple keys:

.. code-block:: bash

    jq '{dt: .dt, omega: .omega}' outputs/log_*/params.json

Filtering Based on Output Metrics
---------------------------------

Assuming each run saved a final metric like this:

.. code-block:: json

    {
      "x": 1.5,
      "v": 0.9,
      "E": 2.1345
    }

You can filter all runs with ``E > 2.0``:

.. code-block:: bash

    jq 'select(.E > 2.0)' outputs/log_*/artifacts/final_state.json

Or print run names and energy:

.. code-block:: bash

    for path in outputs/log_*; do
      val=$(jq '.E' "$path/artifacts/final_state.json" 2>/dev/null)
      echo "$path: $val"
    done

Searching Logs
--------------

Check for warnings or specific events in logs:

.. code-block:: bash

    grep -i 'warning' outputs/log_*/log.txt

    grep 'step=1000' outputs/log_*/log.txt

Scripting Across Runs
---------------------

You can combine with ``xargs`` or ``find`` to batch-process outputs:

**Re-run failed runs only:**

.. code-block:: bash

    for run in $(grep -l '"status": "failed"' outputs/log_*/metadata.json); do
      echo "Would re-run: $(dirname $run)"
    done

**Tabulate results into CSV:**

.. code-block:: bash

    echo "run_id,E" > results.csv
    for d in outputs/log_*; do
      id=$(basename $d | cut -c5-)
      E=$(jq '.E' "$d/artifacts/final_state.json" 2>/dev/null)
      echo "$id,$E" >> results.csv
    done

This makes downstream analysis with ``pandas``, ``gnuplot``, or ``R`` seamless.

Tips
----

- Always include meaningful names in artifacts (e.g. ``metrics.json``, not ``data.json``)
- Avoid spaces or special characters in ``run_id``s
- Use ``category=`` to avoid cluttering the root artifact directory

Next Steps
----------

- For naming patterns that support scripting: see :doc:`naming`
- For sweep setup and failure recovery: see :doc:`sweeps`