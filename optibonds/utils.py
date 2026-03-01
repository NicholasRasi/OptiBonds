import math
import numpy_financial as npf
from optibonds.models import BondSimple


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


def get_compounding_earning(bond: BondSimple) -> float:
    # compute the final value of the bond investment
    bond_earning = bond.capital_invested * bond.ncif  # ncif = (1 + bond.net_yield / 100)**bond.maturity_years
    return bond_earning


def get_compounding_earnings(bonds: list[BondSimple]) -> float:
    total_bonds_earning = sum(get_compounding_earning(bond) for bond in bonds)
    return total_bonds_earning


def get_annualized_earning(bond: BondSimple) -> float:
    return bond.capital_invested * (bond.net_yield / 100)


def get_annualized_earnings(bonds: list[BondSimple]) -> float:
    total_annualized_earnings = sum(get_annualized_earning(bond) for bond in bonds)
    return total_annualized_earnings

def get_total_return(bonds: list[BondSimple], net: bool = True) -> float:
    total_return = 0.0
    for bond in bonds:
        bond_return = compute_bonds_coupons([bond]) + compute_bonds_capital_gain([bond])
        if net:
            bond_return = compute_net_value(bond_return, bond.taxation)
        total_return += bond_return
    return total_return
    # compute the max number of lots that can be purchased with the capital invested
    num_lots = math.floor(capital_invested / (bond.minimum_lot * bond.settlement_price / 100))
    capital = num_lots * bond.minimum_lot * bond.settlement_price / 100
    bond.capital_invested = capital
    bond.num_lots = num_lots
    return bond


def allocate_capital_to_bonds(
        bonds: list[BondSimple],
        capital_invested: list[float]) -> list[BondSimple]:
    for i, bond in enumerate(bonds):
        bonds[i] = allocate_capital_to_bond(bond, capital_invested[i])
    return bonds


# def compute_total_get_compounding_earning_with_ci(
#         bonds: list[BondSimple],
#         total_capital_invested: float) -> float:
#     bond_earnings = []
#     for i, bond in enumerate(bonds):
#         capital = bond.capital_invested

#         # compute the final value of the bond investment
#         bond_earning = capital * bond.ncif  # ncif = (1 + bond.net_yield / 100)**bond.maturity_years
#         bond_earnings.append(bond_earning)

#     total_bonds_earning = sum(bond_earnings)
#     total_yield = (total_bonds_earning / total_capital_invested) - 1
#     return total_yield


def compute_mean_weighted_maturity(
        bonds: list[BondSimple],
        total_capital_invested: float) -> float:
    mean_weighted_maturity = 0.0
    for bond in bonds:
        weight = bond.capital_invested / total_capital_invested
        mean_weighted_maturity += weight * bond.maturity_years
    return mean_weighted_maturity


# def get_approximated_annualized_compounded_yield(
#         bonds: list[BondSimple],
#         total_capital_invested: float) -> float:
#     mean_weighted_maturity = compute_mean_weighted_maturity(bonds, total_capital_invested)
#     total_earning = get_compounding_earnings(bonds)

#     annualized_yield = (total_earning/total_capital_invested)**(1 / mean_weighted_maturity) - 1
#     return annualized_yield


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


def compute_net_value(value: float) -> float:
    tax_rate = 0.125
    net_value = value * (1 - tax_rate)
    return net_value


def bond_cashflows(bond: BondSimple):
    flows = []

    flows.append(-bond.capital_invested)
    nominal = bond.capital_invested / (bond.settlement_price / 100)
    coupon_net = nominal * bond.current_coupon_rate * (1 - 0.125)

    years = int(round(bond.maturity_years))
    for _ in range(1, years):
        flows.append(coupon_net)

    flows.append(coupon_net + nominal)
    return flows


def portfolio_cashflows(bonds):
    portfolio = []

    for bond in bonds:
        flows = bond_cashflows(bond)

        while len(portfolio) < len(flows):
            portfolio.append(0.0)

        for i, f in enumerate(flows):
            portfolio[i] += f

    return portfolio


def portfolio_irr(bonds):
    cashflows = portfolio_cashflows(bonds)
    irr = npf.irr(cashflows)
    return irr
