Filesystem Structure
====================

``notata`` defines a consistent, human-readable directory layout for each run. This enables reproducibility, introspection, and long-term reuse without custom tooling.

Each run is stored in a uniquely named directory:

.. code-block:: bash

    log_<run_id>/

Contents
--------

Below is a breakdown of the expected structure and the purpose of each file or folder.

.. code-block:: bash

    log_<run_id>/
      log.txt
      metadata.json
      params.yaml  (or params.json)
      data/
      plots/
      artifacts/

Description of Each Element
---------------------------

- **log.txt**  
  A plain text chronological log file. Each line follows:
  
  .. code-block:: text

      [YYYY-MM-DDTHH:MM:SS] LEVEL message

- **metadata.json**  
  JSON file with lifecycle metadata. Fields include:

  - ``run_id``: user-supplied identifier
  - ``status``: one of ``initialized``, ``complete``, ``failed``
  - ``start_time``, ``end_time``: ISO timestamps
  - ``runtime_sec``: total wall time
  - ``failure_reason``: optional, present if run failed

- **params.yaml** / **params.json**  
  Parameters used for the run, written as a single top-level dictionary.

- **data/**  
  NumPy array outputs.

  - Single array: saved as `.npy` via `log.array(...)`
  - Multiple arrays: saved as `.npz` via `log.arrays(...)`

- **plots/**  
  Saved matplotlib figures. Extensions may include ``.png``, ``.pdf``, or ``.svg``.

  Saved using `log.plot(...)`.

- **artifacts/**  
  Arbitrary outputs such as:

  - ``.json``: structured output via `log.json(...)`
  - ``.txt``: logs, notes, diagnostics via `log.text(...)`
  - ``.pkl``: serialized objects via `log.pickle(...)`
  - Other formats like ``.bin`` via `log.bytes(...)`

Custom Structure via Manual Paths
---------------------------------

To organize outputs into custom subfolders, use the indexing interface:

.. code-block:: python

    log["data/intermediate/u_step100.npy"].write_bytes(...)
    log["artifacts/eval/metrics.json"].write_text(json.dumps(metrics))
    log["plots/debug/loss_curve.pdf"]  # to store a figure manually

This ensures that parent directories are created as needed.

Conventions
-----------

- All paths are **relative to the run directory**
- All save methods create parent directories if needed
- All logs and metadata are written in **plain text or JSON** formats

This structure is intentionally flat, discoverable, and designed to support both manual inspection and programmatic tooling.

Searching and Inspecting Runs
=============================

Because ``notata`` stores everything as plain text and structured files in the filesystem, you can inspect results using standard shell tools — no special API or viewer required.

Grep and Search Examples
------------------------

**Find all completed runs:**

.. code-block:: bash

    grep -l '"status": "complete"' outputs/log_*/metadata.json

**List all runs with a specific parameter:**

.. code-block:: bash

    grep -l 'omega: 2.0' outputs/log_*/params.yaml

**Extract a specific metric from all runs:**

If you save final metrics to a JSON artifact:

.. code-block:: bash

    jq '.E' outputs/log_*/artifacts/final_state.json

**Find all runs that failed:**

.. code-block:: bash

    grep -l '"status": "failed"' outputs/log_*/metadata.json

**Find runs with energy above threshold:**

.. code-block:: bash

    jq 'select(.E > 1.0)' outputs/log_*/artifacts/final_state.json

Structured Exploration
----------------------

You can also use tools like:

- ``find`` to filter files by path or type
- ``jq`` to slice structured JSON content
- ``awk``, ``cut``, or ``grep -r`` to scan logs for patterns
- ``du -sh log_*`` to check size of each run

This design is intentional: it makes your experiments **composable with Unix**.

Rationale
---------

Unlike most ML tracking systems that store metrics in databases or hide them behind dashboards, ``notata`` emphasizes:

- **Unix-first reproducibility**
- **Transparency over abstraction**
- **Permanent, discoverable logs**

If it’s in a file, it’s searchable. If it’s structured, it’s scriptable.