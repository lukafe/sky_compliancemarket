# Phase 1 — Universe Audit & Definition (n=90)

## 1. Seed audit summary

- **Seed size:** 75 jurisdictions.
- **HARD field coverage:** Chainalysis rank present for all 75; AML/CFT maturity present; enforcement level present; legal status present.
- **HARD field gaps:** **Deadline date** and **Lifecycle stage** are NOT in the seed schema — both must be added as new columns during Phase 3 verification. These are the dominant urgency drivers.
- **Tier-vs-rank conflicts noted:** the v2 prompt flagged India Tier 3 / Ukraine Tier 5 mismatches; in *this* snapshot India is Tier 1 and Ukraine is Tier 1. v2 references reflected an older sheet — the current seed is internally consistent on tiering.
- **Confirmed staleness candidates** (re-verify in Phase 3):
  - **Pakistan** — seed labels "Gray Zone / No formal framework", but PVARA (Pakistan Virtual Asset Regulatory Authority) framework was advanced in late 2025. Almost certainly stale.
  - **Vietnam** — labelled "Legal – Formal (Jan 2026)" — need to confirm the actual legal status post-Jan 2026.
  - **Australia** — "New crypto bill (2025)" — need lifecycle stage confirmation.

## 2. Offshore / financial-hub gap (v2 known issue)

Seed includes Cayman, Bermuda, Gibraltar, Seychelles, Panama, Malta, Estonia, Lithuania. Missing offshore VASP hubs added below.

## 3. Additions (n=15) → Universe = 90

| # | Country | Reason |
|---|---|---|
| 1 | Liechtenstein | TVTG live; EEA→MiCA passportable; offshore hub |
| 2 | Luxembourg | Major fund domicile; MiCA; high institutional depth |
| 3 | Ireland | Major MiCA jurisdiction; Coinbase EU base; fintech/funds hub |
| 4 | Isle of Man | DBE crypto framework; offshore hub |
| 5 | Jersey | JFSC crypto framework; offshore hub |
| 6 | Guernsey | GFSC crypto framework; offshore hub |
| 7 | Bahamas | DARE Act 2024; FTX legacy; offshore VASP hub |
| 8 | British Virgin Islands | VASP Act 2022; major offshore VASP domicile |
| 9 | Austria | FMA + MiCA |
| 10 | Denmark | FSA + MiCA; Nordic |
| 11 | Sweden | FI + MiCA; Nordic + adoption |
| 12 | Cyprus | CySEC + CIF/CASP; historical crypto licensing hub |
| 13 | Norway | Finanstilsynet; EEA→MiCA-passportable |
| 14 | Mauritius | FSC VAITOS Act 2021; offshore hub |
| 15 | Dominican Republic | Emerging LATAM; CARF-aligned |

## 4. Exclusion rationale (what we deliberately did NOT add)

- **Sub-1M-population micro-states without published crypto frameworks** (Andorra, Monaco, San Marino) — no published HARD framework + negligible TAM.
- **War-active or sanctioned states** (Iran, Syria, Belarus) — Iran has heavy grey-market activity but no addressable market for Western compliance services; Belarus/HTP zone is sanctions-impaired.
- **No-population offshore tax shelters without crypto framework** (Anguilla, Turks & Caicos, Cook Islands) — no regime to anchor demand.
- **Already-covered offshore parents** (e.g., we added BVI but not its smaller affiliates).

## 5. Universe distribution (n=90)

| Region | n |
|---|---|
| Europe – EU | 16 |
| Asia-Pacific | 15 |
| Middle East | 10 |
| Latin America | 10 |
| Europe – Other | 7 |
| Sub-Saharan Africa | 6 |
| Europe – Non-EU | 4 |
| Caribbean | 4 |
| North America | 3 |
| Africa – N.Africa | 3 |
| Central Asia | 3 |
| South Asia | 3 |
| Eastern Europe | 2 |
| Southeast Asia | 2 |
| Indian Ocean | 2 |

## 6. Phase 1 Gate (operator approval)

- ✅ 90 jurisdictions reached.
- ✅ Offshore-hub coverage closed.
- ✅ Major MiCA EU members added.
- ✅ Staleness candidates flagged for Phase 3 HARD re-verification.

**Files:**
- `data/universe/universe.csv` (90 rows: Country, Region, Source)
- `data/universe/universe_additions.csv` (15 rows + rationale)

**Auto-mode: proceeding to Phase 2 (broad screen → longlist 20).**
