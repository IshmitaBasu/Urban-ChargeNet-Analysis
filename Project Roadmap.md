# Urban ChargeNet — Kolkata Mini Project Roadmap

**Goal:** Build a **small, defensible EV charger site-screening case study** near **Webel More, Kolkata**, using **real intersection traffic counts**, OpenStreetMap locations, **Python**, and an **Excel dashboard**.

**Scope:** One intersection, **3 candidate sites**, one transparent scoring table, and **one-page Excel dashboard**. No machine learning, API service, database, cloud, or automated Excel dashboard generation.

**Business question:** *Where might we investigate a new EV charging point near Webel More, and what evidence is still missing before investment?*

> **Important:** This is a **screening exercise**, not proof of EV charging demand, commercial viability, available land, or grid feasibility. We have observed traffic at **one intersection**, not comparable traffic counts for all candidate sites. Do **not** invent counts or use the same intersection count as site-specific traffic exposure for all candidates.

## Data — use these sources only

| Source | Link | What to use | Important note |
|---|---|---|---|
| Kolkata Webel More research data | [Zenodo v0.1 dataset](https://zenodo.org/records/11235335) / [GitHub repository](https://github.com/aceacedey/Kolkata_Data_PMC_paper_TrafficCountEstimationUsingCrowdSourcedTrajectory) | Existing traffic-count CSVs from `Intersection_SignalTiming_Traffic_Count` | Inspect files first. Use **observed counts**, not estimated GNSS trajectories, where possible. CSV timestamps are already in Kolkata local time; `.txt` GNSS timestamps are GMT. Ignore GNSS files for this mini-project. |
| OpenStreetMap | [Overpass Turbo](https://overpass-turbo.eu/) | Existing EV chargers and 3 plausible parking / commercial candidate points near Webel More | Community mapping may be incomplete; use export date and attribution. Candidate locations **are not confirmed available sites**. |
| OSM tagging reference | [EV charging station tag](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dcharging_station) | Distinguish charging stations and, where tagged, charging types | Check whether entries actually represent car charging; unknown values remain unknown. |

**How to collect OSM data (manual, intentionally simple):** In Overpass Turbo, zoom to the Webel More area, then use Wizard queries separately for `amenity=charging_station` and `amenity=parking` (or `shop=mall`). Export as GeoJSON. Select **3 real mapped candidate points** in/near the study area; retain each OSM identifier or source link. If there are too few mapped chargers, widen the geographic search and note the increased radius. Do not use placeholder candidate coordinates or label selected sites as approved for construction.

## Phase 1 — Obtain and inspect real data

**Do:**
1. Download the linked research dataset. Find the traffic-count CSV(s); ignore the unrelated GNSS/headway files.
2. Inspect column names, date range, units, missing fields, and whether counts represent vehicles, intervals, or cumulative totals.
3. Export OSM chargers and parking / commercial places around Webel More; manually choose 3 candidate places.
4. Document both data sources and dates in `DATA_SOURCES.md`.

**Output:** `data/raw/traffic_original.csv`, `data/raw/chargers.geojson`, `data/raw/candidate_places.geojson`, `DATA_SOURCES.md`. Raw files can retain original names if the repo documents them.

**Done when:** You can point to **real source records** for the traffic counts and all 3 selected locations. If the count CSV cannot be interpreted reliably, stop instead of inventing values.

**Prompt for Codex:**
> Inspect the files in `data/raw/`. Identify observed traffic counts and their interval/timestamp meaning from the actual source. Print a concise data audit (columns, sample records, missing values, unit ambiguity). Do not assume column names or create fake observations. Write findings to `DATA_SOURCES.md`. Do not implement a dashboard.

## Phase 2 — Clean data and calculate 3 simple metrics (Python)

Use **pandas** and Python's standard library; optional **geopandas/shapely** only if needed to read GeoJSON.

**Traffic table** (`data/processed/traffic_intervals.csv`):
- Fields after mapping the **actual source schema**: `date`, `time_or_interval`, `vehicle_count` and optional `direction_or_link`.
- Derive only valid aggregates: total observed vehicles, peak observed interval, and average observed count per equal-length interval.
- If observations are irregular, mixed-unit, or sparse, preserve original intervals and **do not** calculate a misleading hourly average.

**Candidate table** (`data/processed/candidates.csv`):
- `candidate_id`, `candidate_name`, `latitude`, `longitude`, `source_osm_id`, `nearest_charger_distance_m`, `nearby_charger_count_1000m`, `location_type`, `data_quality_note`.
- Calculate **straight-line Haversine distance** to mapped existing car chargers. Make clear that these are *not driving distances*.
- The candidate's presence in OSM **does not prove** land access, parking permissions, traffic volume at that site, EV adoption, or grid capacity.
- If no existing chargers are mapped nearby, record `unknown/not found in source` appropriately rather than treating missing coverage as confirmed zero.

**Output:** Two clean CSVs plus `src/prepare_data.py` and a few simple data-check assertions (nonnegative counts, valid lat/lon, unique candidate IDs).

**Done when:** Re-running the script produces the same CSVs and no invented or silently filled observations.

**Prompt for Codex:**
> Implement `src/prepare_data.py` with pandas to transform the inspected research traffic-count CSV and OSM GeoJSON exports into `traffic_intervals.csv` and `candidates.csv`. Derive descriptive traffic metrics only from genuine observations. Use a small Haversine function for charger proximity. Check missing values, negative counts, duplicates, lat/lon ranges and 3 unique candidates. Keep the implementation minimal and explain assumptions. Do not infer site-level traffic from the single observed intersection.

## Phase 3 — Very small, explainable site screening

**Do not train a predictive model.** Score the 3 candidate locations in Excel using **only attributes that are actually available or explicitly assessed**.

Recommended **starter rubric** (mark values as *analyst-assessed*, not measured demand):

| Criterion | Weight | How to score (1 to 5) |
|---|---:|---|
| Gap from mapped existing car chargers | 60% | Larger distance / lower mapped local charger presence gets a higher score; define thresholds before scoring. |
| Accessibility / activity context | 40% | Manual site review using mapped parking, retail, or other amenities; keep a written justification for each 1–5 rating. |

**Excel formula:** `=0.6*CoverageGapScore+0.4*ActivityScore`

**Output:** A ranked table with `candidate`, `coverage_gap_score`, `activity_score`, `weighted_score`, `reason`, `major_unknowns`.

**Crucial:** The traffic-count trend is presented as **context for the Webel More area**, not as a numerical feature for ranking individual sites. State that the ranking is an exploratory heuristic and sensitive to weights and incomplete maps. A ranked candidate is only a **site for further investigation**.

**Done when:** You can explain *why* each candidate has its score and how changing a weight might change the ranking.

**Prompt for Codex:**
> Create an Excel-ready `candidate_scoring_template.csv` from `candidates.csv`. Include blank/manual score columns and source-backed metadata, not invented scores. Add a short `SCORING_NOTES.md` describing a 60/40 screening rubric, its limitations, and the Excel weighted-score formula. Do not assert predicted charger demand or ROI.

## Phase 4 — Build the Excel dashboard **yourself**

Create **one workbook**, with these tabs:

1. **Traffic_Data** — import the cleaned traffic CSV as an Excel Table.
2. **Candidates** — import candidate CSV, enter your justifiable 1–5 scores, and calculate the weighted score.
3. **Dashboard** — keep to **one screen**:
   - KPI: **total observed vehicles** (within dataset observation window, not per day).
   - KPI: **peak observed interval** (with its interval length).
   - **Line/column chart:** vehicle counts by observed time interval.
   - **Horizontal bar chart:** 3 candidate weighted scores.
   - **Small table:** ranked candidate, distance to nearest mapped charger, decision note.
   - Footer: `Exploratory study | Single-intersection traffic data | OSM coverage may be incomplete | No EV utilization or financial validation`.

Use Excel Tables, `SUM`, `MAX`, `XLOOKUP` (if useful), simple arithmetic, and charts. **No VBA or macros.** Do not ask Codex to build the dashboard for you; use it only to debug Excel formulas if needed.

**Output:** `dashboard/Urban_ChargeNet_Kolkata.xlsx` and one screenshot `dashboard/dashboard.png`.

**Done when:** A reader can see the **traffic pattern**, **three shortlisted sites**, and **why one was provisionally ranked highest** without scrolling through multiple sheets.

## Phase 5 — Publish and make it interview-ready

**Repository structure** (small on purpose):

```text
urban-chargenet-kolkata/
├── README.md
├── DATA_SOURCES.md
├── SCORING_NOTES.md
├── requirements.txt
├── data/
│   ├── raw/                  # download/export yourself; check license/size
│   └── processed/
│       ├── traffic_intervals.csv
│       ├── candidates.csv
│       └── candidate_scoring_template.csv
├── src/
│   └── prepare_data.py
└── dashboard/
    ├── Urban_ChargeNet_Kolkata.xlsx
    └── dashboard.png
```

**README structure:** business question → actual data sources → approach → Excel screenshot → 2–3 observations backed by output → limitations → how to reproduce.

**Final Codex prompt:**
> Review the completed repository for reproducibility and factual consistency. Ensure the README describes an **exploratory Kolkata Webel More site-screening case study**, not actual deployed infrastructure, model-predicted EV demand, network optimization, or verified investment returns. Check every claim against the output files. Keep setup instructions short. Do not fabricate metrics.

## Stop here — explicit non-goals

- No machine learning or demand forecasting without EV charging-session ground truth.
- No full-city traffic interpolation from one intersection.
- No FastAPI, Docker, AWS, CI/CD, or automated scheduling.
- No claim that any site is permitted, connected to the grid, financially viable, or definitively underserved.
- No fake traffic readings, EV utilization, revenue, installation costs, or projected ROI.

