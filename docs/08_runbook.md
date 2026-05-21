# Phase 8 — Runbook (Maintenance, Refresh, Tuning, Scaling)

> The system is a **living asset**. This runbook covers the common ops:
> refresh, tune a weight, add a country, re-run controls. Time estimates assume one analyst.

---

## 0. Project layout (where lives what)

```
config/
  scoring_config.yaml         # SINGLE SOURCE OF TRUTH for indicators, weights, gates,
                              # normalization, anchor, sensitivity, thresholds.
                              # Edit this file + re-run scripts/* to regenerate everything.

data/
  seed/                       # source spreadsheet → CSVs
  universe/
    universe.csv              # the 90 jurisdictions
    universe_additions.csv    # the 15 deliberately added (with reasons)
    broad_screen_inputs.csv   # preliminary 1-5 ordinal inputs (Stage 1)
  longlist/
    broad_screen_results.csv  # 90 countries, ranked by Stage 1 priority
    longlist.csv              # the 20 selected
    hard_verified.csv         # source-attributed HARD inputs for the 20
    scored.csv                # verified scores
  shortlist/
    shortlist.csv             # final Top-10
    rank_bands.csv            # all 20 with bootstrap bands

scripts/
  score.py                    # deterministic scorer (loaded by everything else)
  run_broad_screen.py         # Phase 2
  run_verified_scoring.py     # Phase 3 + collinearity
  run_sensitivity.py          # Phase 4 (data bootstrap + weight perturbation)

dossiers/
  _template.md                # bilingual dossier template
  01_*.md .. 10_*.md          # the 10 shortlist dossiers

reports/
  03_collinearity.md          # Spearman matrix
  04_methodology_and_robustness.md   # the defense doc
  06_bd_activation.md         # cross-country BD view

dashboard/
  index.html                  # single-file dashboard
  data.json                   # pre-baked payload — regenerate when scores change

docs/
  00_construct_and_theory.md  # construct, causal theory, schema
  01_universe_audit.md        # Phase 1 audit
  02_broad_screen.md          # Phase 2 deliverable
  03_verified_scoring.md      # Phase 3 deliverable
  08_runbook.md               # this file
```

---

## 1. Pipeline (the standard end-to-end re-run)

```bash
# from project root
python3 scripts/run_broad_screen.py        # Stage 1 → universe ranking + longlist
python3 scripts/run_verified_scoring.py    # Stage 2 → verified scoring + collinearity
python3 scripts/run_sensitivity.py         # Stage 3 → bootstrap + weight + shortlist
# Regenerate dashboard data:
python3 -c "
import csv, json, yaml
ROOT='.'
universe=list(csv.DictReader(open(f'{ROOT}/data/longlist/broad_screen_results.csv')))
scored=list(csv.DictReader(open(f'{ROOT}/data/longlist/scored.csv')))
bands=list(csv.DictReader(open(f'{ROOT}/data/shortlist/rank_bands.csv')))
v={r['Country']:r for r in scored}; b={r['Country']:r for r in bands}
cfg=yaml.safe_load(open(f'{ROOT}/config/scoring_config.yaml'))
out=[]
for r in universe:
    c=r['Country']
    base={'country':c,'attractiveness':float(r['attractiveness']),'urgency':float(r['urgency']),
          'legal_status':r['legal_status'],'notes':r.get('regime_note',''),'flags':r.get('flags','')}
    if c in v:
        x=v[c]; y=b.get(c,{})
        base.update({'urgency_hard_core':float(x.get('urgency_hard_core',0)),
                     'urgency_soft':float(x.get('urgency_soft',0)),
                     'dq':float(x.get('dq',0)),'deadline':x.get('deadline_iso',''),
                     'framework':x.get('framework',''),'regulator':x.get('regulator',''),
                     'stage':'verified','flags':x.get('flags',''),'notes':x.get('notes',''),
                     'urgency_p05':float(y.get('urgency_p05_data',0)),
                     'urgency_p95':float(y.get('urgency_p95_data',0)),
                     'top10_rate':float(y.get('topN_rate_data',0))})
    else:
        base.update({'urgency_hard_core':float(r['urgency_hard_core']),
                     'urgency_soft':float(r['urgency_soft']),
                     'dq':None,'deadline':'','framework':'','regulator':'','stage':'screen',
                     'urgency_p05':None,'urgency_p95':None,'top10_rate':None})
    out.append(base)
json.dump({'config_version':cfg['version'],'config_date':cfg['config_date'],
           'anchor_urgency':cfg['anchor']['computed_urgency_score'],
           'anchor_attractiveness':cfg['anchor']['computed_attractiveness_score'],
           'attractiveness_threshold_universe_median':58.0,
           'countries':out},
          open(f'{ROOT}/dashboard/data.json','w'),indent=2)
print('dashboard/data.json updated')
"
open dashboard/index.html
```

**Total runtime: ~5 seconds** on the current dataset. Bootstraps default to 1000 runs each.

---

## 2. Refresh (what runs automatically vs. manually)

Per §I and Phase 7 spec, refresh is honestly scoped:

### 2.1 Auto-refresh (no human required)
- **Soft signals** — `non_compliance_gap`, `demand_signal_momentum`
- **Rescoring** — re-running the scorer with updated soft signals
- Cadence: weekly (operator schedules a cron or `/loop`)

### 2.2 Manual refresh (human verification required)
- **HARD legal facts** — deadline, framework citation, regulator, license thresholds, tax, Travel Rule status
- Cadence: quarterly, plus on-event (when a jurisdiction announces a change)
- For each updated field: replace value + `source_url` + `as_of_date` + `confidence` in `data/longlist/hard_verified.csv`
- **Re-run the full pipeline** afterward + **re-run controls** (next section).

---

## 3. Tune a weight (config change → traceable new shortlist)

```bash
# Example: down-weight enforcement_intensity due to AML↔Enforcement ρ=0.93 finding
# Edit config/scoring_config.yaml:
#   axis_attractiveness.indicators.enforcement_intensity.weight: 0.20 → 0.175
#   axis_attractiveness.indicators.market_volume_tier.weight:   0.20 → 0.225
# Then:
python3 scripts/run_broad_screen.py
python3 scripts/run_verified_scoring.py
python3 scripts/run_sensitivity.py
# Diff old vs new shortlist
diff data/shortlist/shortlist.csv data/shortlist/shortlist.csv.bak
```

**Acceptance criterion:** one config change → traceable new shortlist, no code edits. ✅

---

## 4. Add a country

```bash
# 1. Append to data/universe/universe_additions.csv (with reason)
# 2. Append a row to data/universe/broad_screen_inputs.csv with cheap-signal estimates
# 3. python3 scripts/run_broad_screen.py
# 4. If the new country lands in the top-25, consider promoting to the longlist:
#    - Add a row to data/longlist/hard_verified.csv with source-attributed HARD values
#    - Optionally drop the lowest-scoring longlist row to maintain n=20
# 5. python3 scripts/run_verified_scoring.py + run_sensitivity.py
# 6. Write a dossier in dossiers/ if it makes the Top-10
```

---

## 5. Re-run controls after ANY change (mandatory)

These three tests must continue to pass:

| Test | What it proves | Where to read result |
|---|---|---|
| Anchor (Brazil) in Q1 | Calibration intact | `data/longlist/scored.csv` row for Brazil |
| Negative control (China) low-low | BAN GATE works | Run `python3 -c "import sys; sys.path.insert(0,'scripts'); from score import *; ..."` |
| Top-10 stability ≥0.85 under data bootstrap | Shortlist not data-fragile | `data/shortlist/rank_bands.csv` `topN_rate_data` column |

Quick command for all three:

```bash
python3 scripts/run_sensitivity.py | tee /tmp/run.log
grep -E "Brazil|China|Shortlist|fragile" /tmp/run.log
```

---

## 6. Tune the anchor (rare — be careful)

**Default policy: don't.** The anchor is frozen on purpose so the urgency threshold doesn't drift. Re-anchoring should only happen if:

1. Brazil's IN 701 deadline passes AND CertiK validates the system against a different reference regime.
2. Or: leadership wants to switch the anchor to a different "Brazil-pattern" jurisdiction.

To re-anchor:

```yaml
# In config/scoring_config.yaml, change `anchor:` block:
anchor:
  reference: "<new country>"
  regime: "<new framework + citation>"
  deadline: "<ISO date>"
  snapshot_taken_when: "~Xmo pre-deadline"
  snapshot_scores: {<all 10 indicators 1-5>}
  computed_urgency_score: null
  computed_attractiveness_score: null
```

Then `python3 scripts/score.py` will recompute and you must paste the new `computed_*` values back into the config (pin them).

**After re-anchoring:** re-run the full pipeline and write a one-paragraph rationale to `docs/anchor_change_<date>.md`.

---

## 7. Scaling — bigger universe, more countries

The Stage 1 broad screen is the bottleneck. To go from 90 → 150:

- Add countries to `universe.csv` + `broad_screen_inputs.csv`.
- The scorer is O(N) — runtime stays linear.
- Bootstrap runs: 1000 × N is fine up to a few hundred countries.

To go from 10 → 25 dossiers per quarter:

- The `_template.md` dossier scaffold is the workflow. Each dossier is ~2-3 hours of analyst work.
- Consider a "tier-2 dossier" template (60 min, no PT-BR) for Q2 countries.

---

## 8. Cron / `/loop` automation (optional)

If the operator wants weekly soft-signal refresh:

```bash
# A weekly job (cron / claude /loop):
# 1. Update soft signals (manually or via an agent that ingests news/RFP chatter)
# 2. Re-run pipeline
# 3. Regenerate dashboard/data.json
# 4. Diff shortlist.csv vs. previous; if changed, notify
```

Manual HARD-fact refresh stays on a quarterly cadence — see §2.2.

---

## 9. Diagnostic recipes

**"My new country isn't in the longlist."** Check the priority score in `broad_screen_results.csv`. If MiCA, see the bloc-cap rule in `scripts/run_broad_screen.py` (`MICA_BLOC_LONGLIST_CAP`).

**"My country's urgency dropped."** Run `python3 scripts/run_verified_scoring.py` and inspect the decomposition column. The geometric mean penalizes imbalance — single weak hard-core component will pull the score sharply down.

**"Shortlist is suddenly volatile."** Re-check `data/shortlist/rank_bands.csv` `topN_rate_data` and `topN_rate_weights`. If `topN_rate_data < 0.70` for a Top-10 entry, the inputs are too noisy — increase confidence on at least one HARD field.

**"Two indicators became collinear."** Re-run `scripts/run_verified_scoring.py` and read `reports/03_collinearity.md`. ρ > 0.85 triggers human review per §H.4 — never auto-drop.

**"Anchor needs to move."** See §6.

---

## 10. Versioning & change log

- Config is versioned (`config/scoring_config.yaml` has `version` and `config_date`).
- All output CSVs include the columns needed to compute the scores deterministically.
- Recommend: snapshot `data/shortlist/shortlist.csv` and `config/scoring_config.yaml` together (e.g., `data/snapshots/2026-05-20/`).

---

## 11. Acceptance-criteria recap (§K of the build spec)

- [x] Frozen-Brazil in Q1; negative control low-low (ban gate works on grey-market China)
- [x] Every HARD field: source + date + confidence; UNVERIFIED listed
- [x] Top-N stable under data bootstrap AND ±20% weight perturbation; fragile entries flagged; shortlist positions NOT driven by soft signals alone (Pakistan is flagged as the one soft-dependent)
- [x] No unresolved Spearman pair > 0.85 (the one pair is documented design choice)
- [x] One weight change → traceable new shortlist, no code edits
- [x] Each shortlist country: bilingual dossier, TAM as a justified range, named referral path, falsifiable hypothesis
- [x] Methodology & Robustness Report defends every ranking

**System is operational.**
