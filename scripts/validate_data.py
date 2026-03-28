"""
validate_data.py — Validation script for SuperAuto synthetic data.
Checks referential integrity, calculation consistency, value ranges,
and prints summary statistics.
Exit code 0 = OK, exit code 1 = errors found.
"""

import csv
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TOLERANCE = 0.01


def load_csv(filename: str) -> list[dict]:
    """Load a CSV file and return a list of row dicts."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------

def check_referential_integrity(
    fact: list[dict],
    dim_date: list[dict],
    dim_dealer: list[dict],
    dim_model: list[dict],
) -> list[str]:
    """Return list of error messages for referential integrity violations."""
    errors: list[str] = []

    valid_dates = {r["date"] for r in dim_date}
    valid_dealers = {r["dealer_id"] for r in dim_dealer}
    valid_models = {r["model_id"] for r in dim_model}

    missing_dates: set[str] = set()
    missing_dealers: set[str] = set()
    missing_models: set[str] = set()

    for row in fact:
        if row["date"] not in valid_dates:
            missing_dates.add(row["date"])
        if row["dealer_id"] not in valid_dealers:
            missing_dealers.add(row["dealer_id"])
        if row["model_id"] not in valid_models:
            missing_models.add(row["model_id"])

    if missing_dates:
        errors.append(f"Missing dates in dim_date: {sorted(missing_dates)[:5]}")
    if missing_dealers:
        errors.append(f"Missing dealer_ids in dim_dealer: {sorted(missing_dealers)[:5]}")
    if missing_models:
        errors.append(f"Missing model_ids in dim_model: {sorted(missing_models)[:5]}")

    return errors


# ---------------------------------------------------------------------------
# Calculation consistency
# ---------------------------------------------------------------------------

def check_calculations(fact: list[dict]) -> list[str]:
    """Return list of error messages for calculation inconsistencies."""
    errors: list[str] = []
    bad_rows = {
        "gross_revenue": 0,
        "discount_amount": 0,
        "net_revenue": 0,
        "total_cost": 0,
        "profit": 0,
        "margin_pct": 0,
    }

    for row in fact:
        units = float(row["units_sold"])
        unit_price = float(row["unit_price"])
        gross_revenue = float(row["gross_revenue"])
        discount_pct = float(row["discount_pct"])
        discount_amount = float(row["discount_amount"])
        net_revenue = float(row["net_revenue"])
        unit_cost = float(row["unit_cost"])
        total_cost = float(row["total_cost"])
        profit = float(row["profit"])
        margin_pct = float(row["margin_pct"])

        if abs(gross_revenue - units * unit_price) > TOLERANCE:
            bad_rows["gross_revenue"] += 1
        if abs(discount_amount - gross_revenue * discount_pct) > TOLERANCE:
            bad_rows["discount_amount"] += 1
        if abs(net_revenue - (gross_revenue - discount_amount)) > TOLERANCE:
            bad_rows["net_revenue"] += 1
        if abs(total_cost - units * unit_cost) > TOLERANCE:
            bad_rows["total_cost"] += 1
        if abs(profit - (net_revenue - total_cost)) > TOLERANCE:
            bad_rows["profit"] += 1
        if net_revenue != 0:
            expected_margin = profit / net_revenue
            if abs(margin_pct - expected_margin) > TOLERANCE:
                bad_rows["margin_pct"] += 1

    for field, count in bad_rows.items():
        if count > 0:
            errors.append(f"Calculation mismatch in '{field}': {count} rows")

    return errors


# ---------------------------------------------------------------------------
# Value ranges
# ---------------------------------------------------------------------------

def check_ranges(fact: list[dict]) -> list[str]:
    """Return list of error messages for out-of-range values."""
    errors: list[str] = []
    bad_units = bad_price = bad_discount = bad_margin = 0

    for row in fact:
        units = int(row["units_sold"])
        unit_price = float(row["unit_price"])
        discount_pct = float(row["discount_pct"])
        margin_pct = float(row["margin_pct"])

        if units <= 0:
            bad_units += 1
        if unit_price <= 0:
            bad_price += 1
        if not (0 <= discount_pct <= 0.30):
            bad_discount += 1
        if not (-0.15 <= margin_pct <= 0.40):
            bad_margin += 1

    if bad_units:
        errors.append(f"units_sold <= 0: {bad_units} rows")
    if bad_price:
        errors.append(f"unit_price <= 0: {bad_price} rows")
    if bad_discount:
        errors.append(f"discount_pct out of [0, 0.30]: {bad_discount} rows")
    if bad_margin:
        errors.append(f"margin_pct out of [-0.15, 0.40]: {bad_margin} rows")

    return errors


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def print_summary(
    fact: list[dict],
    dim_dealer: list[dict],
    dim_date: list[dict],
    dim_model: list[dict],
) -> None:
    """Print summary statistics to stdout."""
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    # Row counts
    print(f"\nRow counts:")
    print(f"  dim_date:    {len(dim_date):>8,}")
    print(f"  dim_dealer:  {len(dim_dealer):>8,}")
    print(f"  dim_model:   {len(dim_model):>8,}")
    print(f"  fact_sales:  {len(fact):>8,}")

    # Aggregate financials
    total_revenue = sum(float(r["net_revenue"]) for r in fact)
    total_profit = sum(float(r["profit"]) for r in fact)
    total_gross = sum(float(r["gross_revenue"]) for r in fact)
    avg_margin = total_profit / total_revenue if total_revenue else 0

    print(f"\nFinancials:")
    print(f"  Gross Revenue:  € {total_gross:>18,.2f}")
    print(f"  Net Revenue:    € {total_revenue:>18,.2f}")
    print(f"  Total Profit:   € {total_profit:>18,.2f}")
    print(f"  Avg Margin %:   {avg_margin * 100:>17.2f}%")

    # Build dealer lookup
    dealer_region: dict[str, str] = {r["dealer_id"]: r["region"] for r in dim_dealer}
    dealer_model: dict[str, str] = {}  # model_id -> model_name
    for m in dim_model:
        dealer_model[m["model_id"]] = m["model_name"]

    # Revenue by region
    region_revenue: dict[str, float] = {}
    for row in fact:
        region = dealer_region.get(row["dealer_id"], "Unknown")
        region_revenue[region] = region_revenue.get(region, 0.0) + float(row["net_revenue"])

    print(f"\nRevenue by Region:")
    for region, rev in sorted(region_revenue.items(), key=lambda x: -x[1]):
        pct = rev / total_revenue * 100 if total_revenue else 0
        print(f"  {region:<20} € {rev:>15,.0f}  ({pct:>5.1f}%)")

    # Revenue by model
    model_revenue: dict[str, float] = {}
    for row in fact:
        name = dealer_model.get(row["model_id"], row["model_id"])
        model_revenue[name] = model_revenue.get(name, 0.0) + float(row["net_revenue"])

    print(f"\nRevenue by Model:")
    for model, rev in sorted(model_revenue.items(), key=lambda x: -x[1]):
        pct = rev / total_revenue * 100 if total_revenue else 0
        print(f"  {model:<25} € {rev:>15,.0f}  ({pct:>5.1f}%)")

    # Top 5 and Bottom 5 dealers by margin
    dealer_profit: dict[str, float] = {}
    dealer_revenue: dict[str, float] = {}
    for row in fact:
        did = row["dealer_id"]
        dealer_profit[did] = dealer_profit.get(did, 0.0) + float(row["profit"])
        dealer_revenue[did] = dealer_revenue.get(did, 0.0) + float(row["net_revenue"])

    dealer_name_map: dict[str, str] = {r["dealer_id"]: r["dealer_name"] for r in dim_dealer}

    dealer_margins = []
    for did, rev in dealer_revenue.items():
        if rev > 0:
            margin = dealer_profit[did] / rev
            dealer_margins.append((did, dealer_name_map.get(did, did), margin))

    dealer_margins.sort(key=lambda x: -x[2])

    print(f"\nTop 5 Dealers by Margin %:")
    for did, name, margin in dealer_margins[:5]:
        print(f"  {did} {name:<35} {margin * 100:>6.2f}%")

    print(f"\nBottom 5 Dealers by Margin %:")
    for did, name, margin in dealer_margins[-5:]:
        print(f"  {did} {name:<35} {margin * 100:>6.2f}%")

    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all validations and print results."""
    print("Loading data files...")
    dim_date = load_csv("dim_date.csv")
    dim_dealer = load_csv("dim_dealer.csv")
    dim_model = load_csv("dim_model.csv")
    fact = load_csv("fact_sales.csv")

    all_errors: list[str] = []

    print("Checking referential integrity...")
    all_errors += check_referential_integrity(fact, dim_date, dim_dealer, dim_model)

    print("Checking calculation consistency...")
    all_errors += check_calculations(fact)

    print("Checking value ranges...")
    all_errors += check_ranges(fact)

    if all_errors:
        print("\nVALIDATION FAILED:")
        for err in all_errors:
            print(f"  [ERROR] {err}")
        print_summary(fact, dim_dealer, dim_date, dim_model)
        sys.exit(1)
    else:
        print("\nAll checks passed.")
        print_summary(fact, dim_dealer, dim_date, dim_model)
        sys.exit(0)


if __name__ == "__main__":
    main()
