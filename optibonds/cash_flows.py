from datetime import date
from math import floor
from optibonds.models import BondSimple


def bond_cash_flows(
    bond: BondSimple,
    settlement_date: date,
) -> list[tuple[date, float, str]]:
    """
    Returns a list of (date, cashflow, description)
    """
    cashflows = []

    total_nominal = bond.num_lots * bond.minimum_lot

    # Initial investment (outflow)
    invested = bond.capital_invested
    cashflows.append((
        settlement_date,
        -invested,
        f"Buy {bond.isin}"
    ))

    # Number of coupon payments
    num_coupons = floor(bond.maturity_years)

    annual_coupon = total_nominal * bond.current_coupon_rate

    for i in range(1, num_coupons + 1):
        coupon_date = settlement_date.replace(year=settlement_date.year + i)
        cashflows.append((
            coupon_date,
            annual_coupon,
            f"Coupon {bond.isin}"
        ))

    # Maturity (principal + last coupon if applicable)
    maturity_date = settlement_date.replace(
        year=settlement_date.year + floor(bond.maturity_years)
    )

    cashflows.append((
        maturity_date,
        total_nominal,
        f"Capital Gain {bond.isin}"
    ))

    return cashflows
