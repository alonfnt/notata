# notata

[![tests](https://github.com/alonfnt/notata/actions/workflows/pytest.yml/badge.svg)](https://github.com/alonfnt/notata/actions/workflows/pytest.yml)
[![Docs](https://readthedocs.org/projects/notata/badge/?version=latest)](https://notata.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/notata.svg)](https://pypi.org/project/notata/)

<p align="center">
    <img style="width: 500px; height: auto;"  src="https://github.com/user-attachments/assets/0e73e7b8-bdee-4fcf-9872-fdf8b3d52156" />
</p>

`notata` is a minimal library for **structured filesystem logging of scientific runs**.

Each `Logbook` creates a run directory with parameters, arrays, plots, artifacts, metadata, and a timestamped log. **Explicit. Reproducible. Grep-friendly**.

Unlike ML logging tools (e.g. W&B, TensorBoard, MLflow), notata is built for scientific workflows such as simulations, solvers, and numerical experiments, where file-based logging matters more than dashboards.
**No servers, no setup, no reinventing the wheel for each new project.**

## Installation
```bash
pip install notata
```

## Quick Start
### Context Manager
Logs a single simulation run to `log_<run_id>/`, including arrays, metadata, and messages.
```python
from notata import Logbook
import numpy as np

with Logbook("oscillator_dt1e-3", params={"omega": 2.0, "dt": 1e-3, "steps": 10_000}) as log:
    omega = 2.0
    dt = 1e-3
    steps = 10_000
    x, v = 1.0, 0.0

    xs = np.empty(steps)
    vs = np.empty(steps)
    E  = np.empty(steps)

    for n in range(steps):
        a = -omega**2 * x
        x += v*dt + 0.5*a*dt*dt
        a_new = -omega**2 * x
        v += 0.5*(a + a_new)*dt
        xs[n], vs[n] = x, v
        E[n] = 0.5*(v**2 + (omega*x)**2)
        if (n+1) % 2000 == 0:
            log.info(f"step={n+1} x={x:.4f} v={v:.4f} E={E[n]:.6f}")

    log.arrays("trajectory", x=xs, v=vs)
    log.array("energy", E)
    log.json("final_state", {"x": float(x), "v": float(v), "E": float(E[-1])})
```
This creates a structured folder with logs, parameters, and output arrays for reproducibility.

### Manual Lifecycle
For full control, create a `Logbook` manually and mark it complete when you're done.
```python
from notata import Logbook
import numpy as np

Nx = Ny = 64
kappa = 0.01
dx = 1.0
dt = 0.2 * dx*dx / kappa

X, Y = np.meshgrid(np.linspace(-1,1,Nx), np.linspace(-1,1,Ny), indexing="ij")
T = np.exp(-6*(X**2 + Y**2))

log = Logbook("heat_eq")
log.params(Nx=Nx, Ny=Ny, kappa=kappa, steps=steps)

for step in range(500):
    lap = (np.roll(T,1,0)+np.roll(T,-1,0)+np.roll(T,1,1)+np.roll(T,-1,1)-4*T)
    T += kappa * dt * lap
    if (step+1) % 100 == 0:
        log.array(f"states/T_step{step+1}", T)
        log.info(f"step={step+1} maxT={T.max():.4f}")
log.json("final_stats", {"max": float(T.max()), "mean": float(T.mean())})
log.mark_complete()
```
### Parameter sweeps with `Experiment`
Automatically log multiple runs, each in its own directory, with structured metadata and failure tracking:

```python
from notata import Experiment
import numpy as np

exp = Experiment("falling_ball")

for dt in [0.01, 0.5]:  # stable vs unstable
    log = exp.add(dt=dt, skip_existing=True)
    if log is None:
        continue
    with log:
        v, h = 0.0, 100.0
        for _ in range(100):
            v += 9.81 * dt
            h -= v * dt
            if h < 0:
                raise RuntimeError(f"Object hit the ground (h={h:.2f})")
        log.json("metrics", {"final_height": h, "final_speed": v})
```
Each run creates a `log_<run_id>/` folder and appends a row to `index.csv` with parameters, status, and final metrics:

| run\_id                 | dt   | status   | final\_height | final\_speed |
| ----------------------- | ---- | -------- | ------------- | ------------ |
| falling\_ball\_dt\_0.01 | 0.01 | complete | 95.04595      | 9.81         |
| falling\_ball\_dt\_0.5  | 0.5  | missing  |               |              |

## Using ExperimentReader

Since `notata` log dirs are somewhat verbose, we also provided a utility wrapper to load and read the data.
This makes it more intuitive when you need to compare runs (e.g. in experiments), or you just don't want to deal with the files paths.
For single runs you can directly use `notata.LogReader`.

```python
from notata import ExperimentReader
import matplotlib.pyplot as plt

# Load the experiment
exp = ExperimentReader("outputs/oscillator_sweep")

# Plot energy vs time for each run
fig, ax = plt.subplots()
for run in exp:
    omega, dt = run.params['omega'], run.params['dt']
    energy = run.load_array("energy")
    label = f"omega={omega}, dt={dt}"
    ax.plot(energy, label=label)
ax.set(xlabel="Time step", ylabel="Energy", title="Energy vs Time")
ax.legend()
plt.show()

# Print summary of runs
for run in exp:
    status = run.meta.get('status', 'unkown')
    duration = run.meta.get('runtime_sec', 'unknown')
    print(f"Run ID: {run.run_id}, {status=}, {duration=}")
```

## Output format
Data is stored as following in order to be intuitive to explore:
```bash
log_<run_id>/
  log.txt
  metadata.json
  params.yaml
  data/
  plots/
  artifacts/
```

where the files follow:

| Path / Pattern                | Purpose / Format                                                                                      |
|------------------------------|--------------------------------------------------------------------------------------------------------|
| `log.txt`                    | Plain text log; lines: `[YYYY-MM-DDTHH:MM:SS] LEVEL message`                                           |
| `metadata.json`              | Run metadata: `status`, `start_time`, optional `end_time`, `runtime_sec`, optional `failure_reason`, `run_id` |
| `params.yaml` / `params.json`| Parameter snapshot (latest saved form)                                                                 |
| `data/*.npy` / `data/*.npz` | `.npy` for single arrays (`array()`); `.npz` for multi-array bundles (`arrays(...)`)                    |
| `plots/*.(png\|pdf\|svg)`    | Saved figures (`save_plot`)                                                                            |
| `artifacts/*.txt`            | Text artifacts (`save_text`)                                                                           |
| `artifacts/*.json`           | JSON artifacts (`save_json`)                                                                           |
| `artifacts/*.pkl`            | Pickled objects (`save_pickle`)                                                                        |
| `artifacts/*` (other)        | Raw bytes (`save_bytes`)                                                                               |
| `artifacts/**/`              | Nested artifact categories                                                                             |

## Documentation

Full documentation, tutorials, and examples are available at:
[https://notata.readthedocs.io/en/latest/](https://notata.readthedocs.io/en/latest/)

## Citation
You don't have to, but if you use `notata` in your research and need to reference it, please cite it as follows:
```
@software{notata_2025,
  author  = {Albert Alonso},
  title   = {notata: Structured Filesystem Logging for Scientific Runs},
  url     = {https://github.com/alonfnt/notata},
  version = {0.1.0},
  year    = {2025}
}
```

## License
MIT License
