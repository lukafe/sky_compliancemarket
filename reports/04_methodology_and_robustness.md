# Phase 4 — Methodology & Robustness Report

> One-page defense of the shortlist. All tests required by §H of the build spec passed.

## 1. Validation against controls

| Test | Result | Detail |
|---|---|---|
| **Positive control** — Brazil-anchor in Q1 | ✅ PASS | Brazil at (Attr 86, Urg 97) lands above both thresholds by design |
| **Negative control** — total-ban low-low | ✅ PASS | China (grey-market Chainalysis #20 + Total Ban): Attr=25 (BAN GATE), Urg=20 (no clock → geometric mean of 1-floor inputs = 20). Lands clearly low-low. Grey-market volume does NOT inflate score. |
| **Face validity** — Switzerland (mature DLT, no clock) | ✅ PASS | Attr=96 high, Urg=41.5 low → correctly Q3 (high attractiveness, low urgency). System recognizes mature-regime ≠ urgent. |
| **Face validity** — US (GENIUS enforcement-ramp) | ✅ PASS | Attr=96, Urg=78 → Q3-ish. NOT in Top-10 by urgency despite #2 Chainalysis rank — correctly identifying that GENIUS is enforcement-ramp, not net-new licensing. |
| **Face validity** — EU MiCA pre-Jul-2026 | ✅ PASS | Germany/France/Ireland/Netherlands all score 95.5-98.5 urgency — high but stratified by adoption + institutional depth, not flat. |

## 2. Spearman collinearity

Full matrix in `reports/03_collinearity.md`. Only one pair > 0.85 review threshold:

- **AML/CFT maturity ↔ Enforcement intensity (ρ=+0.93)** — kept separate by design per §D.3 (rules-on-paper vs. rules-enforced). High empirical correlation reflects longlist sampling (top-20 are advanced regimes where both move together). Documented; no model change. Sensitivity below confirms not load-bearing.

All other pairs |ρ| < 0.85. Lifecycle ↔ Trigger at 0.74 is the next-highest — within accepted range for theoretically related but distinct concepts.

## 3. Sensitivity — DATA bootstrap (PRIMARY; 1000 runs)

Per §H.5, data uncertainty dominates weight uncertainty. We perturbed each HARD input within its confidence band (Low: ±1, Medium: ±0.5, High: 0 on the 1-5 ordinal) and re-ran.

**Top-10 membership rate** (1.0 = always in Top-10):

| Country | Membership | Urgency 5-95% band |
|---|---|---|
| Turkey | **1.00** | [98.1, 100.0] |
| Germany | **1.00** | [96.5, 99.7] |
| France | **1.00** | [96.5, 99.7] |
| Nigeria | **1.00** | [96.3, 99.7] |
| Lithuania | 0.93 | [94.9, 99.1] |
| Poland | 0.93 | [94.9, 99.1] |
| Brazil | 0.92 | [94.9, 99.2] |
| Ireland | 0.91 | [94.9, 98.3] |
| Pakistan | **0.87** ⚠️ | [94.2, 99.7] — also soft-dependent |
| Vietnam | **0.85** ⚠️ | [93.9, 99.7] |
| Netherlands | 0.57 ← out | [93.5, 97.5] |

All Top-10 ≥ 85% membership rate. **No fragile entries** by the 0.70 threshold. Pakistan and Vietnam carry Medium-confidence inputs (new regimes 2024-25 with limited FATF follow-up) — flagged but stable.

## 4. Sensitivity — WEIGHT perturbation (SECONDARY; 1000 runs, ±20%)

| Country | Membership under weight perturbation | Urgency band |
|---|---|---|
| All 10 shortlist countries | **1.00** | Bands ≤ ±2 points |

**Weight choice does NOT drive the shortlist.** Validates §H.5 (data uncertainty is where the real uncertainty lives). Even if all weights are ±20% off, the shortlist is unchanged.

## 5. Sensitivity — SOFT signal dependence

Re-ran shortlist with `soft_signal_weight = 0`:

| Baseline Top-10 | Soft=0 Top-10 |
|---|---|
| Pakistan IN | Pakistan OUT (#11) |
| (Netherlands #11) | Netherlands IN |
| Other 9 stable | Same 9 |

**Stability 9/10.** Only **Pakistan** is soft-signal-dependent — flagged for human verification per acceptance criteria.

## 6. Bias register & mitigations

| Bias | Risk | Mitigation |
|---|---|---|
| **Recency** | Newest regimes over-weighted | Cross-checked with confidence levels; Vietnam/Pakistan/Kenya flagged Medium DQ. |
| **English-source** | Anglophone regimes over-verified | Brazil (PT), Nigeria, UAE primary sources included; Turkey CMB resmî gazete cited. |
| **Anchor confirmation** | Inadvertently tuning to "look like Brazil" | Anchor is frozen at a specific snapshot, threshold not retuned per country. Turkey ended up beating Brazil — proving we're not artificially preserving Brazil's primacy. |
| **Survivorship** (announced ≠ enacted) | Pre-draft regimes inflated | Lifecycle scale specifically penalizes pre-draft (1) and consultation (2); only enacted-not-enforced (5) flags as peak urgency. |
| **Regulator optimism** (enacted ≠ enforced) | Enforcement-only scores inflated | Enforcement Intensity scored on rolling 24mo of actual enforcement actions, not announcements. |

## 7. Final shortlist (n=10)

Ranked by data-bootstrap Top-10 membership rate, then urgency:

| Rk | Country | Attr | Urg | Q1 | Top-10 rate | Deadline | Flag |
|----|---|---|---|---|---|---|---|
| 1 | Turkey | 72 | 100.0 | ✅ | 1.00 | 2026-03-31 | — |
| 2 | Germany | 94 | 98.5 | ✅ | 1.00 | 2026-07-30 | — |
| 3 | France | 90 | 98.5 | ✅ | 1.00 | 2026-07-30 | — |
| 4 | Nigeria | 76 | 98.5 | ✅ | 1.00 | 2026-06-30 | — |
| 5 | Lithuania | 64 | 97.0 | ✅ | 0.93 | 2026-07-30 | — |
| 6 | Poland | 60 | 97.0 | ✅ | 0.93 | 2026-07-30 | — |
| 7 | Brazil | 86 | 97.0 | ✅ | 0.92 | 2026-10-31 | **ANCHOR** |
| 8 | Ireland | 86 | 97.0 | ✅ | 0.91 | 2026-07-30 | — |
| 9 | Pakistan | 56 | 100.0 | Q2 | 0.87 | 2026-11-30 | **SOFT_DEPENDENT** + Medium DQ |
| 10 | Vietnam | 66 | 100.0 | ✅ | 0.85 | 2026-01-01 | Medium DQ — verify before close |

(Pakistan is Q2 because Attr 56 sits just below universe-median 58. Still in Top-10 by urgency + bootstrap stability.)

## 8. Acceptance criteria (§K) — checklist

- [x] Frozen-Brazil in Q1
- [x] Negative control low-low (ban gate works on grey-market China)
- [x] Top-N stable under data bootstrap AND ±20% weight perturbation; fragile entries flagged
- [x] Shortlist positions NOT driven by soft signals alone (only Pakistan flagged; 9/10 stable when soft=0)
- [x] No unresolved Spearman pair > 0.85 (the one pair is documented design choice)
- [x] One config change → traceable new shortlist, no code edits (config YAML drives everything)
- [x] DQ ≥ 0.60 for all 10
- [x] Sources + as-of dates + confidence on every HARD field

**Shortlist accepted. Proceeding to Phase 5 (dossiers).**
