---
title: 'notata: Structured Filesystem Logging for Scientific Runs'
tags:
  - Python
  - scientific computing
  - logging
  - reproducibility
  - data management
  - HPC
  - numerical simulations
authors:
  - name: Albert Alonso
    email: aadlf@cs.aau.dk
    affiliation: 1
    orcid: 0000-0002-0441-0395
affiliations:
  - index: 1
    name: Aalborg University, Aalborg, Denmark
date: 26 January 2026
bibliography: paper.bib
repository: https://github.com/alonfnt/notata
---

# Summary

`notata` is a lightweight Python library for structured, file-based logging of scientific runs. It provides a simple, zero-infrastructure API for organizing simulation outputs, experimental data, and metadata in a reproducible, grep-friendly directory structure. Unlike machine learning logging platforms (e.g., Weights & Biases, TensorBoard, MLflow), `notata` is purpose-built for scientific workflows such as numerical simulations, solvers, and computational experiments where filesystem-level accessibility, local reproducibility, and integration with Unix tools are central to research practice. The library provides just that, a simple scaffolding API for managing scientific results, enabling seamless post-hoc analysis without external services or dependencies.

# Statement of Need

Scientific computing encompasses diverse computational workflows: solving differential equations, running stochastic simulations, executing parameter sweeps, and performing numerical experiments. These workflows generate outputs of varying types (arrays, plots, metadata, checkpoints) that must be organized, versioned, and later retrieved for analysis, comparison, and reproduction.

Most existing logging solutions, such as Weights & Biases [@wandb2020], TensorBoard [@tensorflow2015], MLflow [@matsuoka2020], were designed for machine learning model training in mind, where the primary concern is real-time monitoring, hyperparameter tracking, and cloud-based dashboards. These tools impose significant infrastructure overhead (servers, databases, APIs) and are optimized for scenarios with frequent scalar metric writes rather than heterogeneous data types or reproducibility-first workflows.

Scientific computing research, by contrast, often operates in more ad-hoc scenarios, where each researcher stores and logs their work in a different manner. For a field that values reproducibility and audit trails as primary concerns, the current approach results in less than an ideal solution. Thus, it can clearly benefit from results that are easy to explore, directly queryable via Unix tools and version-controllable, and remove the need for the user to place all the scaffolding neeeded.
Practically, a researcher running simulations might need to:

- Compare results across 100+ parameter combinations, querying results via `grep` or `find`.
- Reproduce a simulation from X months ago by inspecting saved parameters.
- Version-control results alongside code using standard Git workflows.
- Run simulations on machines without internet connectivity or cloud access.
- Integrate logging with shell scripts and existing computational pipelines.
- Explore previous work's results to reproduce figures.

Current tools fall short because they either: require external infrastructure, optimize for real-time dashboards over filesystem accessibility, or impose schemas that don't align with scientific computing practices.

`notata` addresses this gap by placing filesystem-level reproducibility, accessibility, and portability at the center of its design. The library captures domain expertise in managing parameter–result associations through a simple, zero-infrastructure API that integrates naturally with Unix tools and version control systems.

# Related work

The landscape of scientific data logging spans multiple domains and tools. General-purpose logging libraries (e.g., Python's `logging`, ELK stack [@elastic2024]) focus on operational monitoring rather than scientific reproducibility. Cloud-based experiment tracking platforms (Weights & Biases [@wandb2020], TensorBoard [@tensorflow2015], MLflow [@matsuoka2020]) optimize for real-time dashboards and hyperparameter tuning in machine learning, imposing significant infrastructure overhead and cloud dependencies unsuitable for HPC or offline workflows.

In the scientific computing domain, ad-hoc file-based logging remains common, but lacks structured organization and metadata tracking. Some domain-specific solutions exist—for example, Sacred [@greffSacredSimplifyingExperimentalSetup2017] for ML experiment tracking, and Snakemake [@kösterSnakmakePracticableScalable2012] for workflow management, but these target specific workflow patterns rather than providing a general solution for scientific simulation logging.

`notata` on the other hand, provides structured, filesystem-native logging designed from first principles for scientific computing, emphasizing reproducibility, portability, and integration with existing Unix tools and version control systems, rather than real-time monitoring or cloud infrastructure.

# Design and implementation

## Core Design Tradeoffs

`notata` makes deliberate design choices reflecting scientific computing realities but its minimal nature allows it to quickly adapt to the community needs:

**Filesystem over database**: Simulations often run on machines where installing and managing database services is impractical or prohibited. By using the filesystem as the primary data store, `notata` ensures portability, versionability, and accessibility without additional dependencies or infrastructure. This is also the most common way to store results, `notata` just organizes it.

**Simplicity over feature richness**: Rather than attempting to be a universal logging platform, `notata` provides a minimal API focused on the essential outputs of scientific runs: parameters, arrays, plots, and logs. This reduces complexity, improves maintainability, and makes the library easier to understand and adapt.

**Offline-first design**: Unlike cloud-based platforms, `notata` operates entirely offline. Results are immediately queryable via standard Unix tools without requiring external services. While `notata` is minimal by design, we are open to developed a GUI/TUI solution (extra library) on top of it in order to ease file exploration and management.

**Structured outputs over free-form logging**: The library enforces organization (parameters in YAML, arrays in NPZ, plots in standard image formats) to enable post-hoc analysis without requiring knowledge of internal logging details. This design captures domain expertise about what scientific workflows typically need to track. Extensions to other common saving formats is also an open option as long as there is community demand for it.

## Directory Structure and Reproducibility

Each run generates a self-contained, timestamped directory with clear separation of concerns:

```
log_<run_id>/
├── params.yml          # Parameters (human-readable, version-controllable)
├── metadata.yml        # System info, timestamps, software versions
├── log.txt             # Timestamped messages and progress
├── arrays/             # Numerical arrays (NumPy .npz/.npy format)
│   ├── trajectory.npz
│   └── statistics.npz
└── plots/              # Visualizations (PNG/PDF)
    ├── phase_space.png
    └── energy.png
```

This structure enables:
- **Grep-friendliness**: `grep "diverged" log_*/log.txt` finds all failed runs
- **Version control**: Parameters and logs are text-based and naturally compatible with Git
- **Audit trails**: Every run is timestamped with metadata (Python version, random seed, runtime)
- **Interoperability**: Arrays in standard NumPy format, images in PNG/PDF, metadata in YAML

## Comparison to Alternatives

| Tool | Use Case | Filesystem | Offline | Minimal Deps | No Server |
|------|----------|-----------|---------|--------------|-----------|
| `notata` | Scientific simulations | yes | yes | yes | yes |
| W&B | ML training dashboards | no | no | no | no |
| TensorBoard | Real-time ML metrics | no | Partial | no | no |
| MLflow | ML lifecycle management | Partial | no | no | no |
| Plain files | Undefined | no | yes | yes | yes |

`notata` fills the gap: structured, reproducible, filesystem-native logging designed for scientific computing rather than adapted from ML tools. It shares more similarity with just saving files that to more elaborate tracking platforms.

# Features

- **Logbook context manager**: Simple, Pythonic API for wrapping simulation/experiment code
- **Structured output types**: Parameters (YAML), arrays (NumPy), plots (matplotlib), arbitrary artifacts, timestamped logs
- **Automatic parameter tracking**: Parameters are captured and logged alongside results for reproducibility
- **Multi-run experiments**: `Experiment` API for managing collections of related runs with shared configuration
- **Reader utilities**: `LogReader` and `ExperimentReader` for post-hoc analysis and aggregation
- **Shell integration**: Output directories are queryable via standard Unix tools
- **Minimal dependencies**: Only `numpy` and `PyYAML`, with optional `matplotlib` for plotting
- **Lightweight**: Negligible performance overhead, suitable for compute-intensive workloads

# Typical Workflows

## Example 1: Parameter Sweep with Result Analysis

A researcher running a parameter sweep over 50 configurations can store each run's results and later analyze them via shell:

```python
from notata import Experiment
import numpy as np

# Define parameter sweep
params_list = [
  {'omega': omega, 'dt': dt}
  for omega in [1.0, 2.0, 3.0]
  for dt in [1e-3, 1e-4, 1e-5]
]

exp = Experiment(name="parameter_sweep", params_list=params_list)
for log in exp:
  omega, dt = log.params['omega'], log.params['dt']
  energy = simulate(omega, dt)

  log.arrays('energy', energy=energy)
  if np.all(energy < threshold):
    log.info("stable")
  else:
    log.info("unstable")

# Later: find all stable runs by grepping log files
# grep "stable" parameter_sweep_*/log_*/log.txt

# Find runs with specific parameter values
# grep "omega: 2.0" parameter_sweep_*/log_*/params.yml

# Aggregate results using ExperimentReader
from notata import ExperimentReader
exp_reader = ExperimentReader('parameter_sweep')
results = [(run.params['omega'], run.arrays('energy')) 
       for run in exp_reader.runs]
```

## Example 2: Long-Running Simulation with Checkpointing

A multi-hour simulation can log progress and save checkpoints:

```python
with Logbook("long_sim", params=config, autosave_dir="checkpoints") as log:
  for epoch in range(1000):
    state = compute_epoch(state)
    if epoch % 100 == 0:
      log.info(f"Epoch {epoch}: loss={state.loss}")
      log.arrays(f"checkpoint_{epoch}", state=state)
```

Results are immediately queryable and version-controllable, enabling reproducibility and post-hoc analysis without external services.

# Implementation and Testing

`notata` is implemented in pure Python and emphasizes robustness and maintainability:

- **Comprehensive test coverage**: Unit tests for core logging functionality, parameter handling, and output formats; integration tests for common workflows
- **Reader utilities**: `LogReader` for single-run analysis and `ExperimentReader` for aggregating multi-run results
- **Shell integration**: Command-line utilities for inspecting run logs and metadata
- **Documentation**: Tutorials covering basic usage, parameter sweeps, multi-run experiments, and post-hoc analysis
- **Open development**: All development conducted in public on GitHub with transparent issue tracking

The library is designed for both interactive use (Jupyter notebooks) and batch integration (HPC systems, shell scripts), with minimal performance overhead even on large simulation workloads.

# Impact and Scope

`notata` addresses a gap in the scientific software ecosystem. While machine learning logging tools dominate the landscape, scientific computing—simulations, solvers, numerical experiments—requires different design priorities. By providing structured, filesystem-native logging without infrastructure overhead, `notata` enables researchers to focus on science rather than software setup.

The library is scoped for scientific workflows where:
- Results must be reproducible and version-controllable
- Offline operation is necessary (HPC, air-gapped networks)
- Integration with Unix tools and shell scripts is valued
- Cloud-based dashboards are not required or desired

This design makes `notata` suitable for:
- **Numerical simulations**: ODE/PDE solvers, physics simulations, molecular dynamics
- **Parameter sweeps**: Systematic exploration of parameter spaces
- **Computational experiments**: Algorithm benchmarks, optimization studies, statistical experiments
- **HPC workflows**: Integration with job scheduling, batch processing, and file-based data management

The library's emphasis on simplicity, reproducibility, and portability aligns with reproducible science principles and best practices in open-source software development.

# Future steps

Near-term priorities include expanding support for additional output formats (HDF5, Parquet) to accommodate large-scale simulations, and enhanced integration with common scientific Python libraries (scipy, scikit-learn) for seamless logging of optimization results and statistical analyses. We aim to develop domain-specific extensions and plugins for specialized scientific communities (e.g., molecular dynamics, computational fluid dynamics) to demonstrate `notata`'s adaptability across research domains.

Long-term development will explore integration with workflow orchestration systems (Snakemake, Nextflow) to enable logging at the workflow level, and automated provenance tracking to capture computational lineage for enhanced reproducibility. Community contributions and feedback from active users will guide these directions.

# Availability

`notata` is distributed via PyPI (`pip install notata`) and available at https://github.com/alonfnt/notata under the MIT License. The source code is maintained with open governance on GitHub, with transparent issue tracking and pull request review. Complete documentation, including tutorials, API reference, and design rationale, is available at https://notata.readthedocs.io. The project follows semantic versioning and maintains a public changelog.

# AI usage discloure:
This work was prepared with assistance from large language models (ChatGPT 5) for initial unit-testing scaffolding and assistance in documentation management, as well as this manuscript structural organization, and editorial refinement. All technical content, design decisions, implementation details, reflect the authors' original work. The use of AI tools served to improve clarity and presentation quality.

# References
