from time import perf_counter
import argparse
from optibonds.dataset import load_dataset
from optibonds.metrics import print_dataset_data, print_portfolio_report
from optibonds.models import BondSimple, PortfolioConditions
from optibonds.utils import allocate_capital_to_bond


def main():
    parser = argparse.ArgumentParser(description='Bond Portfolio Earnings Calculator')
    parser.add_argument('--config', '-c', type=str, default='portfolio.yml', help='Path to the configuration YAML file')
    args = parser.parse_args()

    try:
        portfolio_conditions = PortfolioConditions.from_yaml(args.config)
    except Exception as e:
        print(f"Error loading {args.config}: {e}")
        return

    df = load_dataset('./data/data.csv')
    print_dataset_data(df)

    t_start = perf_counter()

    bonds: list[BondSimple] = []

    print("\nProcessing investments...")
    for investment in portfolio_conditions.investments:
        if investment.isin not in df.index:
            print(f"Warning: ISIN {investment.isin} not found in dataset. Skipping.")
            continue

        bond_row = df.loc[investment.isin]

        simple_bond = BondSimple(
            isin=bond_row.isincode,
            issuer=bond_row.issuercode,
            maturity_years=bond_row.maturityyears,
            net_yield=bond_row.netyieldtomaturity,
            gross_yield=bond_row.grossyieldtomaturity,
            current_coupon_rate=bond_row.currentcouponrate,
            settlement_price=bond_row.settlementprice,
            minimum_lot=bond_row.minimumlot,
            ncif=bond_row.ncif,
            rating=bond_row.ratingsp,
            volume_rating=bond_row.volumevalue
        )

        simple_bond.num_lots = int(investment.nominal_value / simple_bond.minimum_lot)
        simple_bond.capital_invested = investment.nominal_value * simple_bond.settlement_price / 100
        bonds.append(simple_bond)

    t_end = perf_counter()
    execution_time = t_end - t_start

    ladder = []
    processed_bonds = {bond.isin: bond for bond in bonds}

    for i, inv in enumerate(portfolio_conditions.investments):
        if inv.isin in processed_bonds:
            ladder.append([processed_bonds[inv.isin]])
        else:
            ladder.append([])

    print_portfolio_report(
        bonds=bonds,
        ladder=ladder,
        ladder_conditions=portfolio_conditions.ladder_conditions,
        execution_time=execution_time
    )


if __name__ == "__main__":
    main()
