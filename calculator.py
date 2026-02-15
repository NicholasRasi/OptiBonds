import pandas as pd
import argparse
from time import perf_counter
from optibonds.dataset import load_dataset
from optibonds.metrics import print_bond_vertical, print_dataset_data, print_portfolio_report, print_ladder_conditions, print_portfolio_cash_flows
from optibonds.models import BondSimple, LadderConditions
from optibonds.strategies import build_ladder
from optibonds.filters import get_eligible_bonds


def main():
    parser = argparse.ArgumentParser(description='Optibonds')
    parser.add_argument('--config', '-c', type=str, default='conditions.yml',
                        help='Path to the configuration YAML file')
    parser.add_argument('--save', '-s', type=str, help='Path to save the generated portfolio YAML')
    args = parser.parse_args()

    try:
        ladder_conditions = LadderConditions.from_yaml(args.config)
    except Exception as e:
        print(f"Error loading {args.config}: {e}")
        return

    ladder: list[list[BondSimple]] = []
    eligible_bonds: list[pd.DataFrame] = []

    # load dataset
    df = load_dataset('./data/data.csv')

    print_dataset_data(df)

    print_ladder_conditions(ladder_conditions)

    t_start = perf_counter()

    print("\nFiltering eligible bonds")
    eligible_bonds = get_eligible_bonds(df, ladder_conditions)
    if not eligible_bonds:
        print("No eligible bonds found for ladder construction")
        return

    diversification = ladder_conditions.step_width > 1 or ladder_conditions.max_duplicated_issuers is not None
    ladder = build_ladder(eligible_bonds, ladder_conditions, diversification)

    t_end = perf_counter()
    execution_time = t_end - t_start

    print(f"\nLadder Results:")
    for i, bonds in enumerate(ladder):
        print(f" \nStep {i+1}:")
        print(f" Number of bonds: {len(bonds)}")
        for bond in bonds:
            print(f"Bond: {bond.isin}")
            print(f"Lots: {bond.num_lots}, capital: {bond.capital_invested:.2f}, nominal: {bond.num_lots * bond.minimum_lot:.2f}\n",)

            bond_df = df.loc[bond.isin]

            print_bond_vertical(bond_df)
            print("\n")

    bonds: list[BondSimple] = [bond for bonds in ladder for bond in bonds]

    print_portfolio_report(
        bonds=bonds,
        ladder=ladder,
        ladder_conditions=ladder_conditions,
        execution_time=execution_time
    )

    # print_portfolio_cash_flows(bonds)

    if args.save:
        portfolio_data = {
            "investments": [
                {"isin": bond.isin, "nominal_value": float(bond.num_lots * bond.minimum_lot)}
                for bond in bonds
            ],
            "ladder_conditions": {
                "strategy": ladder_conditions.strategy.value,
                "capital_invested": sum(bond.capital_invested for bond in bonds)
            },
        }
        try:
            with open(args.save, 'w') as f:
                import yaml
                yaml.dump(portfolio_data, f, sort_keys=False)
            print(f"\nPortfolio saved to {args.save}")
        except Exception as e:
            print(f"Error saving portfolio to {args.save}: {e}")


main()
