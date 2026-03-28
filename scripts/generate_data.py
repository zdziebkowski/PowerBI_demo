"""
generate_data.py — Synthetic data generator for SuperAuto Global Wholesale Sales Dashboard.
Generates 4 CSV files: dim_date, dim_dealer, dim_model, fact_sales.
Uses only Python stdlib. Seed: 42 for reproducibility.
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def ensure_output_dir() -> None:
    """Create output directory if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# dim_date
# ---------------------------------------------------------------------------

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_quarter(month: int) -> str:
    """Return quarter label for a given month number."""
    return f"Q{(month - 1) // 3 + 1}"


def generate_dim_date(start: date, end: date) -> list[dict]:
    """Generate one row per calendar day between start and end (inclusive)."""
    rows = []
    current = start
    while current <= end:
        rows.append({
            "date": current.strftime("%Y-%m-%d"),
            "year": current.year,
            "quarter": get_quarter(current.month),
            "month": current.month,
            "month_name": MONTH_NAMES[current.month - 1],
            "year_month": current.strftime("%Y-%m"),
            "day_of_week": DAY_NAMES[current.weekday()],
            "is_weekend": current.weekday() >= 5,
        })
        current += timedelta(days=1)
    return rows


def write_dim_date() -> None:
    """Write dim_date.csv."""
    rows = generate_dim_date(date(2024, 1, 1), date(2025, 12, 31))
    path = os.path.join(OUTPUT_DIR, "dim_date.csv")
    fieldnames = ["date", "year", "quarter", "month", "month_name", "year_month", "day_of_week", "is_weekend"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  dim_date.csv: {len(rows)} rows")


# ---------------------------------------------------------------------------
# dim_dealer
# ---------------------------------------------------------------------------

# (country, region, cities, count)
DEALER_DISTRIBUTION = [
    # Europe (35)
    ("Germany",      "Europe",        ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne", "Stuttgart", "Dusseldorf", "Leipzig"], 8),
    ("France",       "Europe",        ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Bordeaux"], 6),
    ("UK",           "Europe",        ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Bristol"], 6),
    ("Spain",        "Europe",        ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao"], 5),
    ("Italy",        "Europe",        ["Rome", "Milan", "Naples", "Turin", "Florence"], 5),
    ("Poland",       "Europe",        ["Warsaw", "Krakow", "Wroclaw"], 3),
    ("Netherlands",  "Europe",        ["Amsterdam", "Rotterdam"], 2),
    # North America (25)
    ("USA",          "North America", ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", "Denver", "Seattle", "Nashville", "Portland", "Las Vegas", "Boston"], 18),
    ("Canada",       "North America", ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"], 5),
    ("Mexico",       "North America", ["Mexico City", "Guadalajara"], 2),
    # South America (12)
    ("Brazil",       "South America", ["Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Curitiba", "Fortaleza"], 6),
    ("Argentina",    "South America", ["Buenos Aires", "Cordoba", "Rosario"], 3),
    ("Colombia",     "South America", ["Bogota", "Medellin"], 2),
    ("Chile",        "South America", ["Santiago"], 1),
    # Asia-Pacific (18)
    ("China",        "Asia-Pacific",  ["Shanghai", "Beijing", "Guangzhou", "Shenzhen", "Chengdu", "Hangzhou"], 6),
    ("Japan",        "Asia-Pacific",  ["Tokyo", "Osaka", "Yokohama", "Nagoya"], 4),
    ("India",        "Asia-Pacific",  ["Mumbai", "Delhi", "Bangalore", "Hyderabad"], 4),
    ("Australia",    "Asia-Pacific",  ["Sydney", "Melbourne", "Brisbane"], 3),
    ("South Korea",  "Asia-Pacific",  ["Seoul"], 1),
    # MEA (10)
    ("UAE",          "MEA",           ["Dubai", "Abu Dhabi", "Sharjah"], 3),
    ("Saudi Arabia", "MEA",           ["Riyadh", "Jeddah"], 2),
    ("South Africa", "MEA",           ["Johannesburg", "Cape Town", "Durban"], 3),
    ("Nigeria",      "MEA",           ["Lagos"], 1),
    ("Egypt",        "MEA",           ["Cairo"], 1),
]

NAME_PATTERNS = [
    "{city} Auto Group",
    "{city} Motors",
    "{country} Premium Cars",
    "{city} Automotive",
    "{country} Auto Dealers",
    "{city} Car Center",
]


def pick_dealer_name(city: str, country: str) -> str:
    """Generate a dealer name from available patterns."""
    pattern = random.choice(NAME_PATTERNS)
    return pattern.format(city=city, country=country)


def assign_tier() -> str:
    """Assign dealer tier: Premium ~20%, Standard ~50%, Local ~30%."""
    r = random.random()
    if r < 0.20:
        return "Premium"
    elif r < 0.70:
        return "Standard"
    return "Local"


def generate_dim_dealer() -> list[dict]:
    """Generate 100 dealer rows."""
    rows = []
    dealer_num = 1
    for country, region, cities, count in DEALER_DISTRIBUTION:
        for i in range(count):
            city = cities[i % len(cities)]
            dealer_id = f"D{dealer_num:03d}"
            rows.append({
                "dealer_id": dealer_id,
                "dealer_name": pick_dealer_name(city, country),
                "country": country,
                "region": region,
                "city": city,
                "dealer_tier": assign_tier(),
            })
            dealer_num += 1
    return rows


def write_dim_dealer() -> None:
    """Write dim_dealer.csv."""
    rows = generate_dim_dealer()
    path = os.path.join(OUTPUT_DIR, "dim_dealer.csv")
    fieldnames = ["dealer_id", "dealer_name", "country", "region", "city", "dealer_tier"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  dim_dealer.csv: {len(rows)} rows")


# ---------------------------------------------------------------------------
# dim_model
# ---------------------------------------------------------------------------

MODELS = [
    {"model_id": "M01", "model_name": "SuperAuto City",   "segment": "Compact",     "fuel_type": "Petrol",   "vehicle_class": "Economy"},
    {"model_id": "M02", "model_name": "SuperAuto Urban",  "segment": "Hatchback",   "fuel_type": "Petrol",   "vehicle_class": "Economy"},
    {"model_id": "M03", "model_name": "SuperAuto Family", "segment": "Sedan",       "fuel_type": "Hybrid",   "vehicle_class": "Mid-Range"},
    {"model_id": "M04", "model_name": "SuperAuto Tourer", "segment": "SUV",         "fuel_type": "Diesel",   "vehicle_class": "Mid-Range"},
    {"model_id": "M05", "model_name": "SuperAuto Cargo",  "segment": "Van",         "fuel_type": "Diesel",   "vehicle_class": "Commercial"},
    {"model_id": "M06", "model_name": "SuperAuto Electra","segment": "EV",          "fuel_type": "Electric", "vehicle_class": "Premium"},
    {"model_id": "M07", "model_name": "SuperAuto Falcon", "segment": "Premium SUV", "fuel_type": "Hybrid",   "vehicle_class": "Premium"},
]


def write_dim_model() -> None:
    """Write dim_model.csv."""
    path = os.path.join(OUTPUT_DIR, "dim_model.csv")
    fieldnames = ["model_id", "model_name", "segment", "fuel_type", "vehicle_class"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(MODELS)
    print(f"  dim_model.csv: {len(MODELS)} rows")


# ---------------------------------------------------------------------------
# fact_sales helpers
# ---------------------------------------------------------------------------

# Base price ranges per model_id
BASE_PRICE_RANGES: dict[str, tuple[int, int]] = {
    "M01": (18_000, 22_000),
    "M02": (20_000, 25_000),
    "M03": (28_000, 35_000),
    "M04": (35_000, 45_000),
    "M05": (25_000, 32_000),
    "M06": (42_000, 55_000),
    "M07": (55_000, 72_000),
}

# Unit cost as fraction of price
COST_PCT_RANGES: dict[str, tuple[float, float]] = {
    "M01": (0.72, 0.78),  # Economy
    "M02": (0.72, 0.78),  # Economy
    "M03": (0.68, 0.74),  # Mid-Range
    "M04": (0.68, 0.74),  # Mid-Range
    "M05": (0.75, 0.80),  # Commercial
    "M06": (0.80, 0.88),  # Premium EV (high battery cost)
    "M07": (0.62, 0.70),  # Premium (best margin)
}

# Units sold range per vehicle_class
UNITS_RANGES: dict[str, tuple[int, int]] = {
    "Economy":    (5, 25),
    "Mid-Range":  (3, 15),
    "Commercial": (2, 10),
    "Premium":    (1, 5),
}

MODEL_CLASS: dict[str, str] = {m["model_id"]: m["vehicle_class"] for m in MODELS}

# Discount base range per tier
DISCOUNT_RANGES: dict[str, tuple[float, float]] = {
    "Premium":  (0.08, 0.15),
    "Standard": (0.03, 0.08),
    "Local":    (0.00, 0.04),
}

# Models that are "premium" for discount multiplier
PREMIUM_MODELS = {"M06", "M07"}
ECONOMY_MODELS = {"M01", "M02"}

# Seasonality volume multipliers per quarter
SEASON_MULT: dict[str, float] = {
    "Q1": 1.05,
    "Q2": 0.90,
    "Q3": 0.80,
    "Q4": 1.25,
}

# Regional price and volume multipliers
REGION_PRICE_MULT: dict[str, float] = {
    "Europe":        1.00,
    "North America": 1.08,
    "Asia-Pacific":  0.92,
    "South America": 1.00,
    "MEA":           1.00,
}

REGION_VOLUME_MULT: dict[str, float] = {
    "Europe":        1.00,
    "North America": 1.00,
    "Asia-Pacific":  1.00,
    "South America": 0.70,
    "MEA":           0.50,
}

REGION_DISCOUNT_ADD: dict[str, float] = {
    "Europe":        0.02,
    "North America": -0.01,
    "Asia-Pacific":  0.00,
    "South America": 0.00,
    "MEA":           -0.01,
}


def apac_volume_mult(d: date) -> float:
    """Asia-Pacific growing volume in 2025."""
    if d.year == 2025:
        return 1.20
    return 1.00


def electra_trend_mult(d: date) -> float:
    """EV (Electra M06) trend multiplier: starts at 1.0 in 2024-Q1, +0.05 each quarter."""
    start_quarter = 0  # 2024-Q1 = 0
    year_offset = d.year - 2024
    quarter_num = (d.month - 1) // 3  # 0-based
    total_quarters = year_offset * 4 + quarter_num
    return 1.0 + 0.05 * total_quarters


def compute_units(model_id: str, tier: str, region: str, d: date, quarter: str) -> int:
    """Compute units sold for a transaction."""
    vehicle_class = MODEL_CLASS[model_id]
    lo, hi = UNITS_RANGES[vehicle_class]
    base = random.randint(lo, hi)

    # Seasonality
    mult = SEASON_MULT[quarter]

    # Regional volume
    mult *= REGION_VOLUME_MULT[region]
    if region == "Asia-Pacific":
        mult *= apac_volume_mult(d)

    # Electra trend
    if model_id == "M06":
        mult *= electra_trend_mult(d)

    units = max(1, round(base * mult))
    return units


def compute_discount(model_id: str, tier: str, region: str) -> float:
    """Compute discount_pct for a transaction."""
    lo, hi = DISCOUNT_RANGES[tier]
    disc = random.uniform(lo, hi)

    # Premium models: lower discount
    if model_id in PREMIUM_MODELS:
        disc *= 0.6
    # Economy models: higher discount
    elif model_id in ECONOMY_MODELS:
        disc *= 1.2

    # Regional adjustment
    disc += REGION_DISCOUNT_ADD[region]
    disc = max(0.0, min(0.30, disc))
    return round(disc, 4)


# ---------------------------------------------------------------------------
# fact_sales
# ---------------------------------------------------------------------------

def generate_fact_sales(dealers: list[dict]) -> list[dict]:
    """Generate fact_sales rows for every business day in 2024-2025."""
    rows = []
    sales_num = 1

    # Build a lookup for dealer info
    dealer_map: dict[str, dict] = {d["dealer_id"]: d for d in dealers}
    dealer_ids = [d["dealer_id"] for d in dealers]

    current = date(2024, 1, 1)
    end = date(2025, 12, 31)

    while current <= end:
        # Only business days (Mon-Fri)
        if current.weekday() < 5:
            quarter = get_quarter(current.month)
            num_transactions = random.randint(40, 80)

            for _ in range(num_transactions):
                dealer_id = random.choice(dealer_ids)
                dealer = dealer_map[dealer_id]
                model = random.choice(MODELS)
                model_id = model["model_id"]

                region = dealer["region"]
                tier = dealer["dealer_tier"]

                # Unit price
                p_lo, p_hi = BASE_PRICE_RANGES[model_id]
                base_price = random.uniform(p_lo, p_hi)
                base_price *= REGION_PRICE_MULT[region]
                unit_price = round(base_price, 2)

                # Unit cost
                c_lo, c_hi = COST_PCT_RANGES[model_id]
                cost_pct = random.uniform(c_lo, c_hi)
                unit_cost = round(unit_price * cost_pct, 2)

                # Units
                units_sold = compute_units(model_id, tier, region, current, quarter)

                # Discount
                discount_pct = compute_discount(model_id, tier, region)

                # Derived financials
                gross_revenue = round(units_sold * unit_price, 2)
                discount_amount = round(gross_revenue * discount_pct, 2)
                net_revenue = round(gross_revenue - discount_amount, 2)
                total_cost = round(units_sold * unit_cost, 2)
                profit = round(net_revenue - total_cost, 2)
                margin_pct = round(profit / net_revenue, 4) if net_revenue != 0 else 0.0

                rows.append({
                    "sales_id":        f"S{sales_num:05d}",
                    "date":            current.strftime("%Y-%m-%d"),
                    "dealer_id":       dealer_id,
                    "model_id":        model_id,
                    "units_sold":      units_sold,
                    "unit_price":      unit_price,
                    "gross_revenue":   gross_revenue,
                    "discount_pct":    discount_pct,
                    "discount_amount": discount_amount,
                    "net_revenue":     net_revenue,
                    "unit_cost":       unit_cost,
                    "total_cost":      total_cost,
                    "profit":          profit,
                    "margin_pct":      margin_pct,
                })
                sales_num += 1

        current += timedelta(days=1)

    return rows


def write_fact_sales(dealers: list[dict]) -> None:
    """Write fact_sales.csv."""
    rows = generate_fact_sales(dealers)
    path = os.path.join(OUTPUT_DIR, "fact_sales.csv")
    fieldnames = [
        "sales_id", "date", "dealer_id", "model_id",
        "units_sold", "unit_price", "gross_revenue",
        "discount_pct", "discount_amount", "net_revenue",
        "unit_cost", "total_cost", "profit", "margin_pct",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  fact_sales.csv: {len(rows)} rows")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate all 4 CSV files."""
    ensure_output_dir()
    print("Generating data files...")
    write_dim_date()
    dealers = generate_dim_dealer()

    # Write dim_dealer manually (reuse generated list for fact_sales)
    path = os.path.join(OUTPUT_DIR, "dim_dealer.csv")
    fieldnames = ["dealer_id", "dealer_name", "country", "region", "city", "dealer_tier"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dealers)
    print(f"  dim_dealer.csv: {len(dealers)} rows")

    write_dim_model()
    write_fact_sales(dealers)
    print("Done.")


if __name__ == "__main__":
    main()
