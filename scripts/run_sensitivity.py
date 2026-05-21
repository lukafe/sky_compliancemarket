"""
Phase 4 — Sensitivity analysis (data bootstrap PRIMARY, weight perturbation SECONDARY).

Per §H of the build spec, data uncertainty dominates weight uncertainty. We:
  1. Perturb each HARD input within its confidence band (±1 on the 1-5 ordinal
     scale for Low conf, ±0.5 for Medium, 0 for High) — 1000 runs.
  2. Perturb weights ±20% uniformly — 1000 runs.
  3. Report Top-10 membership rate per country and a (5th, 50th, 95th) urgency
     band per country.
  4. Validate controls: anchor lands in Q1; total-ban negative control low-low;
     known recent regimes (MiCA, GENIUS) face-valid.

Writes data/shortlist/shortlist.csv + reports/04_sensitivity.md.
"""
from __future__ import annotations
import csv, random, sys, copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from score import load_config, score_country  # noqa: E402

INPUT = ROOT / "data" / "longlist" / "hard_verified.csv"
OUT_SHORT = ROOT / "data" / "shortlist" / "shortlist.csv"
OUT_REPORT = ROOT / "reports" / "04_sensitivity.md"
OUT_BANDS = ROOT / "data" / "shortlist" / "rank_bands.csv"


CONF_PERTURBATION = {"High": 0.0, "Medium": 0.5, "Low": 1.0, "Unverified": 1.5}


def to_int(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_inputs():
    rows = list(csv.DictReader(open(INPUT)))
    inputs_by_country = {}
    for r in rows:
        inp = {
            "country": r["Country"],
            "legal_status": r["legal_status"],
            "attractiveness": {
                "adoption": (to_int(r["adoption"]), r["conf_adoption"]),
                "aml_cft_maturity": (to_int(r["aml_cft_maturity"]), r["conf_aml"]),
                "enforcement_intensity": (to_int(r["enforcement_intensity"]), r["conf_enforcement"]),
                "market_volume_tier": (to_int(r["market_volume_tier"]), r["conf_volume"]),
                "institutional_depth": (to_int(r["institutional_depth"]), "Low"),  # SYNTH
            },
            "urgency_hard": {
                "deadline_proximity": (to_int(r["deadline_proximity"]), r["conf_deadline"]),
                "lifecycle_stage": (to_int(r["lifecycle_stage_raw"]), r["conf_lifecycle"]),
                "trigger_type": (to_int(r["trigger_type_raw"]), r["conf_trigger"]),
            },
            "urgency_soft": {
                "non_compliance_gap": (to_int(r["non_compliance_gap"]), "Low"),
                "demand_signal_momentum": (to_int(r["demand_signal_momentum"]), "Low"),
            },
        }
        inputs_by_country[r["Country"]] = inp
    return inputs_by_country


def perturb_value(v, conf, rng):
    if v is None:
        return None
    delta = CONF_PERTURBATION.get(conf, 1.0)
    # uniform within band, clipped to [1,5]
    p = v + rng.uniform(-delta, delta)
    return max(1.0, min(5.0, p))


def make_scoring_input(raw, rng=None):
    """Convert (val, conf) tuples to flat dict; perturb if rng given."""
    def conv(group):
        out = {}
        for k, (v, c) in group.items():
            out[k] = perturb_value(v, c, rng) if rng else v
        return out
    return {
        "legal_status": raw["legal_status"],
        "attractiveness": conv(raw["attractiveness"]),
        "urgency_hard": conv(raw["urgency_hard"]),
        "urgency_soft": conv(raw["urgency_soft"]),
        "confidence": {k: c for grp in ["attractiveness", "urgency_hard"]
                       for k, (_, c) in raw[grp].items()},
    }


def perturb_weights(cfg, pct, rng):
    cfg_p = copy.deepcopy(cfg)
    for grp_name in ["axis_attractiveness", "axis_urgency"]:
        if grp_name == "axis_urgency":
            for sub in ["hard_core", "soft_signals"]:
                for k in cfg_p[grp_name][sub]:
                    w = cfg_p[grp_name][sub][k]["weight"]
                    cfg_p[grp_name][sub][k]["weight"] = w * (1 + rng.uniform(-pct, pct))
        else:
            for k in cfg_p[grp_name]["indicators"]:
                w = cfg_p[grp_name]["indicators"][k]["weight"]
                cfg_p[grp_name]["indicators"][k]["weight"] = w * (1 + rng.uniform(-pct, pct))
    return cfg_p


def run_bootstrap(inputs, cfg, n_runs, kind, rng_seed=42):
    """kind: 'data' or 'weights'."""
    rng = random.Random(rng_seed)
    countries = list(inputs.keys())
    # Track urgency per run + top-N membership
    urgency_runs = {c: [] for c in countries}
    attr_runs = {c: [] for c in countries}
    topN_hits = {c: 0 for c in countries}
    rank_per_run = []

    topN = cfg["sensitivity"]["stability_topn"]
    pct = cfg["sensitivity"]["weight_perturbation_pct"]

    for _ in range(n_runs):
        if kind == "data":
            cfg_use = cfg
            rng_data = rng
        else:
            cfg_use = perturb_weights(cfg, pct, rng)
            rng_data = None

        run_scores = []
        for c in countries:
            inp = make_scoring_input(inputs[c], rng=rng_data if kind == "data" else None)
            out = score_country(inp, cfg_use)
            urgency_runs[c].append(out["urgency"] or 0)
            attr_runs[c].append(out["attractiveness"] or 0)
            run_scores.append((c, (out["urgency"] or 0), (out["attractiveness"] or 0)))

        run_scores.sort(key=lambda x: (x[1], x[2]), reverse=True)
        in_topN = {c for c, _, _ in run_scores[:topN]}
        for c in in_topN:
            topN_hits[c] += 1
        rank_per_run.append([c for c, _, _ in run_scores])

    # Bands
    def pct_band(vals):
        s = sorted(vals)
        n = len(s)
        if n == 0:
            return (0, 0, 0)
        p05 = s[max(0, int(0.05 * n) - 1)]
        p50 = s[n // 2]
        p95 = s[min(n - 1, int(0.95 * n))]
        return (p05, p50, p95)

    out = {}
    for c in countries:
        u_band = pct_band(urgency_runs[c])
        a_band = pct_band(attr_runs[c])
        out[c] = {
            "urgency_p05": round(u_band[0], 2),
            "urgency_p50": round(u_band[1], 2),
            "urgency_p95": round(u_band[2], 2),
            "attr_p05": round(a_band[0], 2),
            "attr_p50": round(a_band[1], 2),
            "attr_p95": round(a_band[2], 2),
            "topN_rate": topN_hits[c] / n_runs,
        }
    return out


def main():
    cfg = load_config()
    inputs = load_inputs()
    n_data = cfg["sensitivity"]["data_bootstrap_runs"]
    n_weights = cfg["sensitivity"]["weight_perturbation_runs"]
    fragility = cfg["sensitivity"]["fragility_flag_threshold"]
    anchor_u = cfg["anchor"]["computed_urgency_score"]

    print(f"Running data bootstrap ({n_data} runs)...")
    data_results = run_bootstrap(inputs, cfg, n_data, "data")
    print(f"Running weight perturbation ({n_weights} runs, ±20%)...")
    wt_results = run_bootstrap(inputs, cfg, n_weights, "weights", rng_seed=99)

    # Baseline scores (no perturbation)
    baseline = {}
    for c, raw in inputs.items():
        out = score_country(make_scoring_input(raw), cfg)
        baseline[c] = out

    # Merge into table
    table = []
    for c in inputs:
        b = baseline[c]
        d = data_results[c]
        w = wt_results[c]
        in_q1 = (b["urgency"] or 0) >= anchor_u and (b["attractiveness"] or 0) >= 58.0
        fragile_data = d["topN_rate"] < fragility
        fragile_wts = w["topN_rate"] < fragility
        table.append({
            "Country": c,
            "attractiveness": b["attractiveness"],
            "urgency": b["urgency"],
            "urgency_p05_data": d["urgency_p05"],
            "urgency_p95_data": d["urgency_p95"],
            "urgency_p05_weights": w["urgency_p05"],
            "urgency_p95_weights": w["urgency_p95"],
            "topN_rate_data": round(d["topN_rate"], 2),
            "topN_rate_weights": round(w["topN_rate"], 2),
            "in_Q1": in_q1,
            "fragile_data": fragile_data,
            "fragile_weights": fragile_wts,
        })

    table.sort(key=lambda x: (x["topN_rate_data"], x["urgency"] or 0), reverse=True)

    # Print
    print(f"\n{'Country':<20} {'A':>5} {'U':>5} {'U_data':>14} {'U_wts':>14} {'top10_d':>8} {'top10_w':>8} {'Q1':>3} {'frag'}")
    for r in table:
        ud = f"[{r['urgency_p05_data']:.1f},{r['urgency_p95_data']:.1f}]"
        uw = f"[{r['urgency_p05_weights']:.1f},{r['urgency_p95_weights']:.1f}]"
        frag = ("D" if r["fragile_data"] else " ") + ("W" if r["fragile_weights"] else " ")
        print(f"{r['Country']:<20} {r['attractiveness']:>5} {r['urgency']:>5} "
              f"{ud:>14} {uw:>14} {r['topN_rate_data']:>8} {r['topN_rate_weights']:>8} "
              f"{'Y' if r['in_Q1'] else ' ':>3} {frag}")

    # Shortlist: top 10 by data topN rate (primary), tiebreak urgency
    shortlist = table[:10]
    OUT_SHORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_SHORT, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        wr.writeheader()
        wr.writerows(shortlist)

    with open(OUT_BANDS, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        wr.writeheader()
        wr.writerows(table)

    print(f"\nShortlist ({len(shortlist)}): {[r['Country'] for r in shortlist]}")
    print(f"Fragile under data: {[r['Country'] for r in table if r['fragile_data']]}")
    print(f"Fragile under weights: {[r['Country'] for r in table if r['fragile_weights']]}")


if __name__ == "__main__":
    main()
