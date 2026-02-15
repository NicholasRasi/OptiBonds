from tabulate import tabulate
from datetime import date
from optibonds.cash_flows import bond_cash_flows
from optibonds.models import BondSimple, LadderConditions
from optibonds.utils import (
    compute_bonds_capital_gain,
    compute_bonds_coupons,
    compute_mean_weighted_maturity,
    compute_net_value,
    compute_total_gain_yield,
    compute_total_simple_yield,
    get_compounding_earnings,
    portfolio_irr
)


def money(x):
    return f"{x:,.2f}"


def pct(x):
    return f"{x:.2%}"


def years(x):
    return f"{x:.2f}y"


def section(title):
    print("\n" + title)
    print("=" * len(title))


def print_dataset_data(df):
    section("DATASET SAMPLE")
    rows = [
        ["Total bonds in dataset", len(df)],
        ["Date range", f"{df['redemptiondate'].min().date()} to {df['redemptiondate'].max().date()}"],
        ["Issuers", df['issuercode'].nunique()]
    ]
    print(tabulate(
        rows,
        tablefmt="github",
    ))


def print_ladder_conditions(ladder_conditions):
    section("LADDER CONDITIONS")

    rows = [
        ["Ladder size", ladder_conditions.ladder_size],
        ["Step size (years)", ladder_conditions.step_size],
        ["Step width", ladder_conditions.step_width],
        ["Years offset", ladder_conditions.years_offset],
        ["Months offset", ladder_conditions.months_offset],
        ["Date tolerance start (days)", ladder_conditions.date_tolerance_days_start],
        ["Date tolerance end (days)", ladder_conditions.date_tolerance_days_end],
        [
            "Capital invested per step",
            ", ".join(f"{x:,.2f}" for x in ladder_conditions.capital_invested),
        ],
        ["Minimum rating", ladder_conditions.min_rating or "—"],
        [
            "Currencies",
            ", ".join(ladder_conditions.currencies)
            if ladder_conditions.currencies else "—",
        ],
        ["Max duplicated issuers", ladder_conditions.max_duplicated_issuers],
        [
            "Included issuers",
            ", ".join(ladder_conditions.include_issuer_codes)
            if ladder_conditions.include_issuer_codes else "—",
        ],
        [
            "Excluded issuers",
            ", ".join(ladder_conditions.exclude_issuer_codes)
            if ladder_conditions.exclude_issuer_codes else "—",
        ],
        [
            "Excluded ISINs",
            ", ".join(ladder_conditions.exclude_isins)
            if ladder_conditions.exclude_isins else "—",
        ],
        [
            "Max last price",
            f"{ladder_conditions.max_last_price:,.2f}"
            if ladder_conditions.max_last_price is not None else "—",
        ],
        ["Min coupon rate",
         f"{ladder_conditions.min_coupon_rate:.2%}"
         if ladder_conditions.min_coupon_rate is not None else "—"],
        ["Minimum volume rating",
         ladder_conditions.min_volume_rating if ladder_conditions.min_volume_rating is not None else "—"],
    ]

    print(tabulate(
        rows,
        headers=["Condition", "Value"],
        tablefmt="github",
    ))


def print_portfolio_report(
        bonds: list[BondSimple],
        ladder: list[list[BondSimple]],
        execution_time: float,
        ladder_conditions: dict | LadderConditions | None = None):
    # =========================
    # EXECUTION
    # =========================
    section("EXECUTION SUMMARY")

    exec_summary = [
        ["Execution time (seconds)", f"{execution_time:.2f}"]
    ]

    print(tabulate(exec_summary, tablefmt="github"))

    # =========================
    # CORE METRICS
    # =========================
    if ladder_conditions and isinstance(ladder_conditions, dict):
        target_capital_invested = ladder_conditions['capital_invested']
        ladder_strategy = ladder_conditions['strategy']
    elif ladder_conditions and isinstance(ladder_conditions, LadderConditions):
        target_capital_invested = sum(ladder_conditions.capital_invested)
        ladder_strategy = ladder_conditions.strategy.value

    capital_invested = sum(bond.capital_invested for bond in bonds)
    net_compounding_earning = get_compounding_earnings(bonds)

    mean_weighted_duration = compute_mean_weighted_maturity(bonds, capital_invested)
    irr_portfolio = portfolio_irr(bonds)

    # =========================
    # SUMMARY
    # =========================
    section("PORTFOLIO SUMMARY")

    summary_table = [
        ["Number of bonds", len(bonds)],
        ["Target capital invested", money(target_capital_invested)],
        ["Total capital invested", money(capital_invested)],
        ["Net compounding earnings", money(net_compounding_earning)],
        ["Mean weighted duration (years)", years(mean_weighted_duration)],
        ["Portfolio IRR", pct(irr_portfolio)],
        ["Strategy", ladder_strategy],
    ]

    print(tabulate(summary_table, tablefmt="github"))

    if ladder_conditions and isinstance(ladder_conditions, LadderConditions):
        # =========================
        # LADDER BREAKDOWN
        # =========================
        section("LADDER BREAKDOWN")

        ladder_rows = []

        total_coupons_gross = 0.0
        total_coupons_net = 0.0
        total_capital_gains_gross = 0.0
        total_capital_gains_net = 0.0
        total_capital = 0.0
        total_capital_invested = 0.0

        for i, step_capital in enumerate(ladder_conditions.capital_invested):
            bonds_step = ladder[i]

            if not bonds_step:
                ladder_rows.append([
                    i + 1,
                    money(step_capital),
                    0,
                    "—",
                    "—",
                    "—",
                    "—",
                    "—",
                ])
                continue

            step_capital_invested = sum(bond.capital_invested for bond in bonds_step)
            step_coupons_gross = compute_bonds_coupons(bonds_step)
            step_coupons_net = compute_net_value(step_coupons_gross)

            step_capital_gain_gross = compute_bonds_capital_gain(bonds_step)
            step_capital_gain_net = compute_net_value(step_capital_gain_gross)

            coupon_rates = ", ".join(
                f"{bond.current_coupon_rate * 100:.2f}%" for bond in bonds_step
            )

            ladder_rows.append([
                i + 1,
                money(step_capital),
                money(step_capital_invested),
                len(bonds_step),
                coupon_rates,
                money(step_coupons_gross),
                money(step_coupons_net),
                money(step_capital_gain_gross),
                money(step_capital_gain_net),
            ])

            total_capital += step_capital
            total_capital_invested += step_capital_invested
            total_coupons_gross += step_coupons_gross
            total_coupons_net += step_coupons_net
            total_capital_gains_gross += step_capital_gain_gross
            total_capital_gains_net += step_capital_gain_net

        # ---- TOTAL ROW ----
        ladder_rows.append([
            "TOTAL",
            money(total_capital),
            money(total_capital_invested),
            "",
            "",
            money(total_coupons_gross),
            money(total_coupons_net),
            money(total_capital_gains_gross),
            money(total_capital_gains_net),
        ])

        print(tabulate(
            ladder_rows,
            headers=[
                "Step",
                "Target Capital Invested",
                "Capital Invested",
                "# Bonds",
                "Coupon Rates",
                "Coupons Gross",
                "Coupons Net",
                "Capital Gain Gross",
                "Capital Gain Net",
            ],
            tablefmt="github",
        ))

    # =========================
    # BOND BREAKDOWN
    # =========================
    section("BOND BREAKDOWN")

    bond_rows = []

    total_capital_invested = 0.0
    total_num_lots = 0
    total_coupons_gross = 0.0
    total_coupons_net = 0.0
    total_capital_gains_gross = 0.0
    total_capital_gains_net = 0.0

    for i, bond in enumerate(bonds):
        coupons_gross = compute_bonds_coupons([bond])
        coupons_net = compute_net_value(coupons_gross)

        capital_gain_gross = compute_bonds_capital_gain([bond])
        capital_gain_net = compute_net_value(capital_gain_gross)

        net_ytm = bond.net_yield/100

        bond_rows.append([
            bond.isin,
            bond.issuer,
            bond.rating,
            bond.volume_rating,
            years(bond.maturity_years),
            bond.settlement_price,
            money(bond.capital_invested),
            bond.num_lots,
            bond.num_lots * bond.minimum_lot,
            pct(net_ytm),
            pct(bond.current_coupon_rate),
            money(coupons_gross),
            money(coupons_net),
            money(capital_gain_gross),
            money(capital_gain_net),
        ])

        total_capital_invested += bond.capital_invested
        total_num_lots += bond.num_lots
        total_coupons_gross += coupons_gross
        total_coupons_net += coupons_net
        total_capital_gains_gross += capital_gain_gross
        total_capital_gains_net += capital_gain_net

    # ---- TOTAL ROW ----
    bond_rows.append([
        "TOTAL",
        "",
        "",
        "",
        years(mean_weighted_duration),
        "",
        money(total_capital_invested),
        total_num_lots,
        "",
        "",
        "",
        money(total_coupons_gross),
        money(total_coupons_net),
        money(total_capital_gains_gross),
        money(total_capital_gains_net),
    ])

    print(tabulate(
        bond_rows,
        headers=[
            "ISIN",
            "Issuer",
            "Rating",
            "VR",
            "Duration",
            "Price",
            "Capital Invested",
            "Lots",
            "Nominal",
            "Net YTM",
            "Coupon",
            "Coupons G",
            "Coupons N",
            "Capital Gain G",
            "N",
        ],
        tablefmt="github",
    ))

    # =========================
    # TOTAL RETURNS
    # =========================
    section("TOTAL RETURNS")

    gross_total_return = total_coupons_gross + total_capital_gains_gross
    net_total_return = total_coupons_net + total_capital_gains_net

    returns_table = [
        ["Coupons", money(total_coupons_gross), money(total_coupons_net)],
        ["Avg Monthly Coupon", money(total_coupons_gross / mean_weighted_duration / 12),
         money(total_coupons_net / mean_weighted_duration / 12)],
        ["Capital gains", money(total_capital_gains_gross), money(total_capital_gains_net)],
        ["Total return", money(gross_total_return), money(net_total_return)],
        ["Total", money(capital_invested + gross_total_return), money(capital_invested + net_total_return)],
        [
            "Annualized simple net yield",
            "",
            pct(
                compute_total_simple_yield(
                    total_coupons_net,
                    total_capital_gains_net,
                    capital_invested,
                    mean_weighted_duration,
                )
            ),
        ],
        [
            "Net interest factor (simple)",
            "",
            f"{compute_total_gain_yield(
                total_coupons_net,
                total_capital_gains_net,
                capital_invested,
            ):.4f}x",
        ],
    ]

    print(tabulate(
        returns_table,
        headers=["Metric", "Gross", "Net"],
        tablefmt="github",
    ))


def print_bond_vertical(bond_df):
    df = bond_df.copy()

    df['redemptiondate'] = df['redemptiondate'].date()
    df['grossyieldtomaturity'] = df['grossyieldtomaturity']
    df['netyieldtomaturity'] = df['netyieldtomaturity']
    df['currentcouponrate'] = df['currentcouponrate'] * 100
    df['settlementprice'] = df['settlementprice'].round(2)
    df['maturityyears'] = df['maturityyears'].round(2)
    df['ncif'] = df['ncif'].round(2)

    df = df.rename({
        'isincode': 'ISIN',
        'issuercode': 'Issuer',
        'issuerdescription': 'Issuer Name',
        'description': 'Description',
        'redemptiondate': 'Maturity',
        'maturityyears': 'Maturity (yrs)',
        'ratingsp': 'S&P Rating',
        'ratingmoodys': "Moody's Rating",
        'ratingfitch': 'Fitch Rating',
        'grossyieldtomaturity': 'YTM Gross (%)',
        'netyieldtomaturity': 'YTM Net (%)',
        'currentcouponrate': 'Coupon (%)',
        'settlementprice': 'Price',
        'minimumlot': 'Minimum Lot',
        'currencycode': 'Currency',
        'ncif': 'NCIF'
    })

    fields = [
        'ISIN',
        'Description',
        'Issuer',
        'Issuer Name',
        'Currency',
        'Maturity',
        'Maturity (yrs)',
        'S&P Rating',
        "Moody's Rating",
        'Fitch Rating',
        'Coupon (%)',
        'Price',
        'YTM Gross (%)',
        'YTM Net (%)',
        'Minimum Lot',
        'NCIF'
    ]

    out = (
        df[fields]
        .to_frame(name='Value')
        .to_markdown(
            tablefmt='github',
            floatfmt='.2f'
        )
    )

    print(out)


def print_portfolio_cash_flows(bonds: list[BondSimple]):
    section("CASH FLOWS")
    settlement_date = date.today()
    all_cashflows = []

    for bond in bonds:
        all_cashflows.extend(
            bond_cash_flows(bond, settlement_date)
        )

    # Sort by date
    all_cashflows.sort(key=lambda x: x[0])

    table = [
        [cf_date.isoformat(), f"{amount:,.2f}", desc]
        for cf_date, amount, desc in all_cashflows
    ]

    print(tabulate(
        table,
        headers=["Date", "Cash Flow", "Description"],
        tablefmt="github"
    ))
