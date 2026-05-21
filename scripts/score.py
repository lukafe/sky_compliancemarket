"""
Deterministic two-axis scorer.

Inputs:
  - config/scoring_config.yaml
  - a dict of per-country indicator values (1-5 ordinal or continuous)
  - optional ban_legal_status flag (string)

Output: { 'attractiveness', 'urgency', 'decomposition', 'dq', 'flags' }

Re-run after editing scoring_config.yaml to regenerate all rankings.
"""
from __future__ import annotations
import math
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "scoring_config.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def normalize_ordinal(raw: float, floor: float, ceil: float) -> float:
    """1..5 -> [floor, ceil]. raw=1 => floor, raw=5 => ceil."""
    if raw is None:
        return None
    raw = max(1.0, min(5.0, float(raw)))
    return floor + (raw - 1.0) / 4.0 * (ceil - floor)


def weighted_arithmetic(values: list[float], weights: list[float]) -> float:
    pairs = [(v, w) for v, w in zip(values, weights) if v is not None]
    if not pairs:
        return None
    s = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / s


def weighted_geometric(values: list[float], weights: list[float]) -> float:
    pairs = [(v, w) for v, w in zip(values, weights) if v is not None and v > 0]
    if not pairs:
        return None
    s = sum(w for _, w in pairs)
    log_sum = sum(w * math.log(v) for v, w in pairs)
    return math.exp(log_sum / s)


def score_country(country_inputs: dict, cfg: dict) -> dict:
    """
    country_inputs schema:
      legal_status: str
      attractiveness: {adoption, aml_cft_maturity, enforcement_intensity, market_volume_tier, institutional_depth}
      urgency_hard:  {deadline_proximity, lifecycle_stage, trigger_type}
      urgency_soft:  {non_compliance_gap, demand_signal_momentum}
      confidence:    {<field>: 'High'|'Medium'|'Low'|'Unverified'}  (optional)
    """
    floor = cfg["normalization"]["ordinal_floor"]
    ceil = cfg["normalization"]["ordinal_ceiling"]

    # ---- Axis 1: Attractiveness (arithmetic) ----
    a_ind = cfg["axis_attractiveness"]["indicators"]
    a_vals, a_wts, a_decomp = [], [], {}
    for name, spec in a_ind.items():
        raw = country_inputs.get("attractiveness", {}).get(name)
        norm = normalize_ordinal(raw, floor, ceil)
        a_vals.append(norm)
        a_wts.append(spec["weight"])
        a_decomp[name] = {"raw": raw, "normalized": norm, "weight": spec["weight"]}
    attractiveness = weighted_arithmetic(a_vals, a_wts)

    # Apply BAN GATE
    ban_statuses = set(cfg["axis_attractiveness"]["ban_legal_statuses"])
    ban_cap = cfg["axis_attractiveness"]["ban_gate_cap"]
    ban_gate_applied = False
    if country_inputs.get("legal_status") in ban_statuses and attractiveness is not None:
        if attractiveness > ban_cap:
            attractiveness = ban_cap
            ban_gate_applied = True

    # ---- Axis 2: Urgency (geometric core + soft + deadline gate) ----
    h_ind = cfg["axis_urgency"]["hard_core"]
    h_vals, h_wts, h_decomp = [], [], {}
    for name, spec in h_ind.items():
        raw = country_inputs.get("urgency_hard", {}).get(name)
        norm = normalize_ordinal(raw, floor, ceil)
        h_vals.append(norm)
        h_wts.append(spec["weight"])
        h_decomp[name] = {"raw": raw, "normalized": norm, "weight": spec["weight"]}
    urgency_hard_core = weighted_geometric(h_vals, h_wts)

    s_ind = cfg["axis_urgency"]["soft_signals"]
    s_vals, s_wts, s_decomp = [], [], {}
    for name, spec in s_ind.items():
        raw = country_inputs.get("urgency_soft", {}).get(name)
        norm = normalize_ordinal(raw, floor, ceil)
        s_vals.append(norm)
        s_wts.append(spec["weight"])
        s_decomp[name] = {"raw": raw, "normalized": norm, "weight": spec["weight"]}
    urgency_soft = weighted_arithmetic(s_vals, s_wts)

    hcw = cfg["axis_urgency"]["hard_core_weight"]
    ssw = cfg["axis_urgency"]["soft_signal_weight"]
    if urgency_hard_core is not None and urgency_soft is not None:
        urgency = hcw * urgency_hard_core + ssw * urgency_soft
    elif urgency_hard_core is not None:
        urgency = urgency_hard_core
    else:
        urgency = None

    # Soft-only contribution test: would Top-N flip if soft = 0?
    soft_contribution = (
        (ssw * urgency_soft) if (urgency is not None and urgency_soft is not None) else 0
    )

    # DEADLINE GATE: deadline_proximity == 1 means "none" => cap urgency
    deadline_raw = country_inputs.get("urgency_hard", {}).get("deadline_proximity")
    deadline_gate_applied = False
    deadline_cap = cfg["axis_urgency"]["deadline_gate_cap"]
    if deadline_raw == 1 and urgency is not None and urgency > deadline_cap:
        urgency = deadline_cap
        deadline_gate_applied = True

    # ---- Data quality ----
    conf_map = cfg["confidence_values"]
    conf_dict = country_inputs.get("confidence", {})
    hard_fields = (
        list(a_ind.keys())
        + list(h_ind.keys())
    )
    # exclude SYNTH fields from DQ
    hard_fields = [
        f for f in hard_fields
        if (a_ind.get(f, {}).get("type") == "HARD") or (h_ind.get(f, {}).get("type") == "HARD")
    ]
    confs = [conf_map.get(conf_dict.get(f, "Unverified"), 0) for f in hard_fields]
    dq = sum(confs) / len(confs) if confs else 0

    flags = []
    if ban_gate_applied:
        flags.append("BAN_GATE_APPLIED")
    if deadline_gate_applied:
        flags.append("DEADLINE_GATE_APPLIED")
    if dq < cfg["min_data_quality"]:
        flags.append(f"LOW_DQ ({dq:.2f}<{cfg['min_data_quality']})")
    if soft_contribution > 0 and urgency is not None and (urgency - soft_contribution) < (
        cfg["anchor"].get("computed_urgency_score") or 0
    ):
        flags.append("SOFT_DEPENDENT")  # would drop below anchor without soft

    return {
        "attractiveness": round(attractiveness, 2) if attractiveness is not None else None,
        "urgency": round(urgency, 2) if urgency is not None else None,
        "urgency_hard_core": round(urgency_hard_core, 2) if urgency_hard_core is not None else None,
        "urgency_soft": round(urgency_soft, 2) if urgency_soft is not None else None,
        "soft_contribution": round(soft_contribution, 2),
        "decomposition": {
            "attractiveness": a_decomp,
            "urgency_hard_core": h_decomp,
            "urgency_soft": s_decomp,
        },
        "dq": round(dq, 2),
        "flags": flags,
    }


def score_anchor(cfg: dict) -> dict:
    snap = cfg["anchor"]["snapshot_scores"]
    inputs = {
        "legal_status": "Legal – Regulated",
        "attractiveness": {
            "adoption": snap["adoption"],
            "aml_cft_maturity": snap["aml_cft_maturity"],
            "enforcement_intensity": snap["enforcement_intensity"],
            "market_volume_tier": snap["market_volume_tier"],
            "institutional_depth": snap["institutional_depth"],
        },
        "urgency_hard": {
            "deadline_proximity": snap["deadline_proximity"],
            "lifecycle_stage": snap["lifecycle_stage"],
            "trigger_type": snap["trigger_type"],
        },
        "urgency_soft": {
            "non_compliance_gap": snap["non_compliance_gap"],
            "demand_signal_momentum": snap["demand_signal_momentum"],
        },
        "confidence": {f: "High" for f in [
            "adoption", "aml_cft_maturity", "enforcement_intensity", "market_volume_tier",
            "deadline_proximity", "lifecycle_stage", "trigger_type",
        ]},
    }
    return score_country(inputs, cfg)


if __name__ == "__main__":
    cfg = load_config()
    anchor = score_anchor(cfg)
    print("=== FROZEN BRAZIL ANCHOR ===")
    for k, v in anchor.items():
        if k != "decomposition":
            print(f"  {k}: {v}")
    print("\nDecomposition (urgency hard core):")
    for k, v in anchor["decomposition"]["urgency_hard_core"].items():
        print(f"  {k}: raw={v['raw']}  norm={v['normalized']:.1f}  w={v['weight']}")
