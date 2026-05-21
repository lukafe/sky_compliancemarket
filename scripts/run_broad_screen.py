"""
Phase 2 — Stage 1 broad screen + bloc-balanced longlist selection.

Reads data/universe/broad_screen_inputs.csv, scores all 90, then builds the
longlist with a MiCA-bloc cap so the longlist captures regulatory diversity
rather than the same regime 12 times.
"""
from __future__ import annotations
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from score import load_config, score_country  # noqa: E402

INPUT = ROOT / "data" / "universe" / "broad_screen_inputs.csv"
RESULTS = ROOT / "data" / "longlist" / "broad_screen_results.csv"
LONGLIST = ROOT / "data" / "longlist" / "longlist.csv"

MICA_BLOC = {
    "Germany", "France", "Netherlands", "Spain", "Italy", "Poland",
    "Estonia", "Lithuania", "Portugal", "Malta", "Austria", "Denmark",
    "Sweden", "Luxembourg", "Cyprus", "Ireland", "Norway",
}
MICA_BLOC_LONGLIST_CAP = 6   # max MiCA seats on the 20-slot longlist


def to_int(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def main():
    cfg = load_config()
    rows = list(csv.DictReader(open(INPUT)))
    anchor_urgency = cfg["anchor"]["computed_urgency_score"]
    anchor_attr = cfg["anchor"]["computed_attractiveness_score"]

    results = []
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
                "lifecycle_stage": to_int(r["lifecycle_stage"]),
                "trigger_type": to_int(r["trigger_type"]),
            },
            "urgency_soft": {
                "non_compliance_gap": to_int(r["non_compliance_gap"]),
                "demand_signal_momentum": to_int(r["demand_signal_momentum"]),
            },
            "confidence": {
                f: "Medium" for f in [
                    "adoption", "aml_cft_maturity", "enforcement_intensity",
                    "market_volume_tier", "deadline_proximity", "lifecycle_stage",
                    "trigger_type",
                ]
            },
        }
        out = score_country(inputs, cfg)
        priority = (
            (1 if (out["urgency"] or 0) >= anchor_urgency else 0) * 1000
            + (out["urgency"] or 0) * 10
            + (out["attractiveness"] or 0)
        )
        in_q1 = (out["urgency"] or 0) >= anchor_urgency and (out["attractiveness"] or 0) >= anchor_attr
        results.append({
            "Country": r["Country"],
            "legal_status": r["legal_status"],
            "attractiveness": out["attractiveness"],
            "urgency": out["urgency"],
            "urgency_hard_core": out["urgency_hard_core"],
            "urgency_soft": out["urgency_soft"],
            "flags": ",".join(out["flags"]),
            "in_Q1_anchor": in_q1,
            "priority_score": round(priority, 2),
            "regime_note": r.get("regime_note", ""),
            "is_mica": r["Country"] in MICA_BLOC,
        })

    results.sort(key=lambda x: x["priority_score"], reverse=True)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    # Bloc-balanced longlist
    longlist_size = cfg["universe"]["longlist_size"]
    longlist, mica_count = [], 0
    for r in results:
        if len(longlist) >= longlist_size:
            break
        if r["is_mica"]:
            if mica_count >= MICA_BLOC_LONGLIST_CAP:
                continue
            mica_count += 1
        longlist.append(r)

    with open(LONGLIST, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(longlist[0].keys()))
        w.writeheader()
        w.writerows(longlist)

    print(f"Universe scored: {len(results)}")
    print(f"Above anchor (Q1 candidates): {sum(1 for r in results if r['in_Q1_anchor'])}")
    print(f"Longlist size: {len(longlist)} (MiCA={mica_count}, others={len(longlist)-mica_count})\n")

    print(f"=== LONGLIST (n={len(longlist)}) ===")
    print(f"{'Rk':>2} {'Country':<25} {'Attr':>5} {'Urg':>5} {'Bloc':<6}")
    for i, r in enumerate(longlist, 1):
        bloc = "MiCA" if r["is_mica"] else "—"
        print(f"{i:>2} {r['Country'][:25]:<25} {r['attractiveness']:>5} {r['urgency']:>5} {bloc:<6}")

    # Stress tests
    print(f"\n=== BAN GATE applied ({sum(1 for r in results if 'BAN_GATE_APPLIED' in r['flags'])} countries) ===")
    for r in results:
        if "BAN_GATE_APPLIED" in r["flags"]:
            print(f"  {r['Country']:<25} attr={r['attractiveness']} ({r['legal_status']})")


if __name__ == "__main__":
    main()
