Saving Artifacts
================

Artifacts are arbitrary files produced during a run: structured outputs, diagnostics, serialized models, logs, or raw data blobs.  
``notata`` provides methods to save these in a consistent, organized way.

By default, all artifacts are saved under:

.. code-block:: text

    log_<run_id>/
      artifacts/

Text Files
----------

Use `text()` to write plain `.txt` files:

.. code-block:: python

    log.text("notes", "Run converged in 1.3s\nno issues detected")

This saves:

.. code-block:: text

    artifacts/
      notes.txt

JSON
----

Use `json()` for structured, human-readable data:

.. code-block:: python

    metrics = {"max": 0.92, "mean": 0.81}
    log.json("metrics", metrics)

Saved as:

.. code-block:: text

    artifacts/
      metrics.json

Pickle
------

Use `pickle()` to serialize Python objects:

.. code-block:: python

    log.pickle("model", my_model)

Saved as:

.. code-block:: text

    artifacts/
      model.pkl

Useful for saving intermediate results, models, or cached data.

Binary Blobs
------------

Use `bytes()` to write raw binary content:

.. code-block:: python

    log.bytes("weights.raw", b"\x01\x02\x03")

This can be used for custom formats or compressed binaries.

Organizing Artifacts
--------------------

To save files in nested folders, use the indexing interface:

.. code-block:: python

    log["artifacts/settings/config.json"].write_text(json.dumps(config_dict))
    log["artifacts/debug/crash_dump.txt"].write_text(traceback_text)

This will create:

.. code-block:: text

    artifacts/
      settings/
        config.json
      debug/
        crash_dump.txt

File Naming Conventions
-----------------------

- File extension is determined by the method (`.json`, `.txt`, `.pkl`) or by your key when using `log[...]`
- Use lowercase, descriptive names
- Avoid redundant extensions (e.g. `config.json.json`)
- Prefer ISO-style timestamps if versioning (e.g. `weights_2025-07-25T12-00-00.pkl`)

Overwriting
-----------

Each method **overwrites** the target file if it already exists.
To implement versioning, append suffixes or timestamps manually.

Best Practices
--------------

- Use `json()` for any final stats or metrics
- Use `text()` for logs, warnings, or notes
- Use `pickle()` only when portability isn't a concern
- Use `bytes()` for compressed or binary formats
- Keep everything self-contained inside the run directory
- Use `log[...]` when you need full control over paths and filenames

Next Steps
----------

- To capture exception info or log structured failures: see :doc:`failures`
- To search and grep outputs: see :doc:`shell_usage`
