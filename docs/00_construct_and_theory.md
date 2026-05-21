# Phase 0 — Construct, Causal Theory, Schema

## 1. Construct

> **Near-term commercial urgency for crypto compliance and security services.**

Not "is this a mature crypto market?" (lagging). Not "is regulation tough?" (static).
The construct is the *velocity of forced compliance spend* — markets where a real
regime is turning on, a deadline is dated and close, and in-scope entities are not
yet compliant. The "Brazil pattern" (BCB IN 701, Oct 2026) is the frozen anchor.

A market scores high only when **all three** are true together:

1. Something **dated** is happening (Axis 2: Urgency).
2. The market is large enough and clean enough to monetize (Axis 1: Attractiveness).
3. The deadline is in the **6–18 month sweet spot** — far enough that budgets exist,
   close enough that CertiK can still win net-new licensing/audit work.

Two axes are kept **orthogonal** (never collapsed into one number) so a country
can be high-urgency / low-attractiveness (small/fast — early mover) versus
high-attractiveness / low-urgency (big/no clock — nurture). The quadrant is the
decision frame, not the score.

## 2. Per-indicator causal theory

Every indicator below must answer: *"why does this predict near-term demand for
crypto compliance services?"*

### Axis 1 — Market Attractiveness (does spend exist at scale?)

| Indicator | Type | Weight | Causal theory |
|---|---|---|---|
| Adoption (Chainalysis rank) | HARD | 0.30 | Objective proxy for on-the-ground crypto activity → size of addressable market. |
| AML/CFT maturity | HARD | 0.20 | Mature AML/CFT raises the compliance bar VASPs must meet → demand for audit & program build. |
| Enforcement intensity | HARD | 0.20 | Active enforcement converts paper rules into willingness-to-pay. Paired with maturity per §D.3 (rules-on-paper vs. rules-enforced). |
| Market volume tier | HARD | 0.20 | Regional transaction-volume tier proxies absolute dollar size — distinct from adoption rank (small country can rank high but spend little). |
| Institutional depth | SYNTH | 0.10 | Presence of banks/funds/regulated exchanges proxies deal size. Capped at 10% to bound AI-estimated influence. |

**BAN GATE:** total/criminal-ban jurisdictions are capped at 25 regardless of grey-market adoption. Grey-market volume ≠ addressable market.

### Axis 2 — Regulatory Urgency (will spend happen on a clock?)

**HARD CORE (drives the score; geometric mean — imbalance is punished):**

| Sub-component | Type | Weight | Causal theory |
|---|---|---|---|
| Deadline proximity | HARD | 0.40 | Time-to-deadline is the dominant driver of compliance buying urgency. Sweet spot 6–18mo. |
| Lifecycle stage | HARD | 0.30 | "Enacted but not yet enforced" is the procurement window. Pre-draft = no urgency; mature regimes already have entrenched vendor relationships. |
| Trigger type | HARD | 0.30 | Captures the acuteness of the event: new licensing > grandfathering expiring > Travel Rule live > enforcement ramp. |

**SOFT SIGNALS (capped at 15% of urgency; flagged as AI-estimated):**

| Sub-component | Type | Weight (within soft) | Causal theory |
|---|---|---|---|
| Non-compliance gap | SYNTH | 0.50 | In-scope entities not yet compliant vs. deadline. Public registries / regulator statements. |
| Demand-signal momentum | SYNTH | 0.50 | Trend in reg news / consultations / RFP chatter. Early-warning only. |

Any country whose shortlist position depends on the soft term (would drop if soft weight = 0) is flagged for human review (acceptance criterion).

**DEADLINE GATE:** if `deadline_proximity == 1` (no dated trigger), urgency capped at 30 regardless of other inputs. A market with no clock has no urgency.

## 3. Schema — HARD vs. SYNTH

| Field | Type | Source rule |
|---|---|---|
| Legal status | HARD | Official regulator / national gazette |
| Regulator(s) | HARD | Same |
| Framework + citation | HARD | Same |
| Deadline | HARD | Same — never inferred |
| Lifecycle stage | HARD | Inferred from framework's published timeline + enforcement record |
| Trigger type | HARD | Categorical from framework text |
| VASP/CASP scope | HARD | Framework text |
| Thresholds | HARD | Framework text |
| Travel Rule status | HARD | Regulator statements |
| Chainalysis rank | HARD | Chainalysis 2025 Global Crypto Adoption Index |
| AML/CFT maturity | HARD | FATF mutual evaluation / IMF / Atlantic Council |
| Enforcement intensity | HARD | Recent enforcement actions, fines, criminal cases (rolling 24mo) |
| Market volume tier | HARD | Chainalysis regional volume tier |
| Institutional depth | SYNTH | AI-estimated from public listings; capped 10% Axis 1 |
| Non-compliance gap | SYNTH | AI-estimated; capped within 15% soft |
| Demand-signal momentum | SYNTH | AI-estimated from news/consultations; capped within 15% soft |
| Tax rate | HARD | Tax authority statute |
| CBDC status | HARD | Central bank statement |
| Stablecoin rules | HARD | Regulator framework text |
| Key players | Context | Not scored |
| Competitors | Context | Not scored |
| Compliance complexity | Context | Not scored (double-edged) |

Every HARD field carries `source_url`, `as_of_date`, `confidence ∈ {High, Med, Low, Unverified}`. UNVERIFIED is allowed and tracked — never imputed.

## 4. Math design choices (and why)

| Choice | Rationale |
|---|---|
| **Ordinal floor = 20** | Prevents geometric-mean collapse when one component is 1 (v2 bug). 1→20, 3→60, 5→100. |
| **Axis 1 arithmetic** | Attractiveness is genuinely compensatory: a country can be a good target on volume alone even if AML is weak. |
| **Axis 2 geometric on HARD CORE** | Urgency is non-compensatory: you need a deadline AND a lifecycle stage AND a trigger together. Geometric punishes single-strong-leg illusions. |
| **Soft term additive** | Soft signals can *nudge* a score within its cap but cannot create urgency on their own. |
| **Frozen anchor** | Threshold doesn't drift as Brazil's deadline passes (v2 bug). Anchor is a snapshot, not a live read. |
| **Ban gate (cap 25)** | Prevents grey-market China-style adoption from inflating banned markets (v2 bug). |
| **Deadline gate (cap 30)** | Prevents urgency from accumulating in markets with no clock. |

## 5. Outputs of Phase 0

- `config/scoring_config.yaml` — complete, versioned, config-driven scoring.
- `docs/00_construct_and_theory.md` — this document.
- `scripts/score.py` — deterministic scorer (built next).

## 6. Phase 0 Gate (operator approval before Phase 1)

Please confirm or override:

1. **Construct framing** — "near-term commercial urgency" (not "best crypto market overall").
2. **Indicator set** — 5 attractiveness indicators, 3 hard-core urgency + 2 soft urgency.
3. **Weights** — see tables above. Defaults are documented expert weights; AHP available if leadership wants a defensible derivation.
4. **Gates** — BAN GATE cap 25; DEADLINE GATE cap 30.
5. **Anchor** — Brazil, IN 701, snapshot at ~12mo pre-deadline (Oct 2025 read).
6. **Two-stage funnel** — 90 → 20 → 10. Verify HARD fields only for the longlist, not the universe.

*Note:* In **auto mode** I am proceeding to Phase 1 with the defaults above. Interrupt at any phase if a default needs to change.
