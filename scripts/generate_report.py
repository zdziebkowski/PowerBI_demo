#!/usr/bin/env python3
"""Generate report.json for SuperAuto Power BI Dashboard.

Produces a complete report.json with all 4 pages (3 main + 1 tooltip)
as specified in REPORT_SPEC.md.
"""
import json
import uuid
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "SuperAuto.Report", "report.json")

# ─── Table aliases for Power Query references ────────────────────────────────
ALIAS: dict[str, str] = {
    "dim_date": "d",
    "dim_dealer": "dd",
    "dim_model": "dm",
    "fact_sales": "f",
    "Metric Parameter": "mp",
    "Discount Change": "dc",
}


def uid() -> str:
    return str(uuid.uuid4())


def from_e(table: str) -> dict:
    return {"Name": ALIAS[table], "Entity": table, "Type": 0}


def c_sel(table: str, col: str) -> dict:
    """Column select entry."""
    return {
        "Column": {
            "Expression": {"SourceRef": {"Source": ALIAS[table]}},
            "Property": col,
        },
        "Name": f"{table}.{col}",
    }


def m_sel(table: str, measure: str) -> dict:
    """Measure select entry."""
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Source": ALIAS[table]}},
            "Property": measure,
        },
        "Name": f"{table}.{measure}",
    }


def query(tables: list[str], selects: list[dict]) -> dict:
    """Build prototypeQuery."""
    unique_tables = list(dict.fromkeys(tables))
    return {
        "Version": 2,
        "From": [from_e(t) for t in unique_tables],
        "Select": selects,
    }


def _vc(
    x: int, y: int, w: int, h: int,
    visual_type: str,
    projections: dict,
    tables: list[str],
    selects: list[dict],
    objects: dict | None = None,
    z: int = 1000,
) -> dict:
    """Build a visual container dict."""
    inner = {
        "name": uid(),
        "layouts": [
            {
                "id": 0,
                "position": {
                    "x": 0, "y": 0, "z": z,
                    "width": w, "height": h,
                    "tabOrder": z,
                },
            }
        ],
        "singleVisual": {
            "visualType": visual_type,
            "projections": projections,
            "prototypeQuery": query(tables, selects),
            "objects": objects or {},
            "vcObjects": {},
        },
    }
    return {
        "id": uid(), "x": x, "y": y, "z": z, "width": w, "height": h,
        "config": json.dumps(inner, separators=(",", ":")),
        "filters": "[]",
    }


# ─── Visual builder helpers ──────────────────────────────────────────────────

def slicer(x, y, w, h, table, col, z=1000, mode=None):
    """Dropdown slicer by default; pass mode='Basic' for buttons/chiclet."""
    proj = {"Values": [{"queryRef": f"{table}.{col}"}]}
    objs = {}
    if mode:
        objs = {"data": [{"properties": {"mode": {"expr": {"Literal": {"Value": f"'{mode}'"}}}}}]}
    return _vc(x, y, w, h, "slicer", proj, [table], [c_sel(table, col)], objects=objs, z=z)


def card(x, y, w, h, table, measure, z=2000):
    proj = {"Values": [{"queryRef": f"{table}.{measure}"}]}
    return _vc(x, y, w, h, "card", proj, [table], [m_sel(table, measure)], z=z)


def line_chart(x, y, w, h, x_table, x_col, y_table, y_measure,
               leg_table=None, leg_col=None, y2_table=None, y2_measure=None, z=3000):
    tables = [x_table, y_table]
    selects = [c_sel(x_table, x_col), m_sel(y_table, y_measure)]
    proj = {
        "Category": [{"queryRef": f"{x_table}.{x_col}"}],
        "Y": [{"queryRef": f"{y_table}.{y_measure}"}],
    }
    if leg_table and leg_col:
        tables.append(leg_table)
        selects.append(c_sel(leg_table, leg_col))
        proj["Legend"] = [{"queryRef": f"{leg_table}.{leg_col}"}]
    if y2_table and y2_measure:
        if y2_table not in tables:
            tables.append(y2_table)
        selects.append(m_sel(y2_table, y2_measure))
        proj["Y2"] = [{"queryRef": f"{y2_table}.{y2_measure}"}]
    return _vc(x, y, w, h, "lineChart", proj, tables, selects, z=z)


def bar_chart(x, y, w, h, cat_table, cat_col, y_table, y_measure, z=3000):
    """Horizontal bar chart."""
    proj = {
        "Category": [{"queryRef": f"{cat_table}.{cat_col}"}],
        "Y": [{"queryRef": f"{y_table}.{y_measure}"}],
    }
    return _vc(x, y, w, h, "barChart", proj,
               [cat_table, y_table], [c_sel(cat_table, cat_col), m_sel(y_table, y_measure)], z=z)


def clustered_bar(x, y, w, h, cat_table, cat_col, measures, z=3000):
    """Clustered horizontal bar with multiple measures from fact_sales."""
    tables = list(dict.fromkeys([cat_table, "fact_sales"]))
    selects = [c_sel(cat_table, cat_col)] + [m_sel("fact_sales", m) for m in measures]
    proj = {
        "Category": [{"queryRef": f"{cat_table}.{cat_col}"}],
        "Y": [{"queryRef": f"fact_sales.{m}"} for m in measures],
    }
    return _vc(x, y, w, h, "clusteredBarChart", proj, tables, selects, z=z)


def clustered_col(x, y, w, h, cat_table, cat_col, y_entries, z=3000):
    """Clustered column chart. y_entries = list of (table, measure)."""
    tables = list(dict.fromkeys([cat_table] + [t for t, _ in y_entries]))
    selects = [c_sel(cat_table, cat_col)] + [m_sel(t, m) for t, m in y_entries]
    proj = {
        "Category": [{"queryRef": f"{cat_table}.{cat_col}"}],
        "Y": [{"queryRef": f"{t}.{m}"} for t, m in y_entries],
    }
    return _vc(x, y, w, h, "clusteredColumnChart", proj, tables, selects, z=z)


def filled_map(x, y, w, h, loc_table, loc_col, val_table, val_measure, z=3000):
    proj = {
        "Location": [{"queryRef": f"{loc_table}.{loc_col}"}],
        "ColorSaturation": [{"queryRef": f"{val_table}.{val_measure}"}],
    }
    tables = list(dict.fromkeys([loc_table, val_table]))
    selects = [c_sel(loc_table, loc_col), m_sel(val_table, val_measure)]
    return _vc(x, y, w, h, "filledMap", proj, tables, selects, z=z)


def matrix_visual(x, y, w, h, row_specs, value_specs, z=3000):
    """Matrix visual. row_specs = [(table, col), ...], value_specs = [(table, measure), ...]"""
    tables = list(dict.fromkeys([t for t, _ in row_specs] + [t for t, _ in value_specs]))
    selects = [c_sel(t, c) for t, c in row_specs] + [m_sel(t, m) for t, m in value_specs]
    proj = {
        "Rows": [{"queryRef": f"{t}.{c}"} for t, c in row_specs],
        "Values": [{"queryRef": f"{t}.{m}"} for t, m in value_specs],
    }
    return _vc(x, y, w, h, "matrix", proj, tables, selects, z=z)


def scatter_chart(x, y, w, h,
                  x_table, x_measure, y_table, y_measure,
                  size_table, size_measure,
                  legend_table, legend_col,
                  detail_table, detail_col, z=3000):
    tables = list(dict.fromkeys([
        x_table, y_table, size_table, legend_table, detail_table
    ]))
    selects = [
        m_sel(x_table, x_measure),
        m_sel(y_table, y_measure),
        m_sel(size_table, size_measure),
        c_sel(legend_table, legend_col),
        c_sel(detail_table, detail_col),
    ]
    proj = {
        "X": [{"queryRef": f"{x_table}.{x_measure}"}],
        "Y": [{"queryRef": f"{y_table}.{y_measure}"}],
        "Size": [{"queryRef": f"{size_table}.{size_measure}"}],
        "Legend": [{"queryRef": f"{legend_table}.{legend_col}"}],
        "Details": [{"queryRef": f"{detail_table}.{detail_col}"}],
    }
    return _vc(x, y, w, h, "scatterChart", proj, tables, selects, z=z)


def table_visual(x, y, w, h, col_specs, z=3000):
    """Table visual. col_specs = [(table, name, is_measure), ...]"""
    tables = list(dict.fromkeys([t for t, _, _ in col_specs]))
    selects = [m_sel(t, n) if is_m else c_sel(t, n) for t, n, is_m in col_specs]
    proj = {"Values": [{"queryRef": f"{t}.{n}"} for t, n, _ in col_specs]}
    return _vc(x, y, w, h, "tableEx", proj, tables, selects, z=z)


def decomp_tree(x, y, w, h, analyze_table, analyze_measure, explain_specs, z=3000):
    """Decomposition tree. explain_specs = [(table, col), ...]"""
    tables = list(dict.fromkeys([analyze_table] + [t for t, _ in explain_specs]))
    selects = [m_sel(analyze_table, analyze_measure)] + [c_sel(t, c) for t, c in explain_specs]
    proj = {
        "Analyze": [{"queryRef": f"{analyze_table}.{analyze_measure}"}],
        "ExplainBy": [{"queryRef": f"{t}.{c}"} for t, c in explain_specs],
    }
    return _vc(x, y, w, h, "decompositionTreeVisual", proj, tables, selects, z=z)


def textbox(x, y, w, h, text, z=500):
    inner = {
        "name": uid(),
        "layouts": [{"id": 0, "position": {"x": 0, "y": 0, "z": z, "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [{"properties": {"paragraphs": [{"textRuns": [{"value": text}], "name": "para0"}]}}]
            },
            "vcObjects": {},
        },
    }
    return {"id": uid(), "x": x, "y": y, "z": z, "width": w, "height": h,
            "config": json.dumps(inner, separators=(",", ":")), "filters": "[]"}


def action_button(x, y, w, h, label, z=500):
    inner = {
        "name": uid(),
        "layouts": [{"id": 0, "position": {"x": 0, "y": 0, "z": z, "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "actionButton",
            "objects": {
                "text": [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{label}'"}}}}}],
                "outline": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            },
            "vcObjects": {},
        },
    }
    return {"id": uid(), "x": x, "y": y, "z": z, "width": w, "height": h,
            "config": json.dumps(inner, separators=(",", ":")), "filters": "[]"}


def section(name, ordinal, visuals, width=1280, height=720, hidden=False):
    display_option = 2 if hidden else 0
    return {
        "id": uid(),
        "displayName": name,
        "displayOption": display_option,
        "height": height,
        "width": width,
        "ordinal": ordinal,
        "config": json.dumps({"relationships": [], "objects": {}}),
        "filters": "[]",
        "visualContainers": visuals,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: Executive Overview  (1280 × 720)
# ─────────────────────────────────────────────────────────────────────────────
p1: list[dict] = []

# Row 1 — Slicers + Dynamic Title  (y=10, h=42)
p1.append(slicer(10,   10, 175, 42, "dim_date",   "year"))
p1.append(slicer(195,  10, 175, 42, "dim_date",   "quarter"))
p1.append(slicer(380,  10, 175, 42, "dim_dealer", "region"))
p1.append(slicer(565,  10, 260, 42, "Metric Parameter", "Metric Parameter", mode="Basic"))
p1.append(card(835,    10, 435, 42, "fact_sales", "Dynamic Title Overview"))

# Row 2 — KPI Cards  (y=62, h=93)
kpis = [
    ("Net Revenue",       10),
    ("Total Profit",     210),
    ("Margin %",         410),
    ("Units Sold",       610),
    ("Avg Selling Price", 810),
    ("Avg Discount %",  1010),
]
for measure, x in kpis:
    w = 190 if x < 1000 else 260
    p1.append(card(x, 62, w, 93, "fact_sales", measure))

# Row 3 — Line chart + Filled map  (y=165, h=263)
p1.append(line_chart(10, 165, 630, 263,
                     "dim_date", "year_month",
                     "fact_sales", "Selected Metric"))
p1.append(filled_map(650, 165, 620, 263,
                     "dim_dealer", "country",
                     "fact_sales", "Selected Metric"))

# Row 4 — Bar chart by model + Clustered bar by region  (y=438, h=272)
p1.append(bar_chart(10, 438, 620, 272,
                    "dim_model", "model_name",
                    "fact_sales", "Selected Metric"))
p1.append(clustered_bar(640, 438, 630, 272,
                        "dim_dealer", "region",
                        ["Net Revenue", "Total Profit"]))

page1 = section("Executive Overview", 0, p1)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: Product & Dealer Analysis  (1280 × 720)
# ─────────────────────────────────────────────────────────────────────────────
p2: list[dict] = []

# Row 1 — Slicers + Dynamic Title
p2.append(slicer(10,  10, 240, 42, "dim_date",   "year"))
p2.append(slicer(260, 10, 240, 42, "dim_dealer", "region"))
p2.append(slicer(510, 10, 240, 42, "dim_model",  "segment"))
p2.append(card(760, 10, 510, 42, "fact_sales", "Dynamic Title Product"))

# Row 2 — Matrix + Scatter (y=62, h=278)
p2.append(matrix_visual(10, 62, 440, 278,
    row_specs=[
        ("dim_dealer", "region"),
        ("dim_dealer", "country"),
        ("dim_model",  "model_name"),
    ],
    value_specs=[
        ("fact_sales", "Net Revenue"),
        ("fact_sales", "Total Profit"),
        ("fact_sales", "Margin %"),
        ("fact_sales", "Units Sold"),
    ],
))

p2.append(scatter_chart(460, 62, 810, 278,
    x_table="fact_sales",    x_measure="Net Revenue",
    y_table="fact_sales",    y_measure="Margin %",
    size_table="fact_sales", size_measure="Units Sold",
    legend_table="dim_model", legend_col="model_name",
    detail_table="dim_dealer", detail_col="dealer_name",
))

# Row 3 — Top Dealers table + Decomposition Tree (y=350, h=360)
p2.append(table_visual(10, 350, 630, 360,
    col_specs=[
        ("dim_dealer", "dealer_name",       False),
        ("dim_dealer", "region",            False),
        ("dim_dealer", "dealer_tier",       False),
        ("fact_sales", "Net Revenue",       True),
        ("fact_sales", "Margin %",          True),
        ("fact_sales", "Dealer Revenue Rank", True),
    ],
))

p2.append(decomp_tree(650, 350, 620, 360,
    analyze_table="fact_sales", analyze_measure="Total Profit",
    explain_specs=[
        ("dim_dealer", "region"),
        ("dim_dealer", "country"),
        ("dim_model",  "model_name"),
        ("dim_dealer", "dealer_tier"),
    ],
))

page2 = section("Product & Dealer Analysis", 1, p2)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: Interactive Demo  (1280 × 720)
# ─────────────────────────────────────────────────────────────────────────────
p3: list[dict] = []

# ── Section A: What-If Discount Simulator ───────────────────────────────────
p3.append(textbox(10, 8, 620, 22, "What-If: Discount Simulator"))

# What-If slider slicer (Discount Change table)
p3.append(slicer(10, 35, 620, 42, "Discount Change", "Discount Change", mode="Between"))

# KPI cards (y=87)
p3.append(card(10,  87, 190, 90, "fact_sales", "Total Profit"))
p3.append(card(210, 87, 190, 90, "fact_sales", "Simulated Profit"))
p3.append(card(410, 87, 190, 90, "fact_sales", "Profit Impact"))

# Clustered column: Profit vs Simulated Profit by region
p3.append(clustered_col(650, 8, 620, 284,
    "dim_dealer", "region",
    [("fact_sales", "Total Profit"), ("fact_sales", "Simulated Profit")],
))

# ── Section B: Bookmarked Storytelling ──────────────────────────────────────
p3.append(textbox(10, 187, 620, 22, "Bookmarked Storytelling"))

# Story navigation buttons
p3.append(action_button(10,  215, 190, 40, "1. Global Overview"))
p3.append(action_button(210, 215, 190, 40, "2. Europe Problem"))
p3.append(action_button(410, 215, 190, 40, "3. EV Opportunity"))

# Story Chart 1: Revenue by region over time (BM_Story1 — visible by default)
p3.append(line_chart(10, 265, 780, 435,
                     "dim_date", "year_month",
                     "fact_sales", "Net Revenue",
                     leg_table="dim_dealer", leg_col="region"))

# Story Chart 2: Margin % by country (BM_Story2 — same position, toggled by bookmark)
p3.append(bar_chart(10, 265, 780, 435,
                    "dim_dealer", "country",
                    "fact_sales", "Margin %"))

# Story Chart 3: EV trend — Units Sold + Margin % dual axis (BM_Story3)
p3.append(line_chart(10, 265, 780, 435,
                     "dim_date", "year_month",
                     "fact_sales", "Units Sold",
                     y2_table="fact_sales", y2_measure="Margin %"))

# Narrative text box
p3.append(textbox(800, 265, 470, 435,
                  "Story navigation:\n\n"
                  "1. Global Overview — full revenue breakdown by region.\n\n"
                  "2. Europe Problem — European margin under pressure from discounts.\n\n"
                  "3. EV Opportunity — Electra growing fast; costs remain the challenge."))

page3 = section("Interactive Demo", 2, p3)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: Tooltip  (320 × 240, hidden)
# ─────────────────────────────────────────────────────────────────────────────
p4: list[dict] = []

# Row 1: 3 KPI cards
p4.append(card(5,   5,  95, 58, "fact_sales", "Net Revenue"))
p4.append(card(105, 5,  95, 58, "fact_sales", "Total Profit"))
p4.append(card(205, 5, 110, 58, "fact_sales", "Margin %"))

# Sparkline (mini line chart — no axes, no legend)
p4.append(line_chart(5, 68, 310, 82,
                     "dim_date", "year_month",
                     "fact_sales", "Net Revenue"))

# Row 3: 2 KPI cards
p4.append(card(5,   155, 150, 76, "fact_sales", "Avg Discount %"))
p4.append(card(160, 155, 155, 76, "fact_sales", "Units Sold"))

page4 = section("Tooltip", 3, p4, width=320, height=240, hidden=True)


# ─────────────────────────────────────────────────────────────────────────────
# Assemble report
# ─────────────────────────────────────────────────────────────────────────────
report = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "resourcePackages": [],
    "sections": [page1, page2, page3, page4],
    "config": json.dumps({"relationships": [], "objects": {}}),
    "filters": "[]",
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"OK report.json written -> {OUTPUT_PATH}")
print(f"   Pages: {len(report['sections'])}")
for s in report["sections"]:
    vc_count = len(s["visualContainers"])
    hidden = " [hidden]" if s["displayOption"] == 2 else ""
    print(f"   · {s['displayName']}{hidden}: {vc_count} visuals")
