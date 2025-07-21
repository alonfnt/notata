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

        log.save_plot("quadratic")

This creates:

.. code-block:: text

    log_plot_test/
      plots/
        quadratic.png

Multiple Formats
----------------

You can save the same figure in multiple formats (e.g. PNG + PDF):

.. code-block:: python

    log.save_plot("quadratic", formats=["png", "pdf", "svg"])

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
    log.save_plot("explicit_fig", fig=fig)

Controlling DPI
---------------

You can control raster output resolution with the `dpi` argument:

.. code-block:: python

    log.save_plot("hires", dpi=300)

Organizing Plots into Subfolders
--------------------------------

Use the `category=` argument to route plots into a subdirectory:

.. code-block:: python

    log.save_plot("overview", category="plots/summaries")
