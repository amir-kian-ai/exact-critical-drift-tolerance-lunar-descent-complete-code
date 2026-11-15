# Reproducibility guide

## Environment

The recorded validation was run with Python 3.12 and the exact package versions in `requirements.txt`. Install Inkscape 1.4.2 only when regenerating SVG, PDF, or PNG figures. Numerical tests and CSV verification do not require Inkscape.

## Primary checks

From the repository root, run:

```bash
python -m pytest -q
python scripts/reproduce_drift.py --check
python experiments/drift_final_checks.py
```

Expected high-level outcomes:

- 50 tests pass with no skipped tests.
- The drift reproduction reports deterministic agreement after excluding timing and peak-memory fields.
- The independent five-step check returns an optimum of 21 at `gamma = 1/2`.
- `results/drift/rate_diagrams.csv` contains 42 rows: 11 four-step and 31 five-step endpoint/interior evaluations.
- `results/drift/timings.csv` contains 24 rows: four configurations, three repetitions, and two solvers with alternating execution order.

## Full historical reproduction

Earlier model generations remain available for audit. They can be rerun with:

```bash
python scripts/reproduce_research.py
python scripts/reproduce_enhanced.py
```

These scripts are retained to support traceability. The drift-focused commands above are the current manuscript checks.

## Result provenance

- `results/data/`, `results/enhanced/`, and `results/static/` preserve earlier experiment generations.
- `results/drift/` contains the current exact-rate, independent-check, reserved-panel, and timing data.
- `results/figures/editable_svg/` contains editable figure masters; publication PDF and preview PNG exports are stored alongside them.
- Runtime fields can vary with hardware and background load. Deterministic reproduction compares scientific fields while excluding `runtime_s` and `python_peak_bytes`.

The timing plot reports medians from the stored raw 24-run dataset. These desktop measurements document implementation behavior and do not establish onboard scalability.

## Numerical conventions

The production interval solver and the full-history oracle are implemented separately. Fractions are used for the exact drift and threshold logic. CSV `inf` denotes infeasibility. Some older JSON diagnostics contain Python `Infinity`, which strict RFC 8259 parsers may reject.

## Scope

The model is finite-horizon, has finitely many initial physical hypotheses, deterministic dynamics, and a shared scalar threshold subject to bounded inter-observation drift. Allocation values are synthetic metre-per-second-equivalent effort and sensing charges. They are not fuel or energy estimates.

