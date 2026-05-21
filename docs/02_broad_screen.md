# Phase 2 — Stage 1 Broad Screen (preliminary scoring → longlist of 20)

## 1. Method (per §J Phase 2 of the build spec)

Cheap signals only — no HARD verification yet (that's Phase 3 on the longlist only).
Preliminary 1–5 ordinal estimates entered for all 90 countries based on:

- Known legal status (HARD, from seed and training-cutoff knowledge of major regimes)
- Existence of a dated regime + lifecycle stage + trigger type
- Chainalysis 2025 adoption tier (from seed)
- Regional volume tier (from seed)

All inputs live in `data/universe/broad_screen_inputs.csv` — edit + re-run `scripts/run_broad_screen.py` to regenerate.

## 2. Bloc-balance correction

The unconstrained longlist returned **12 MiCA jurisdictions** out of 20 — all sharing the same regime and Jul 2026 transition deadline. That clusters our verification budget into one bet. Applied a `MICA_BLOC_LONGLIST_CAP = 6` rule: keep the top 6 MiCA jurisdictions by priority, then refill with non-bloc standalones. Tunable in `run_broad_screen.py`.

## 3. Stress tests passed in this stage

| Test | Result |
|---|---|
| Brazil lands at top (positive control) | ✅ Rank #1, Attr 86, Urg 97 |
| Total-Ban countries capped by BAN GATE | ✅ 8 countries capped at Attr=25 (China, Egypt, Kuwait, Ghana, Bangladesh, Qatar, Cambodia, Morocco) |
| China grey-market adoption does NOT inflate score | ✅ Capped despite Chainalysis rank 20 |
| Deadline-gate behaviour | No countries flagged because no country had urgency >30 while deadline=1 (gate only triggers when needed; the all-low countries already score below the cap) |
| Above-anchor Q1 entries (frozen) | 1 (Brazil) — by design |

## 4. Longlist (n=20)

| Rk | Country | Attr | Urg | Bloc | Headline |
|---|---|---|---|---|---|
| 1 | Brazil | 86.0 | 97.0 | — | Anchor — IN 701 Oct 2026 |
| 2 | Pakistan | 56.0 | 100.0 | — | PVARA Nov 2025 (seed stale) |
| 3 | Germany | 94.0 | 93.0 | MiCA | MiCA + BaFin |
| 4 | France | 90.0 | 93.0 | MiCA | MiCA + PSAN→CASP |
| 5 | Ireland | 86.0 | 93.0 | MiCA | MiCA + Coinbase EU hub |
| 6 | Hong Kong | 92.0 | 91.2 | — | VASP + Stablecoin Ord Aug 2025 |
| 7 | Turkey | 72.0 | 92.7 | — | Capital Markets Law amend 2025 |
| 8 | Netherlands | 84.0 | 91.5 | MiCA | MiCA + AFM/DNB |
| 9 | United Kingdom | 82.0 | 91.2 | — | FSMA 2023 + FCA gateway 2026 |
| 10 | Vietnam | 66.0 | 92.7 | — | Jan 2026 NEW formal regime |
| 11 | Nigeria | 76.0 | 91.2 | — | ISA 2025 + VASP rules |
| 12 | Kenya | 56.0 | 92.7 | — | VASP Bill 2025 |
| 13 | Lithuania | 64.0 | 91.5 | MiCA | MiCA + historical VASP-licensing hub |
| 14 | Poland | 60.0 | 91.5 | MiCA | MiCA + KNF |
| 15 | Australia | 76.0 | 86.2 | — | Crypto licensing bill 2025 |
| 16 | United States | 100.0 | 82.8 | — | GENIUS enforcement ramp |
| 17 | Taiwan | 60.0 | 80.0 | — | VASP Act 2025 |
| 18 | Japan | 90.0 | 67.7 | — | PSA/FIEA 2025 amendments |
| 19 | UAE | 90.0 | 66.1 | — | VARA + ADGM expanding |
| 20 | South Korea | 84.0 | 63.0 | — | VAUPA phase 2 + token classification |

## 5. Borderline countries (rank 21–28) — operator-swappable

| Rk | Country | Note |
|---|---|---|
| 21 | Spain | Higher attractiveness than Lithuania/Poland but lower urgency. Swap-in candidate. |
| 22 | Italy | Same — swap-in candidate. |
| 23 | Indonesia | Bappebti→OJK transition. |
| 24 | Argentina | CNV registry. |
| 25 | Cyprus | MiCA satellite. |
| 26 | Luxembourg | MiCA satellite, high inst depth. |
| 27 | Estonia | MiCA + FIU. |
| 28 | Norway | MiCA via EEA. |

## 6. Methodological caveats for Phase 3

- **Soft-signal noise:** all top-25 are flagged `SOFT_DEPENDENT` because the anchor threshold (97) is high and the soft term (max 15% = ~15 points) is non-trivial near the threshold. Phase 4 sensitivity will properly test what flips if soft = 0.
- **MiCA clustering of regulators-on-the-same-clock:** treat each MiCA country as a distinct sales motion in Phase 3 (different regulators, different local VASP populations, different competing service providers) — but expect their scores to compress.
- **Pakistan deserves the biggest re-verification effort** — biggest delta from seed (Gray Zone → fresh regime). High value if true, embarrassing if I'm misreading PVARA status.

## 7. Files

- `data/longlist/broad_screen_results.csv` (90 countries, ranked)
- `data/longlist/longlist.csv` (20 countries — input to Phase 3)
- `docs/02_broad_screen.md` (this document)

## 8. Phase 2 Gate

In auto mode, proceeding to Phase 3 (HARD verification of the 20 longlist countries).
