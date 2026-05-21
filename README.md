# Crypto Compliance Intelligence System

Config-driven targeting system for CertiK BD. Finds jurisdictions where compliance demand is about to spike (the "Brazil pattern"). Re-runnable, decomposable, no black box.

## Quick start

```bash
# Re-run the entire pipeline
python3 scripts/run_broad_screen.py
python3 scripts/run_verified_scoring.py
python3 scripts/run_sensitivity.py
# Open the dashboard
open dashboard/index.html
```

## Outputs

| File | What |
|---|---|
| `data/shortlist/shortlist.csv` | The Top-10 targets |
| `reports/04_methodology_and_robustness.md` | Defense of the shortlist (controls, sensitivity, bias register) |
| `reports/06_bd_activation.md` | One-page BD activation view |
| `dossiers/01_…10_*.md` | Bilingual dossier per shortlist country |
| `dashboard/index.html` | Single-file dashboard (quadrant + timeline + drilldown) |
| `docs/08_runbook.md` | Maintenance + tuning recipes |

## Phase reports

| Phase | File |
|---|---|
| 0 — Framework | `docs/00_construct_and_theory.md` |
| 1 — Universe | `docs/01_universe_audit.md` |
| 2 — Broad screen | `docs/02_broad_screen.md` |
| 3 — Verified scoring | `docs/03_verified_scoring.md` |
| 4 — Validation + shortlist | `reports/04_methodology_and_robustness.md` |
| 5 — Dossiers | `dossiers/*.md` |
| 6 — BD activation | `reports/06_bd_activation.md` |
| 7 — Dashboard | `dashboard/index.html` |
| 8 — Runbook | `docs/08_runbook.md` |

## Core config

`config/scoring_config.yaml` — single source of truth for indicators, weights, gates, normalization, anchor, sensitivity, thresholds. Edit it + re-run the pipeline to regenerate everything.

## Refresh policy

- **Soft signals + rescoring:** auto-refresh weekly.
- **HARD legal facts** (deadline, framework, regulator, threshold, tax): manual quarterly re-verification — never automated.

## Acceptance criteria (§K of the build spec)

All seven met. See `docs/08_runbook.md` §11.
