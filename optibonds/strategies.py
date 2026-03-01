import math
import pandas as pd
from optibonds.models import BondSimple, LadderConditions, LadderStrategy
from optibonds.utils import (
    allocate_capital_to_bonds,
    allocate_capital_to_bond,
    compute_permutations_bonds,
    get_annualized_earnings,
    get_compounding_earnings,
    get_total_return,
    get_ytms
)


def build_ladder(
        eligible_bonds: list[pd.DataFrame],
        ladder_conditions: LadderConditions,
        diversification: bool) -> list[list[BondSimple]]:
    if diversification:
        return build_ladder_diversification(eligible_bonds, ladder_conditions)
    else:
        return build_ladder_no_diversification(eligible_bonds, ladder_conditions)


def build_ladder_no_diversification(
        eligible_bonds: list[pd.DataFrame],
        ladder_conditions: LadderConditions) -> list[list[BondSimple]]:
    ladder: list[list[BondSimple]] = [[] for _ in eligible_bonds]

    for i, step_bonds in enumerate(eligible_bonds):
        # compute the bond with the highest earning for the step
        best_bond = get_best_bond(step_bonds, ladder_conditions.capital_invested[i], ladder_conditions.strategy)

        if best_bond and best_bond.num_lots > 0:
            ladder[i].append(best_bond)
    return ladder


def build_ladder_diversification(
        eligible_bonds: list[pd.DataFrame],
        ladder_conditions: LadderConditions) -> list[list[BondSimple]]:
    ladder: list[list[BondSimple]] = [[] for _ in eligible_bonds]

    filtered_eligible_bonds: list[list[BondSimple]] = [[] for _ in eligible_bonds]
    for i, step_bonds in enumerate(eligible_bonds):
       # group by issuer
        top_bonds = step_bonds.groupby("issuercode", as_index=False)
        # for each group of issuer, take the best bond
        for _, group in top_bonds:
            capital_invested_step = ladder_conditions.capital_invested[i]/ladder_conditions.step_width

            best_bond = get_best_bond(group, capital_invested_step, ladder_conditions.strategy)

            if best_bond and best_bond.num_lots > 0:
                filtered_eligible_bonds[i].append(best_bond)

        print(f"Step {i+1} bonds: {len(step_bonds)}, after issuer filter: {len(filtered_eligible_bonds[i])}")

    if ladder_conditions.step_width <= 1:
        # the diversification strategy is enabled on the ladder steps
        ladder = select_best_ladder(filtered_eligible_bonds, ladder_conditions)
        ladder = [[bond] for bond in ladder]
    else:
        ladder = [[] for _ in eligible_bonds]
        strategy_func = select_strategy_function(ladder_conditions.strategy)
        # the diversification strategy is enabled on the ladder step
        for i, bonds in enumerate(filtered_eligible_bonds):
            # sort bonds by bond earning
            bonds.sort(key=lambda b: strategy_func([b]), reverse=True)
            # Take only the top 'step_width' bonds for each step
            ladder[i] = bonds[:ladder_conditions.step_width]

    return ladder


def select_best_ladder(
        bonds: list[list[BondSimple]],
        ladder_conditions: LadderConditions) -> list[BondSimple]:
    ladder: list[BondSimple] = []

    # compute all permutations of the filtered eligible bonds
    bonds_perm: list[list[BondSimple]] = compute_permutations_bonds(bonds, ladder_conditions.max_duplicated_issuers)
    total_permutations_num = math.prod(len(b) for b in bonds)

    print(f"Total permutations {total_permutations_num}, to evaluate: "
          f"{len(bonds_perm)} ({len(bonds_perm)/total_permutations_num*100:.2f}%)")

    strategy_func = select_strategy_function(ladder_conditions.strategy)

    # evaluate each permutation and take the one with the highest total earnings
    max_metric = 0
    for perm in bonds_perm:
        # allocate capital to bonds based on lot sizes
        ladder_perm = allocate_capital_to_bonds(perm, ladder_conditions.capital_invested)
        # compute the permutation total earnings
        total_metrics = strategy_func(ladder_perm)

        # update ladder if the permutation is better
        if total_metrics > max_metric:
            max_metric = total_metrics
            ladder = ladder_perm.copy()

    return ladder


def get_best_bond(
        step_bonds: pd.DataFrame,
        capital_invested: float,
        strategy: str) -> BondSimple | None:
    max_bond_earning = 0.0
    best_bond: BondSimple | None = None

    strategy_func = select_strategy_function(strategy)

    for bond in step_bonds.itertuples():
        simple_bond = BondSimple(
            isin=bond.isincode,
            issuer=bond.issuercode,
            maturity_years=bond.maturityyears,
            net_yield=bond.netyieldtomaturity,
            gross_yield=bond.grossyieldtomaturity,
            current_coupon_rate=bond.currentcouponrate,
            settlement_price=bond.settlementprice,
            minimum_lot=bond.minimumlot,
            ncif=bond.ncif,
            volume_rating=bond.volumevalue,
            rating=bond.ratingsp,
            taxation=bond.taxation)

        bond_allocated = allocate_capital_to_bond(simple_bond, capital_invested)
        bond_metric = strategy_func([bond_allocated])

        if bond_metric > max_bond_earning:
            max_bond_earning = bond_metric
            best_bond = bond_allocated
    return best_bond


def select_strategy_function(strategy: LadderStrategy) -> callable:
    if strategy == LadderStrategy.MAX_EARNINGS:
        return get_compounding_earnings
    elif strategy == LadderStrategy.MAX_YTM_CAPITAL:
        return get_annualized_earnings
    elif strategy == LadderStrategy.MAX_RETURN:
        return get_total_return
    elif strategy == LadderStrategy.MAX_YTM:
        return get_ytms
    else:
        raise ValueError(f"Unknown ladder strategy: {strategy}")