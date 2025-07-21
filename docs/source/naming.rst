Naming Conventions
==================

To enable clear organization, scripting, and downstream tooling (e.g. dashboards, shell pipelines), ``notata`` encourages a consistent naming strategy for all saved outputs.

This page defines conventions for naming arrays, artifacts, plots, and run directories.

Run Directory Names
-------------------

Each run lives in:

.. code-block:: text

    log_<run_id>/

Where ``run_id`` should be:

- Concise: e.g., ``lr0.01_bs64`` or ``omega2.0_dt1e-3``
- File-safe: avoid slashes, spaces, or special characters
- Unique: parameterized with key variables if needed

Use underscores (`_`) to separate variable names.

Examples:

- ``omega2.0_dt1e-3``
- ``baseline_v2``
- ``test_fail_case1``

Array Files (`.npz`)
--------------------

Saved to ``data/``

Use:

.. code-block:: text

    <quantity>[ _<step> | _<variant> ].npz

Examples:

- ``trajectory.npz``
- ``T_step500.npz``
- ``field_baseline.npz``

Plots (`.png`, `.pdf`, `.svg`)
------------------------------

Saved to ``plots/``

Use:

.. code-block:: text

    <figure_name>[ _<variant> ].<ext>

Organize by category if needed:

.. code-block:: python

    log.save_plot("loss_curve_train", category="plots/diagnostics")

Examples:

- ``phase_space.png``
- ``loss_curve_train.svg``
- ``summary_overview.pdf``

Artifacts (`.json`, `.txt`, `.pkl`, etc.)
-----------------------------------------

Saved to ``artifacts/`` or nested categories

**Text**

.. code-block:: text

    <topic>[ _<context> ].txt

    notes_run.txt
    crash_trace.txt
    cmd_args.txt

**JSON**

.. code-block:: text

    <topic>[ _<stage> ].json

    metrics_final.json
    results_validation.json

**Pickle**

.. code-block:: text

    <object_type>_<name>.pkl

    model_v1.pkl
    cache_solver.pkl

**Bytes / Binary**

.. code-block:: text

    <type>_<timestamp>.bin

    weights_20250721T1530.bin

Tips and Recommendations
-------------------------

- Use lowercase, no spaces
- Prefer descriptive keys over generic ones (`energy_final` > `out`)
- Avoid redundant extensions (e.g. `result.json.json`)
- Use `category=...` instead of encoding directory structure in names
- For time-stamped names, prefer ISO-style: `2025-07-21T15-30-00`

Automating Naming
-----------------

You can standardize names using a helper:

.. code-block:: python

    def name_for(prefix, tag=None, step=None, ext=None):
        parts = [prefix]
        if tag:
            parts.append(str(tag))
        if step is not None:
            parts.append(f"step{step}")
        return "_".join(parts)

    name_for("E", step=1000)  # → "E_step1000"
