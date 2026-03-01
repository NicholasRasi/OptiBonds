import math
from datetime import date, timedelta
from optibonds.models import BondSimple, CashFlow
from scipy.optimize import newton


def compute_permutations_bonds(matrix: list[list[BondSimple]], max_duplicated_issuers: int = 1) -> list[list[BondSimple]]:
    result: list[list[BondSimple]] = []

    def backtrack(row_id: int, current_combination: list, used_issuers: dict):
        if row_id == len(matrix):
            result.append(current_combination.copy())
            return

        for b in matrix[row_id]:
            if used_issuers.get(b.issuer, 0) >= max_duplicated_issuers:
                continue
            current_combination.append(b)
            used_issuers[b.issuer] = used_issuers.get(b.issuer, 0) + 1

            backtrack(row_id + 1, current_combination, used_issuers)

            current_combination.pop()
            used_issuers[b.issuer] -= 1
            if used_issuers[b.issuer] == 0:
                del used_issuers[b.issuer]

    backtrack(0, [], {})
    return result

def get_compounding_earnings(bonds: list[BondSimple]) -> float:
    total_bonds_earning = 0.0
    for bond in bonds:
        bond_earning = bond.capital_invested * bond.ncif  # ncif = (1 + bond.net_yield / 100)**bond.maturity_years
        total_bonds_earning += bond_earning
    return total_bonds_earning

def get_annualized_earnings(bonds: list[BondSimple]) -> float:
    total_annualized_earnings = 0.0
    for bond in bonds:
        total_bonds_earning = bond.capital_invested * (bond.net_yield / 100)
        total_annualized_earnings += total_bonds_earning
    return total_annualized_earnings

def get_total_return(bonds: list[BondSimple], net: bool = True) -> float:
    total_return = 0.0
    for bond in bonds:
        bond_return = compute_bonds_coupons([bond]) + compute_bonds_capital_gain([bond])
        if net:
            bond_return = compute_net_value(bond_return, bond.taxation)
        total_return += bond_return
    return total_return

def get_ytms(bonds: list[BondSimple]) -> float:
    return sum(bond.net_yield for bond in bonds)

def allocate_capital_to_bond(bond: BondSimple, capital_invested: float) -> BondSimple:
    # compute the max number of lots that can be purchased with the capital invested
    num_lots = math.floor(capital_invested / (bond.minimum_lot * bond.settlement_price / 100))
    capital = num_lots * bond.minimum_lot * bond.settlement_price / 100
    bond.capital_invested = capital
    bond.num_lots = num_lots
    return bond

def allocate_capital_to_bonds(bonds: list[BondSimple], capital_invested: list[float]) -> list[BondSimple]:
    for i, bond in enumerate(bonds):
        bonds[i] = allocate_capital_to_bond(bond, capital_invested[i])
    return bonds

def compute_mean_weighted_maturity(
        bonds: list[BondSimple],
        total_capital_invested: float) -> float:
    mean_weighted_maturity = 0.0
    for bond in bonds:
        weight = bond.capital_invested / total_capital_invested
        mean_weighted_maturity += weight * bond.maturity_years
    return mean_weighted_maturity

def compute_approximated_bonds_yield(
        bonds: list[BondSimple],
        total_capital_invested: float,
        capital_invested: list[float]) -> float:
    for i, bond in enumerate(bonds):
        weight = capital_invested[i] / total_capital_invested
        # weighted net yield to maturity
        yield_weighted = weight * (bond.net_yield / 100)
    return yield_weighted

def compute_bonds_coupons(bonds: list[BondSimple], net: bool = True) -> float:
    total_coupons = 0.0
    for bond in bonds:
        nominal_value = bond.num_lots * bond.minimum_lot  # or bond.capital_invested / (bond.settlement_price / 100)
        bond_coupons = nominal_value * bond.current_coupon_rate * bond.maturity_years
        if net:
            bond_coupons = compute_net_value(bond_coupons, bond.taxation)
        total_coupons += bond_coupons
    return total_coupons

def compute_bonds_capital_gain(bonds: list[BondSimple], net: bool = True) -> float:
    total_capital_gains = 0.0
    for bond in bonds:
        nominal_value = bond.num_lots * bond.minimum_lot
        # or bond.capital_invested / (bond.settlement_price / 100) - bond.capital_invested
        bond_capital_gain = nominal_value - bond.capital_invested
        if net:
            bond_capital_gain = compute_net_value(bond_capital_gain, bond.taxation)
        total_capital_gains += bond_capital_gain
    return total_capital_gains

def compute_total_gain_yield(
        total_coupons: float,
        total_capital_gain: float,
        total_capital_invested: float) -> float:
    total_yield = ((total_capital_invested + total_coupons + total_capital_gain) / total_capital_invested) - 1
    return total_yield

def compute_total_simple_yield(
        total_coupons: float,
        total_capital_gain: float,
        total_capital_invested: float,
        mean_weighted_maturity: float) -> float:
    total_yield = compute_total_gain_yield(total_coupons, total_capital_gain,
                                           total_capital_invested) / mean_weighted_maturity
    return total_yield

def compute_net_value(value: float, taxation: float) -> float:
    net_value = value * (1 - taxation)
    return net_value

def portfolio_cashflows(bonds):
    portfolio = []

    for bond in bonds:
        flows = bond_cashflows(bond)

        while len(portfolio) < len(flows):
            portfolio.append(0.0)

        for i, f in enumerate(flows):
            portfolio[i] += f

    return portfolio

def portfolio_cash_flows(bonds: list[BondSimple]) -> list[CashFlow]:
    settlement_date = date.today()
    all_cashflows = []

    for bond in bonds:
        all_cashflows.extend(
            bond_cash_flows(bond, settlement_date)
        )

    # Sort by date
    all_cashflows.sort(key=lambda x: x.date)

    return all_cashflows

def portfolio_irr(bonds: list[BondSimple]) -> float:
    all_cashflows = portfolio_cash_flows(bonds)
    portfolio_irr = xirr(all_cashflows)
    return portfolio_irr

def xirr(cashflows: list[CashFlow]):
    """
    cashflows: list of (date, amount, description)
    returns annualized IRR
    """
    dates = [cf.date for cf in cashflows]
    amounts = [cf.amount for cf in cashflows]

    t0 = dates[0]

    def npv(rate):
        return sum(
            amt / (1 + rate) ** ((d - t0).days / 365.25)
            for d, amt in zip(dates, amounts)
        )

    return newton(npv, 0.05)

def bond_cash_flows(bond: BondSimple, settlement_date: date) -> list[CashFlow]:
    cashflows: list[CashFlow] = []

    # Initial investment (outflow)
    invested = bond.capital_invested
    cashflows.append(CashFlow(
        settlement_date,
        -invested,
        f"Buy {bond.isin}"
    ))

    # Number of coupon payments
    num_coupons = math.floor(bond.maturity_years)

    # annual_coupon = total_nominal * bond.current_coupon_rate
    total_coupons = compute_bonds_coupons([bond], net=True)
    coupons = total_coupons * (num_coupons / bond.maturity_years)
    
    if num_coupons > 0:
        annual_coupon = coupons / num_coupons
        last_coupon = total_coupons - coupons
    else:
        annual_coupon = 0.0
        last_coupon = total_coupons

    if annual_coupon > 0:
        for i in range(1, num_coupons + 1):
            coupon_date = settlement_date + timedelta(days=settlement_date.day + i * 365.25)
            cashflows.append(CashFlow(
                coupon_date,
                annual_coupon,
                f"Coupon {bond.isin}"
            ))

    # last coupon + capital gain at maturity
    maturity_days = math.floor(settlement_date.day + bond.maturity_years * 365.25)
    maturity_date = settlement_date + timedelta(days=maturity_days)
    if last_coupon > 0:
        cashflows.append(CashFlow(
            maturity_date,
            last_coupon,
            f"Last Coupon {bond.isin}"
        ))

    cashflows.append(CashFlow(
        maturity_date,
        bond.capital_invested + compute_bonds_capital_gain([bond], net=True),
        f"Capital Gain {bond.isin}"
    ))

    return cashflows
