# Exact Drift Margins for History-Consistent Recovery in Finite Lunar Descent

This repository contains the complete Python research implementation, experiment framework, recorded numerical results, verification scripts, and supporting documentation for the manuscript *Exact Drift Margins for History-Consistent Recovery in Finite Lunar Descent*.

The software studies finite-horizon lunar-descent recovery when a shared scalar visual-detection threshold drifts by a bounded amount between observations. It includes exact interval synthesis, an independently implemented full-history oracle, critical-rate diagram construction, reserved test cases, timing experiments, and publication-quality figure generation.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/` | Production solvers and model implementations |
| `tests/` | Unit, regression, endpoint, and independent-oracle tests |
| `experiments/` | Validation studies, diagnostics, timing runs, and figure generators |
| `scripts/` | Reproduction, analysis, audit, and export utilities |
| `configs/` | Experiment configuration files |
| `results/` | Recorded data, exact-rate results, verification summaries, and figures |
| `research/` | Mathematical, experimental, and scope documentation |
| `review/` and `evidence/` | Archived audit evidence supporting the private research record |

## Requirements

- Python 3.12 (Python 3.11 or newer is declared by the package metadata)
- NumPy 2.3.5
- Matplotlib 3.11.2
- pytest 9.1.1
- pypdf 6.10.0
- Inkscape 1.4.2 for regenerating the finalized vector/PDF/PNG figures

Create an isolated environment and install the pinned packages:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Conda users may instead run:

```bash
conda env create -f environment.yml
conda activate exact-drift-margins
```

## Verification

Run the test suite from the repository root:

```bash
python -m pytest -q
```

Reproduce the current drift results and verify deterministic CSV content:

```bash
python scripts/reproduce_drift.py --check
python experiments/drift_final_checks.py
```

The validated package contains 50 tests. The history-equivalence test enumerates 18,720 scalar histories. The independent full-history implementation checks eight reserved cases, four diagram queries, and the five-step optimum of 21 at a drift bound of 0.5. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for scope, commands, expected artifacts, and runtime-data qualifications.

## Main reproducible results

- The four-step case uses 11 exact endpoint/interior evaluations and has cost 16 at zero drift, 18 for positive drift through 0.5 metres per observation, and is infeasible above 0.5.
- The five-step case uses 31 exact endpoint/interior evaluations and has costs 19 and 21 over the corresponding feasible regions.
- The stored reserved panel contains 256 cases and 24 alternating-order timing measurements.
- Exact rational arithmetic is used where documented; `inf` in CSV output denotes infeasibility.

These values are model-specific synthetic allocation results. They are not physical fuel, reliability, or onboard-scalability claims.

## Reproducibility notes

The project uses no external dataset or model checkpoint. Generated caches, virtual environments, editor state, credentials, and operating-system files are excluded from version control. Some historical JSON diagnostics use Python's `Infinity` token and may require a permissive parser; the current numerical source tables are also available as CSV.

The manuscript source is maintained separately from this code repository. Figure-generation scripts synchronize with a companion manuscript only when it is placed beside this project; the numerical tests and recorded results do not require the manuscript.

## Citation and license

Provisional software citation metadata is provided in `CITATION.cff`. The final bibliographic citation and DOI will be added after publication.

No software license is granted in this repository. A license should be added only after the authors explicitly select and authorize one.


