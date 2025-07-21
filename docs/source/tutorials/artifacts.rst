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

Use `save_text()` to write plain `.txt` files:

.. code-block:: python

    log.save_text("notes", "Run converged in 1.3s\nno issues detected")

This saves:

.. code-block:: text

    artifacts/
      notes.txt

JSON
----

Use `save_json()` for structured, human-readable data:

.. code-block:: python

    metrics = {"max": 0.92, "mean": 0.81}
    log.save_json("metrics", metrics)

Saved as:

.. code-block:: text

    artifacts/
      metrics.json

Pickle
------

Use `save_pickle()` for serialized Python objects:

.. code-block:: python

    log.save_pickle("model", my_model)

Saved as:

.. code-block:: text

    artifacts/
      model.pkl

Useful when saving intermediate results, models, or cached data.

Binary Blobs
------------

Use `save_bytes()` to save raw binary content:

.. code-block:: python

    log.save_bytes("weights.raw", b"\x01\x02\x03")

This can be used for custom formats or compressed binaries.

Organizing Artifacts
--------------------

Artifacts can be routed into subfolders using `category=`:

.. code-block:: python

    log.save_json("config", config_dict, category="artifacts/settings")
    log.save_text("crash_dump", traceback_text, category="artifacts/debug")

This will create:

.. code-block:: text

    artifacts/
      settings/
        config.json
      debug/
        crash_dump.txt

File Naming Conventions
-----------------------

- File extension is inferred from the method (`.json`, `.txt`, `.pkl`)
- Use short, descriptive names
- Avoid slashes in names — use `category=` instead

Overwriting
-----------

Each method will **overwrite** the file if it already exists.  
You can implement your own versioning by appending timestamps or unique suffixes to names.

Best Practices
--------------

- Use `save_json()` for any final stats or metrics you want to tabulate
- Use `save_text()` for logs, warnings, command-line args, or notes
- Use `save_pickle()` only when portability isn't a concern
- Keep everything self-contained inside the run directory

Next Steps
----------

- To capture exception info or log structured failures: see :doc:`failures`
- To search and grep outputs: see :doc:`shell_usage`
