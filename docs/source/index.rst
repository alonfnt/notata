notata
======

Structured filesystem logging for scientific runs.
**Explicit. Reproducible. Grep-friendly.**

Each ``Logbook`` creates a dedicated run directory that stores parameters, arrays, plots, artifacts, metadata, and a timestamped log.
It's designed to make scientific and numerical experiments fully transparent, auditable, and filesystem-native — without introducing database overhead or hidden state.

Why “notata”?
-------------

*Notata* is Latin for “notes,” “annotations,” or “marked things.”
The name reflects the library's purpose: to **record, organize, and preserve** the essential context of computational runs — clearly and permanently.

Motivation
----------

In scientific computing, reproducibility is often undermined by ad hoc scripts, manual logging, or missing metadata.
``notata`` addresses this by enforcing a structured, uniform layout for saving experiment state — logs, parameters, arrays, plots, and artifacts — in plain files and directories.

Many existing tracking libraries (like TensorBoard [1]_, Weights & Biases [2]_, MLflow [3]_ and others [4]_, [5]_, [6]_, [7]_) are excellent for machine learning workflows, but often:

- Impose heavier dependencies and dashboards
- Emphasize metrics, models, and visualizations tied to ML
- Abstract away the underlying filesystem

``notata`` is different: it’s minimal by design, and built for scientists and engineers who want to log structured data from simulations, numerical solvers, or parameter sweeps — not just train models.

It focuses on **clarity over complexity**, **file-based organization**, and **human-readability** — so any other scientist can inspect or reuse your results directly, without extra tooling.

If, however, you need to visualize or explore runs interactively, for example, inspecting logs, viewing saved arrays, or browsing plots, a companion tool, ``notata-view``, is planned.

It will provide a lightweight web-based dashboard for navigating ``notata`` run directories, without introducing any server dependencies, cloud backends, or vendor lock-in.
The goal is to offer **convenience without compromise**, optional tooling built on top of explicit, transparent filesystem structure.


Use Cases
---------

- Simulation runs with changing parameters.
- Parameter sweeps or grid searches.
- Long-running numerical experiments.
- Teaching or sharing reproducible computational workflows.
- Auditable research pipelines that don't rely on external platforms.

``notata`` makes your filesystem the database — with structure and discipline.


Installation
------------

.. code-block:: bash

    pip install notata

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   structure
   naming
   tutorials/quickstart
   tutorials
   api

Project Info
------------

- `GitHub <https://github.com/alonfnt/notata>`_
- `PyPI <https://pypi.org/project/notata/>`_

Citation
--------

If you use ``notata`` in your research or publications, please consider citing it:

.. code-block:: bibtex

    @software{notata_2025,
      author  = {Albert Alonso},
      title   = {notata: Structured Filesystem Logging for Scientific Runs},
      url     = {https://github.com/alonfnt/notata},
      version = {0.1.0},
      year    = {2025}
    }

License
-------

MIT License

References
----------

.. [1] TensorBoard – https://www.tensorflow.org/tensorboard
.. [2] Weights & Biases – https://wandb.ai
.. [3] MLflow – https://mlflow.org
.. [4] Sacred – https://sacred.readthedocs.io
.. [5] Aim – https://aimstack.io
.. [6] Comet – https://www.comet.com
.. [7] Guild AI – https://guild.ai
