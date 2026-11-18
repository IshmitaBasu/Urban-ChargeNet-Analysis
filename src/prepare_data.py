"""Create reproducible traffic and candidate tables from the supplied source exports."""
from __future__ import annotations
import json
import math
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"

def haversine_m(lat1, lon1, lat2, lon2):
    radius_m = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(math.radians(lon2-lon1)/2)**2
    return 2 * radius_m * math.asin(math.sqrt(a))

def prepare_traffic():
    source = pd.read_csv(RAW / "traffic_original.csv")
    fields = ["Dates", "Start", "End", "Count", "gPhaseDuration"]
    if source[fields].isna().any().any(): raise ValueError("Missing traffic fields")
    counts, duration = pd.to_numeric(source["Count"], errors="raise"), pd.to_numeric(source["gPhaseDuration"], errors="raise")
    if (counts < 0).any() or (counts % 1 != 0).any() or (duration <= 0).any(): raise ValueError("Invalid traffic count or duration")
    if source.duplicated(["Dates", "Start", "End"]).any(): raise ValueError("Duplicate traffic interval")
    return pd.DataFrame({"date": pd.to_datetime(source["Dates"], format="%d/%m/%Y").dt.strftime("%Y-%m-%d"), "time_or_interval": source["Start"]+"–"+source["End"], "vehicle_count": counts.astype(int), "green_phase_seconds": duration})

def prepare_candidates():
    with (RAW / "osm_export.geojson").open(encoding="utf-8") as file: features = json.load(file)["features"]
    chargers, places = [], []
    for feature in features:
        prop = feature["properties"]; lon, lat = feature["geometry"]["coordinates"]
        record = {"latitude": lat, "longitude": lon, "source_osm_id": prop["@id"], "name": prop.get("name")}
        if prop.get("amenity") == "charging_station": chargers.append(record)
        elif prop.get("amenity") == "parking" or prop.get("shop") == "mall":
            record["location_type"] = "mall" if prop.get("shop") == "mall" else "parking"; places.append(record)
    if len(places) != 3 or not chargers: raise ValueError("Expected exactly 3 candidates and at least one charger")
    rows = []
    for i, place in enumerate(places, 1):
        distances = [haversine_m(place["latitude"], place["longitude"], c["latitude"], c["longitude"]) for c in chargers]
        rows.append({"candidate_id": f"C{i}", "candidate_name": place["name"] or f"Mapped {place['location_type']} ({place['source_osm_id']})", "latitude": place["latitude"], "longitude": place["longitude"], "source_osm_id": place["source_osm_id"], "nearest_charger_distance_m": round(min(distances)), "nearby_charger_count_1000m": sum(d <= 1000 for d in distances), "location_type": place["location_type"], "data_quality_note": "OSM-mapped point; availability, permissions, grid capacity and site traffic are unverified."})
    result = pd.DataFrame(rows)
    if result.candidate_id.duplicated().any() or not result.latitude.between(-90,90).all() or not result.longitude.between(-180,180).all(): raise ValueError("Invalid candidate data")
    return result

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    traffic, candidates = prepare_traffic(), prepare_candidates()
    traffic.to_csv(OUT / "traffic_intervals.csv", index=False); candidates.to_csv(OUT / "candidates.csv", index=False)
    template = candidates.copy()
    for column in ["coverage_gap_score", "activity_score", "weighted_score", "reason"]: template[column] = ""
    template["major_unknowns"] = "Land access; parking permissions; grid capacity; EV utilization; site-specific traffic."
    template.to_csv(OUT / "candidate_scoring_template.csv", index=False)
    print(f"Wrote {len(traffic)} traffic observations and {len(candidates)} candidates.")

if __name__ == "__main__": main()
