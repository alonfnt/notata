Readers: Accessing Run Data
===========================

``notata`` provides two main classes for accessing run data:

- ``LogReader``: For accessing data and metadata from a single run directory.
- ``ExperimentReader``: For accessing multiple runs within an experiment directory.

LogReader
---------

``LogReader`` allows you to access parameters, metadata, arrays, artifacts, and plots from a single run.

Example:

.. code-block:: python

    from notata.reader import LogReader

    reader = LogReader("outputs/log_my_run")
    print("Run ID:", reader.run_id)
    print("Metadata:", reader.meta)
    print("Parameters:", reader.params)
    print("Available arrays:", reader.arrays)

To load an array:

.. code-block:: python

    energy = reader.load_array("energy")
    print("Energy array:", energy)

To load a JSON artifact:

.. code-block:: python

    metrics = reader.load_json("metrics")
    print("Metrics:", metrics)

ExperimentReader
----------------

``ExperimentReader`` allows you to iterate over multiple runs in an experiment directory.

Example:

.. code-block:: python

    from notata.reader import ExperimentReader

    exp = ExperimentReader("outputs/my_experiment")
    print("Number of runs:", len(exp))

    for run in exp:
        print("Run ID:", run.run_id)
        print("Metadata:", run.meta)

To access a specific run:

.. code-block:: python

    run = exp["1"]
    print("Run ID:", run.run_id)
    print("Parameters:", run.params)

To access parameters and metadata for all runs:

.. code-block:: python

    print("Parameters:", exp.params)
    print("Metadata:", exp.meta)

Best Practices
--------------

- Use ``LogReader`` for detailed inspection of a single run.
- Use ``ExperimentReader`` for batch processing or querying multiple runs.
- Always check ``meta`` for the status and runtime of each run.
- Use ``arrays`` and ``artifacts`` to explore available data and outputs.
