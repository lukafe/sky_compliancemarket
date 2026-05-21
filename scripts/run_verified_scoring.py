"""
Phase 3 — Stage 2 verified scoring.

Reads data/longlist/hard_verified.csv (source-attributed HARD inputs),
runs the deterministic scorer, computes Spearman collinearity on the longlist,
writes data/longlist/scored.csv + reports/03_collinearity.md.
"""
from __future__ import annotations
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from score import load_config, score_country  # noqa: E402

INPUT = ROOT / "data" / "longlist" / "hard_verified.csv"
OUT_SCORED = ROOT / "data" / "longlist" / "scored.csv"
OUT_COLLIN = ROOT / "reports" / "03_collinearity.md"


def to_int(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def spearman(x, y):
    """Hand-rolled Spearman to avoid scipy dep. Returns rho or None if invalid."""
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 4:
        return None
    a, b = zip(*pairs)
    def rank(v):
        sorted_v = sorted(enumerate(v), key=lambda t: t[1])
        ranks = [0] * len(v)
        i = 0
        while i < len(sorted_v):
            j = i
            while j + 1 < len(sorted_v) and sorted_v[j + 1][1] == sorted_v[i][1]:
                j += 1
            avg = sum(range(i + 1, j + 2)) / (j - i + 1)
            for k in range(i, j + 1):
                ranks[sorted_v[k][0]] = avg
            i = j + 1
        return ranks
    ra, rb = rank(list(a)), rank(list(b))
    n = len(ra)
    ma, mb = sum(ra)/n, sum(rb)/n
    num = sum((ra[i]-ma)*(rb[i]-mb) for i in range(n))
    da = sum((ra[i]-ma)**2 for i in range(n)) ** 0.5
    db = sum((rb[i]-mb)**2 for i in range(n)) ** 0.5
    if da == 0 or db == 0:
        return None
    return num / (da * db)


def main():
    cfg = load_config()
    rows = list(csv.DictReader(open(INPUT)))

    scored = []
    indicator_columns = {
        "adoption": [],
        "aml_cft_maturity": [],
        "enforcement_intensity": [],
        "market_volume_tier": [],
        "institutional_depth": [],
        "deadline_proximity": [],
        "lifecycle_stage": [],
        "trigger_type": [],
        "non_compliance_gap": [],
        "demand_signal_momentum": [],
    }

    for r in rows:
        inputs = {
            "legal_status": r["legal_status"],
            "attractiveness": {
                "adoption": to_int(r["adoption"]),
                "aml_cft_maturity": to_int(r["aml_cft_maturity"]),
                "enforcement_intensity": to_int(r["enforcement_intensity"]),
                "market_volume_tier": to_int(r["market_volume_tier"]),
                "institutional_depth": to_int(r["institutional_depth"]),
            },
            "urgency_hard": {
                "deadline_proximity": to_int(r["deadline_proximity"]),
                "lifecycle_stage": to_int(r["lifecycle_stage_raw"]),
                "trigger_type": to_int(r["trigger_type_raw"]),
            },
            "urgency_soft": {
                "non_compliance_gap": to_int(r["non_compliance_gap"]),
                "demand_signal_momentum": to_int(r["demand_signal_momentum"]),
            },
            "confidence": {
                "adoption": r["conf_adoption"],
                "aml_cft_maturity": r["conf_aml"],
                "enforcement_intensity": r["conf_enforcement"],
                "market_volume_tier": r["conf_volume"],
                "deadline_proximity": r["conf_deadline"],
                "lifecycle_stage": r["conf_lifecycle"],
                "trigger_type": r["conf_trigger"],
            },
        }
        out = score_country(inputs, cfg)
        for k in indicator_columns:
            if k in inputs.get("attractiveness", {}):
                indicator_columns[k].append(inputs["attractiveness"][k])
            elif k in inputs.get("urgency_hard", {}):
                indicator_columns[k].append(inputs["urgency_hard"][k])
            else:
                indicator_columns[k].append(inputs["urgency_soft"][k])

        scored.append({
            "Country": r["Country"],
            "deadline_iso": r["deadline_iso"],
            "framework": r["framework"],
            "regulator": r["regulator"],
            "attractiveness": out["attractiveness"],
            "urgency": out["urgency"],
            "urgency_hard_core": out["urgency_hard_core"],
            "urgency_soft": out["urgency_soft"],
            "dq": out["dq"],
            "flags": ",".join(out["flags"]),
            "notes": r.get("notes", ""),
        })

    scored.sort(key=lambda x: (x["urgency"], x["attractiveness"]), reverse=True)
    OUT_SCORED.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(scored[0].keys()))
        w.writeheader()
        w.writerows(scored)

    print(f"=== Scored longlist (n={len(scored)}) — sorted by urgency, attr ===\n")
    print(f"{'Rk':>2} {'Country':<20} {'Attr':>5} {'Urg':>5} {'DQ':>5} {'Flags'}")
    for i, r in enumerate(scored, 1):
        print(f"{i:>2} {r['Country']:<20} {r['attractiveness']:>5} {r['urgency']:>5} {r['dq']:>5} {r['flags']}")

    # Spearman collinearity (longlist only, since universe lacks normalized inputs)
    print(f"\n=== Spearman correlation matrix (longlist, n={len(rows)}) ===")
    pairs = []
    names = list(indicator_columns.keys())
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            rho = spearman(indicator_columns[a], indicator_columns[b])
            if rho is not None:
                pairs.append((a, b, rho))
    pairs.sort(key=lambda t: abs(t[2]), reverse=True)
    print(f"Top 10 absolute correlations:")
    for a, b, rho in pairs[:10]:
        marker = " ⚠️  REVIEW" if abs(rho) >= cfg["collinearity"]["review_pair_threshold"] else ""
        print(f"  {a:<25} ↔ {b:<25} ρ = {rho:+.2f}{marker}")

    # Write collinearity report
    OUT_COLLIN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_COLLIN, "w") as f:
        f.write("# Phase 3 — Spearman Collinearity Report (longlist n={})\n\n".format(len(rows)))
        f.write(f"Review threshold: |ρ| ≥ {cfg['collinearity']['review_pair_threshold']}. Action: human review (never auto-drop).\n\n")
        f.write("| Indicator A | Indicator B | Spearman ρ | Action |\n")
        f.write("|---|---|---|---|\n")
        for a, b, rho in pairs:
            action = "**REVIEW**" if abs(rho) >= cfg["collinearity"]["review_pair_threshold"] else "ok"
            f.write(f"| {a} | {b} | {rho:+.3f} | {action} |\n")

    # Data quality summary
    low_dq = [r for r in scored if r["dq"] < cfg["min_data_quality"]]
    print(f"\nLow-DQ countries ({len(low_dq)}): {[r['Country'] for r in low_dq]}")


if __name__ == "__main__":
    main()
