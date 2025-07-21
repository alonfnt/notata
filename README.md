# notata

[![tests](https://github.com/alonfnt/notata/actions/workflows/pytest.yml/badge.svg)](https://github.com/alonfnt/notata/actions/workflows/pytest.yml)
[![Docs](https://readthedocs.org/projects/notata/badge/?version=latest)](https://notata.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/notata.svg)](https://pypi.org/project/notata/)

<p align="center">
    <img style="width: 500px; height: auto;"  src="https://github.com/user-attachments/assets/0e73e7b8-bdee-4fcf-9872-fdf8b3d52156" />
</p>

`notata` is a minimal library for **structured filesystem logging of scientific runs**.

Each `Logbook` creates a run directory with parameters, arrays, plots, artifacts, metadata, and a timestamped log. **Explicit. Reproducible. Grep-friendly**.

## Installation
```bash
pip install notata
```

## Quick Start
### Context Manager
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

    log.save_arrays("trajectory", x=xs, v=vs)
    log.save_numpy("energy", E)
    log.save_json("final_state", {"x": float(x), "v": float(v), "E": float(E[-1])})
```

### Manual Lifecycle
```python
from notata import Logbook
import numpy as np

log = Logbook("heat_manual", params={"Nx": 64, "Ny": 64, "kappa": 0.01, "steps": 500})
Nx = Ny = 64
kappa = 0.01
dx = 1.0
dt = 0.2 * dx*dx / kappa

X, Y = np.meshgrid(np.linspace(-1,1,Nx), np.linspace(-1,1,Ny), indexing="ij")
T = np.exp(-6*(X**2 + Y**2))

snap_every = 100
for step in range(500):
    lap = (np.roll(T,1,0)+np.roll(T,-1,0)+np.roll(T,1,1)+np.roll(T,-1,1)-4*T)
    T += kappa * dt * lap
    if (step+1) % snap_every == 0:
        log.save_numpy(f"T_step{step+1}", T, category="data/intermediate")
        log.info(f"step={step+1} maxT={T.max():.4f}")
log.save_json("final_stats", {"max": float(T.max()), "mean": float(T.mean())})
log.mark_complete()
```

### Failure capture
```python
from notata import Logbook
import numpy as np

log = Logbook("unstable_run", params={"dt": 0.5})
try:
    dt = 0.5  # too large for stability
    x, v, w = 1.0, 0.0, 5.0
    for step in range(1000):
        a = -w**2 * x
        v += a * dt
        x += v * dt
        if not np.isfinite(x):
            raise RuntimeError("Diverged")
    log.mark_complete()
except Exception as e:
    log.mark_failed(str(e))
```

## Output format
Data is stored as following:
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
| `data/*.npz`                 | Array archives; single array → key `data`; multi-array save → keys = argument names                    |
| `data/**/`                   | Additional numeric outputs (via `category="data/..."`)                                                 |
| `plots/*.(png\|pdf\|svg)`    | Saved figures (`save_plot`)                                                                            |
| `artifacts/*.txt`            | Text artifacts (`save_text`)                                                                           |
| `artifacts/*.json`           | JSON artifacts (`save_json`)                                                                           |
| `artifacts/*.pkl`            | Pickled objects (`save_pickle`)                                                                        |
| `artifacts/*` (other)        | Raw bytes (`save_bytes`)                                                                               |
| `artifacts/**/`              | Nested artifact categories (e.g. `category="artifacts/logs"`)                                          |

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
