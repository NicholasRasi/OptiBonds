import pandas as pd
from optibonds.models import LadderConditions


def get_eligible_bonds(df: pd.DataFrame, ladder_conditions: LadderConditions, starting_date: pd.Timestamp = None) -> list[pd.DataFrame]:
    eligible_bonds: list[pd.DataFrame] = []

    if starting_date is None:
        starting_date = pd.Timestamp.today()

    # set starting date
    today = starting_date + pd.DateOffset(years=ladder_conditions.years_offset, months=ladder_conditions.months_offset)
    # compute eligible bonds for each step
    for step in range(0, ladder_conditions.ladder_size):
        print(f"Step {step + 1}/{ladder_conditions.ladder_size}")

        # compute target date range
        years_offset = (step + 1) * ladder_conditions.step_size
        target_date_start = today + pd.DateOffset(years=years_offset, days=-ladder_conditions.date_tolerance_days_start)
        target_date_end = today + pd.DateOffset(years=years_offset, days=ladder_conditions.date_tolerance_days_end)
        print(f" Date range: {target_date_start.date()} - {target_date_end.date()}")

        eligible_bonds_step = pd.DataFrame()
        filter_mask = (df['redemptiondate'] >= target_date_start) & (df['redemptiondate'] <= target_date_end)
        if ladder_conditions.currencies:
            filter_mask &= df["currencycode"].isin(ladder_conditions.currencies)
        if ladder_conditions.min_rating:
            filter_mask &= (df['ratingsp'] >= ladder_conditions.min_rating)
        if ladder_conditions.include_issuer_codes:
            filter_mask &= df["issuercode"].isin(ladder_conditions.include_issuer_codes)
        if ladder_conditions.exclude_issuer_codes:
            filter_mask &= ~df["issuercode"].str.startswith(tuple(ladder_conditions.exclude_issuer_codes), na=False)
        if ladder_conditions.include_isins:
            filter_mask &= df.index.isin(ladder_conditions.include_isins)
        if ladder_conditions.exclude_isins:
            filter_mask &= ~df.index.isin(ladder_conditions.exclude_isins)
        if ladder_conditions.max_last_price:
            filter_mask &= (df['settlementprice'] <= ladder_conditions.max_last_price)
        if ladder_conditions.min_coupon_rate:
            filter_mask &= (df['currentcouponrate'] >= ladder_conditions.min_coupon_rate)
        if ladder_conditions.min_volume_rating:
            filter_mask &= (df['volumevalue'] >= ladder_conditions.min_volume_rating)

        eligible_bonds_step = df[filter_mask]
        print(f" Bonds found: {len(eligible_bonds_step)}\n")

        if len(eligible_bonds_step) == 0:
            print("No bonds found for this step. Exiting.")
            return

        eligible_bonds.append(eligible_bonds_step)

    return eligible_bonds
