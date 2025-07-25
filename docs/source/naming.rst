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

Array Files (`.npy` or `.npz`)
------------------------------

Saved to ``data/``

Use:

.. code-block:: text

    <quantity>[ _<step> | _<variant> ].npy
    <bundle_name>.npz  (for multiple arrays)

Examples:

- ``trajectory.npy``
- ``T_step500.npy``
- ``field_baseline.npz``

Saved using:

.. code-block:: python

    log.array("vec", np.arange(100))
    log.arrays("batch", a=..., b=...)

Plots (`.png`, `.pdf`, `.svg`)
------------------------------

Saved to ``plots/``

Use:

.. code-block:: text

    <figure_name>[ _<variant> ].<ext>

Examples:

- ``phase_space.png``
- ``loss_curve_train.svg``
- ``summary_overview.pdf``

Saved using:

.. code-block:: python

    log.plot("loss_curve_train", fig=fig, formats=("png", "pdf"))

Artifacts (`.json`, `.txt`, `.pkl`, etc.)
-----------------------------------------

Saved to ``artifacts/``

**Text**

.. code-block:: text

    <topic>[ _<context> ].txt

Examples:

- ``notes_run.txt``
- ``crash_trace.txt``
- ``cmd_args.txt``

Saved using:

.. code-block:: python

    log.text("cmd_args", "python script.py")

**JSON**

.. code-block:: text

    <topic>[ _<stage> ].json

Examples:

- ``metrics_final.json``
- ``results_validation.json``

Saved using:

.. code-block:: python

    log.json("metrics_final", {"acc": 0.94})

**Pickle**

.. code-block:: text

    <object_type>_<name>.pkl

Examples:

- ``model_v1.pkl``
- ``cache_solver.pkl``

Saved using:

.. code-block:: python

    log.pickle("model_v1", model)

**Bytes / Binary**

.. code-block:: text

    <type>_<timestamp>.bin

Examples:

- ``weights_20250721T1530.bin``

Saved using:

.. code-block:: python

    log.bytes("weights_20250721T1530.bin", b"\x00\x01")

Manual Path Customization
-------------------------

If you want full control over where to place an artifact (e.g. a nested folder), use the bracket accessor:

.. code-block:: python

    log["artifacts/eval/metrics.json"].write_text("...")

This guarantees parent directory creation and is the preferred replacement for the deprecated `category=...` argument.

Tips and Recommendations
-------------------------

- Use lowercase, no spaces
- Prefer descriptive keys over generic ones (`energy_final` > `out`)
- Avoid redundant extensions (e.g. `result.json.json`)
- Use `log["relative/path"]` for manual control of directory layout
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
