Saving Plots
============

``notata`` supports saving plots as artifacts, using either the active `matplotlib` figure or a given one.  
Saved plots are written to the ``plots/`` directory inside each run.

Basic Plot Saving
-----------------

If you're already plotting with `matplotlib`, saving a figure is one line:

.. code-block:: python

    import matplotlib.pyplot as plt
    from notata import Logbook

    with Logbook("plot_test") as log:
        x = [0.1 * i for i in range(100)]
        y = [xi**2 for xi in x]

        plt.plot(x, y)
        plt.xlabel("x")
        plt.ylabel("x squared")
        plt.title("Quadratic Function")

        log.plot("quadratic")

This creates:

.. code-block:: text

    log_plot_test/
      plots/
        quadratic.png

Multiple Formats
----------------

You can save the same figure in multiple formats (e.g. PNG + PDF):

.. code-block:: python

    log.plot("quadratic", formats=["png", "pdf", "svg"])

The files will be:

.. code-block:: text

    plots/
      quadratic.png
      quadratic.pdf
      quadratic.svg

Saving a Specific Figure Object
-------------------------------

If you create and manage `Figure` objects manually:

.. code-block:: python

    fig, ax = plt.subplots()
    ax.plot(x, y)
    log.plot("explicit_fig", fig=fig)

Controlling DPI
---------------

You can control raster output resolution with the `dpi` argument:

.. code-block:: python

    log.plot("hires", dpi=300)

Organizing Plots
----------------

All plots are saved inside the ``plots/`` subdirectory by default.
To create structure, you can include folder-like prefixes in the plot name itself:

.. code-block:: python

    log.plot("summaries/overview")

This will result in:

.. code-block:: text

    plots/
      summaries/
        overview.png
