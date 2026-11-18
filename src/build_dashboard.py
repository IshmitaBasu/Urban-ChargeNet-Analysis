"""Build the final Excel workbook and a matching dashboard preview image."""
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard"
OUT.mkdir(exist_ok=True)
traffic = pd.read_csv(ROOT / "data" / "processed" / "traffic_intervals.csv")
candidates = pd.read_csv(ROOT / "data" / "processed" / "candidates.csv")

# Explicit analyst-assessed values. They are editable in the Candidates sheet.
scores = {"C1": (4, 5, "Mapped mall; activity context is stronger than the two parking-only records."),
          "C2": (4, 2, "Mapped parking; no additional activity or access detail in the export."),
          "C3": (4, 3, "Mapped parking close to the mall; site access is unverified.")}
candidates["coverage_gap_score"] = candidates.candidate_id.map(lambda x: scores[x][0])
candidates["activity_score"] = candidates.candidate_id.map(lambda x: scores[x][1])
candidates["weighted_score"] = candidates.candidate_id.map(lambda x: .6*scores[x][0] + .4*scores[x][1])
candidates["reason"] = candidates.candidate_id.map(lambda x: scores[x][2])
candidates["major_unknowns"] = "Land access; parking permission; grid capacity; EV use; site traffic."
candidates = candidates.sort_values("weighted_score", ascending=False).reset_index(drop=True)

book = Workbook()
ws = book.active; ws.title = "Traffic_Data"
ws.append(["date", "time_or_interval", "vehicle_count", "green_phase_seconds"])
for row in traffic.itertuples(index=False, name=None): ws.append(row)
tab = Table(displayName="TrafficData", ref=f"A1:D{ws.max_row}"); tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(tab); ws.freeze_panes = "A2"; ws.column_dimensions["A"].width = 14; ws.column_dimensions["B"].width = 29; ws.column_dimensions["C"].width = 16; ws.column_dimensions["D"].width = 21

ws = book.create_sheet("Candidates")
headers = list(candidates.columns); ws.append(headers)
for row in candidates.itertuples(index=False, name=None): ws.append(row)
tab = Table(displayName="CandidatesData", ref=f"A1:{chr(64+len(headers))}{ws.max_row}"); tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium4", showRowStripes=True)
ws.add_table(tab); ws.freeze_panes = "A2"
for column, width in {"A":12,"B":34,"C":12,"D":12,"E":22,"F":27,"G":22,"H":16,"I":52,"J":22,"K":16,"L":18,"M":64,"N":58}.items(): ws.column_dimensions[column].width = width
ws.conditional_formatting.add("L2:L4", ColorScaleRule(start_type="min", start_color="F8696B", mid_type="percentile", mid_value=50, mid_color="FFEB84", end_type="max", end_color="63BE7B"))

dash = book.create_sheet("Dashboard")
dark, teal, pale = "17324D", "00A6A6", "EAF4F4"
dash.sheet_view.showGridLines = False
for col, width in {"A":4,"B":28,"C":18,"D":18,"E":18,"F":4,"G":26,"H":18,"I":18,"J":18}.items(): dash.column_dimensions[col].width = width
dash.merge_cells("B2:J2"); dash["B2"] = "Urban ChargeNet | Webel More, Kolkata"; dash["B2"].font = Font(size=20, bold=True, color="FFFFFF"); dash["B2"].fill = PatternFill("solid", fgColor=dark); dash["B2"].alignment = Alignment(horizontal="center")
dash.merge_cells("B3:J3"); dash["B3"] = "Exploratory screening — observed intersection traffic plus mapped OSM locations"; dash["B3"].font = Font(italic=True, color="FFFFFF"); dash["B3"].fill = PatternFill("solid", fgColor=dark); dash["B3"].alignment = Alignment(horizontal="center")
dash["B5"] = "TOTAL OBSERVED VEHICLES"; dash["C5"] = int(traffic.vehicle_count.sum()); dash["E5"] = "PEAK OBSERVED PHASE"; peak = traffic.loc[traffic.vehicle_count.idxmax()]; dash["F5"] = f"{peak.vehicle_count} vehicles"; dash["B6"] = "Across 116 observed green phases"; dash["C6"] = "Not a daily total"; dash["E6"] = f"{peak.green_phase_seconds:.0f}-second green phase"; dash["F6"] = str(peak.time_or_interval)
for cell in ["B5","E5"]: dash[cell].font=Font(bold=True,color="FFFFFF"); dash[cell].fill=PatternFill("solid",fgColor=teal)
for cell in ["C5","F5"]: dash[cell].font=Font(size=16,bold=True,color=dark)

dash["B9"] = "Candidate"; dash["C9"] = "Score"; dash["D9"] = "Nearest mapped charger"; dash["E9"] = "Decision note"
for cell in dash[9][1:5]: cell.font=Font(bold=True,color="FFFFFF"); cell.fill=PatternFill("solid",fgColor=dark)
for i, row in candidates.iterrows():
    r = 10+i; dash.cell(r,2,row.candidate_name); dash.cell(r,3,row.weighted_score); dash.cell(r,4,f"{row.nearest_charger_distance_m:,} m straight-line"); dash.cell(r,5,row.reason)
dash["B14"] = "Traffic chart uses all observed green phases, ordered as supplied. Their durations differ, so this is not an hourly traffic profile."; dash.merge_cells("B14:J14"); dash["B14"].alignment=Alignment(wrap_text=True); dash["B14"].font=Font(italic=True,color="666666")

chart = BarChart(); chart.type="col"; chart.style=10; chart.title="Observed vehicle counts by green phase"; chart.y_axis.title="Vehicles"; chart.x_axis.title="Observation order"; chart.height=8; chart.width=18
chart.add_data(Reference(book["Traffic_Data"], min_col=3, min_row=1, max_row=book["Traffic_Data"].max_row), titles_from_data=True); dash.add_chart(chart, "B16")
score_chart = BarChart(); score_chart.type="bar"; score_chart.style=11; score_chart.title="Candidate weighted scores"; score_chart.y_axis.title="Candidate"; score_chart.x_axis.title="Score (out of 5)"; score_chart.height=7; score_chart.width=10
score_chart.add_data(Reference(dash, min_col=3, min_row=9, max_row=12), titles_from_data=True); score_chart.set_categories(Reference(dash,min_col=2,min_row=10,max_row=12)); dash.add_chart(score_chart,"G9")
dash.merge_cells("B33:J33"); dash["B33"]="Exploratory study | Single-intersection traffic data | OSM coverage may be incomplete | No EV utilization or financial validation"; dash["B33"].font=Font(size=9,italic=True,color="666666"); dash["B33"].alignment=Alignment(horizontal="center")

book.calculation.fullCalcOnLoad = True
book.calculation.forceFullCalc = True
book.save(OUT / "Urban_ChargeNet_Kolkata.xlsx")

# Compact preview for README; it mirrors the dashboard's principal results.
image = Image.new("RGB", (1400, 800), "white"); draw = ImageDraw.Draw(image)
font = ImageFont.truetype("arial.ttf", 22); title = ImageFont.truetype("arialbd.ttf", 34); big = ImageFont.truetype("arialbd.ttf", 30)
draw.rectangle((0,0,1400,110), fill="#17324D"); draw.text((45,28), "Urban ChargeNet | Webel More, Kolkata", font=title, fill="white"); draw.text((45,74), "Exploratory screening — observed intersection traffic plus mapped OSM locations", font=font, fill="white")
draw.rectangle((45,145,630,275), fill="#EAF4F4"); draw.text((65,165), "TOTAL OBSERVED VEHICLES", font=font, fill="#17324D"); draw.text((65,205), str(int(traffic.vehicle_count.sum())), font=big, fill="#00A6A6")
draw.rectangle((690,145,1355,275), fill="#EAF4F4"); draw.text((710,165), "PEAK OBSERVED PHASE", font=font, fill="#17324D"); draw.text((710,205), f"{peak.vehicle_count} vehicles / {peak.green_phase_seconds:.0f} seconds", font=big, fill="#00A6A6")
draw.text((45,320), "Provisional candidate ranking", font=big, fill="#17324D")
for i, row in candidates.iterrows():
    y=380+i*105; draw.rectangle((45,y,1355,y+75), fill="#F3F7F7"); draw.text((65,y+20), f"{i+1}. {row.candidate_name}",font=font,fill="#17324D"); draw.text((650,y+20), f"Score: {row.weighted_score:.1f}/5",font=font,fill="#17324D"); draw.text((950,y+20),f"Nearest mapped charger: {row.nearest_charger_distance_m:,} m",font=font,fill="#17324D")
draw.text((45,740), "Single-intersection traffic data | OSM coverage may be incomplete | No EV utilization or financial validation", font=font, fill="#666666")
image.save(OUT / "dashboard.png")
print("Created workbook and dashboard preview.")
