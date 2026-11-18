# Data sources and audit

## Traffic

- Source: Dey, Kolkata Webel More research data, [Zenodo v0.1](https://zenodo.org/records/11235335); [processed source CSV](https://github.com/aceacedey/Kolkata_Data_PMC_paper_TrafficCountEstimationUsingCrowdSourcedTrajectory/blob/main/Intersection_SignalTiming_Traffic_Count/Processed_Count_and_timining_data.csv). Downloaded 18 November 2026.
- The authors describe camera-based ground-truth counts at one single-lane signalised intersection; the CSV timestamps are Kolkata local time. See the [dataset description](https://zenodo.org/records/11191588).
- `data/raw/traffic_original.csv` has 116 rows and fields: unnamed index, `Traj_no`, `Dates`, `Start`, `End`, `Count`, `HeadDelay`, `est_LinkCount`, `gPhaseDuration`, `gRatio`, `rPhaseDuration`, and `Penetration_rate`. No missing values were found. Counts range from 0 to 26. Nine observation dates span 29 August 2021 to 8 January 2022; they are sparse observations, not continuous daily counts.
- The source's [dated 29 August file](https://github.com/aceacedey/Kolkata_Data_PMC_paper_TrafficCountEstimationUsingCrowdSourcedTrajectory/blob/main/Intersection_SignalTiming_Traffic_Count/Dated_raw/29-08-2021%20Signal%20Timing%20Data%20Webel.csv), included locally for inspection, identifies green (`g`) and red (`r`) phases. Its green-phase count and seconds agree with corresponding processed rows. `Count` is used; `est_LinkCount` is a model estimate and is excluded. `gPhaseDuration` gives the green-phase length in seconds.
- The processed file records start and end only to the minute; 46 rows have the same recorded start and end minute. Do not subtract these rounded timestamps to infer duration. Observation durations vary. No hourly average or comparison of these unequal intervals as equal-length traffic rates is appropriate.

## OpenStreetMap

- Source: `data/raw/osm_export.geojson`, exported from [Overpass Turbo](https://overpass-turbo.eu/) at 19:33 UTC on 18 November 2026. The export is licensed under the [Open Database Licence](https://www.openstreetmap.org/copyright).
- Query scope: `amenity=charging_station` within 5 km of Webel More, plus `amenity=parking` and `shop=mall` within 1.2 km. The export contains four mapped charging stations and three eligible candidate places: RDB Boulevard (`way/194248709`), `way/358886818`, and `way/514535237`.
- Distances in the processed candidates file are Haversine straight-line distances to the exported mapped chargers, not driving distances. Mapped candidates are not confirmed available sites; missing chargers are not proof of no chargers.
