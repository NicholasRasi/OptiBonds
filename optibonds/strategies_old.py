import pandas as pd
from models import BondSimple, LadderConditions
from utils import (
    compute_permutations_bonds,
    compute_total_compounded_earning,
    compute_approximated_bonds_yield,
)
import math
# Strategies

# Maximize the yield


def no_diversification_strategy(
        eligible_bonds: list[pd.DataFrame],
        ladder_conditions: LadderConditions) -> list[list[BondSimple]]:
    ladder: list[list[BondSimple]] = []

    # For each step, select the bond with the highest yield
    for i, bonds in enumerate(eligible_bonds):
        best_bond = bonds.sort_values(ladder_conditions.maximize_strategy, na_position="last", ascending=False).iloc[0]
        bond = BondSimple(
            isin=best_bond["isincode"],
            issuer=best_bond["issuercode"],
            maturity_years=best_bond["maturityyears"],
            net_yield=best_bond["netyieldtomaturity"],
            gross_yield=best_bond["grossyieldtomaturity"],
            current_coupon_rate=best_bond["currentcouponrate"],
            settlement_price=best_bond["settlementprice"],
            ncif=best_bond["ncif"]
        )
        bond.capital_invested = ladder_conditions.capital_invested[i]
        ladder.append([bond])

    return ladder

# Return a list of list
# each inner list contains bonds selected for the ladder step


def diversification_strategy(
        eligible_bonds: list[pd.DataFrame],
        ladder_conditions: LadderConditions) -> list[list[BondSimple]]:
    ladder: list[list[BondSimple]] = [[] for _ in eligible_bonds]

    # Filter eligible bonds to keep only the highest yield bond per issuer for each step
    filtered_eligible_bonds: list[list[BondSimple]] = [[] for _ in eligible_bonds]
    for i, step_bonds in enumerate(eligible_bonds):
        if ladder_conditions.step_width == 1:
            # Take the best bond per issuer
            top_bonds = step_bonds\
                .sort_values(ladder_conditions.maximize_strategy, na_position="last", ascending=False)\
                .groupby("issuercode", as_index=False)\
                .head(1)
        else:
            top_bonds = step_bonds\
                .sort_values(ladder_conditions.maximize_strategy, na_position="last", ascending=False)\
                .groupby("issuercode", as_index=False)\
                .head(ladder_conditions.max_duplicated_issuers)

        for top_bond in top_bonds.itertuples():
            filtered_eligible_bonds[i].append(
                BondSimple(
                    isin=top_bond.isincode,
                    issuer=top_bond.issuercode,
                    duration_years=top_bond.durationyears,
                    net_yield=top_bond.netyieldtomaturity,
                    gross_yield=top_bond.grossyieldtomaturity,
                    current_coupon_rate=top_bond.currentcouponrate,
                    settlement_price=top_bond.settlementprice,
                    ncif=top_bond.ncif
                )
            )
        print(f"Step {i+1} bonds: {len(step_bonds)}, after issuer filter: {len(top_bonds)}")

    if ladder_conditions.step_width == 1:
        # The diversification strategy is enabled ladder
        ladder = select_best_ladder(filtered_eligible_bonds, ladder_conditions)
        ladder = [[bond] for bond in ladder]
    else:
        ladder = [[] for _ in filtered_eligible_bonds]
        # The diversification strategy is enabled on the ladder step
        for i, bonds in enumerate(filtered_eligible_bonds):
            # Take only the top 'step_width' bonds for each step
            ladder[i] = bonds[:ladder_conditions.step_width]

    # Assign capital invested to each bond in the ladder
    for i, bonds in enumerate(ladder):
        num_bonds = len(bonds)
        for bond in bonds:
            bond.capital_invested = ladder_conditions.capital_invested[i] / num_bonds
    return ladder


def select_best_ladder(filtered_eligible_bonds: list[list[BondSimple]],
                       ladder_conditions: LadderConditions) -> list[BondSimple]:
    ladder: list[BondSimple] = []

    # Compute all permutations of the filtered eligible bonds
    bonds_perm: list[list[BondSimple]] = compute_permutations_bonds(
        filtered_eligible_bonds, ladder_conditions.max_duplicated_issuers)
    total_permutations_num = math.prod(len(bonds) for bonds in filtered_eligible_bonds)
    print(
        f"Total permutations {total_permutations_num}, to evaluate: {len(bonds_perm)} ({len(bonds_perm)/total_permutations_num*100:.2f}%)")

    # Evaluate each permutation and take the one with the highest total yield
    total_capital_invested = sum(ladder_conditions.capital_invested)
    max_metric = 0
    for perm in bonds_perm:
        # Compute total yield for the permutation
        if ladder_conditions.maximize_strategy == 'ncif':
            total_metrics = compute_total_compounded_earning(bonds=perm,
                                                             total_capital_invested=total_capital_invested,
                                                             capital_invested=ladder_conditions.capital_invested)
        elif ladder_conditions.maximize_strategy == 'netyieldtomaturity':
            total_metrics = compute_approximated_bonds_yield(bonds=perm,
                                                             total_capital_invested=total_capital_invested,
                                                             capital_invested=ladder_conditions.capital_invested)
            # compute an approximation of the average net yield to maturity weighted by the capital invested
            # total_metrics = compute_approximated_annualized_compounded_yield(bonds=perm,
            #                                                                  total_capital_invested=total_capital_invested,
            #                                                                  capital_invested=ladder_conditions.capital_invested)
        # Update ladder if this permutation is better
        if total_metrics > max_metric:
            max_metric = total_metrics
            ladder = perm

    print(f"\nMax diversification yield strategy selected total yield: {max_metric:.2f}%")

    return ladder

# Maximize diversification by selecting bonds from different issuers


# def diversification_strategy_2(
#         eligible_bonds: list[pd.DataFrame],
#         maximize_strategy: str,
#         max_duplicated_issuers: int,
#         capital_invested: list[float]) -> list[BondSimple]:
#     ladder: list[BondSimple] = []

#     # Filter eligible bonds to keep only the highest yield bond per issuer for each step
#     filtered_eligible_bonds: list[list[BondSimple]] = [[] for _ in eligible_bonds]
#     for i, step_bonds in enumerate(eligible_bonds):
#         idx = step_bonds.groupby("issuercode")[maximize_strategy].idxmax()
#         filtered_eligible_step_bonds = step_bonds.loc[idx]
#         for eligible_bond in filtered_eligible_step_bonds.itertuples():
#             filtered_eligible_bonds[i].append(
#                 BondSimple(
#                     isin=eligible_bond.isincode,
#                     issuer=eligible_bond.issuercode,
#                     duration_years=eligible_bond.durationyears,
#                     net_yield=eligible_bond.netyieldtomaturity,
#                     gross_yield=eligible_bond.grossyieldtomaturity,
#                     current_coupon_rate=eligible_bond.currentcouponrate,
#                     settlement_price=eligible_bond.settlementprice,
#                     ncif=eligible_bond.ncif
#                 )
#             )
#         print(f"Step {i+1} bonds: {len(step_bonds)}, after issuer filter: {len(filtered_eligible_step_bonds)}")

#     # Compute all permutations of the filtered eligible bonds
#     bonds_perm = compute_permutations_bonds(filtered_eligible_bonds, max_duplicated_issuers)
#     total_permutations_num = math.prod(len(bonds) for bonds in filtered_eligible_bonds)
#     print(f"Total permutations {total_permutations_num}")
#     print(f"to evaluate: {len(bonds_perm)} ({len(bonds_perm)/total_permutations_num*100:.2f}%)")

#     # Evaluate each permutation and take the one with the highest total yield
#     total_capital_invested = sum(capital_invested)
#     max_metric = 0
#     for i, perm in enumerate(bonds_perm):
#         # percent = (i + 1) / len(bonds_perm) * 100
#         # print(f"{percent:.1f}% done", end="\r")
#         # print(f"Evaluating permutation {perm}")

#         if maximize_strategy == 'ncif':
#             # Compute total yield for the permutation
#             total_metrics = compute_total_compounded_earning(perm, capital_invested, total_capital_invested)
#         # elif maximize_strategy == 'currentcouponrate':
#         #    total_metrics = sum(bond.current_coupon_rate for bond in perm)/len(perm)

#         # Update ladder if this permutation has a higher total yield
#         if total_metrics > max_metric:
#             max_metric = total_metrics
#             ladder = perm

#     print(f"\nMax diversification yield strategy selected total yield: {max_metric:.2f}%")
#     return ladder


# def get_top_n_bonds(eligible_bonds: list[pd.DataFrame], maximize_strategy: str, n: int) -> list[list[BondSimple]]:
#     ladder: list[list[BondSimple]] = []
#     for i, bonds in enumerate(eligible_bonds):
#         ladder.append([])
#         top_bonds = bonds.sort_values(maximize_strategy, na_position="last", ascending=False).head(n)
#         for eligible_bond in top_bonds.itertuples():
#             ladder[i].append(BondSimple(
#                 isin=eligible_bond.isincode,
#                 issuer=eligible_bond.issuercode,
#                 duration_years=eligible_bond.durationyears,
#                 net_yield=eligible_bond.netyieldtomaturity,
#                 gross_yield=eligible_bond.grossyieldtomaturity,
#                 current_coupon_rate=eligible_bond.currentcouponrate,
#                 settlement_price=eligible_bond.settlementprice
#             ))
#     return ladder
