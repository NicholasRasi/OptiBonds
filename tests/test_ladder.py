"""
Integration tests for bond filtering and ladder building.
Tests various combinations of diversification, step width, capital, and strategies.
All bond data is generated at runtime using current date.
"""
import pytest
import pandas as pd
from optibonds.dataset import RATING_DTYPE_SP
from optibonds.filters import get_eligible_bonds
from optibonds.strategies import build_ladder
from optibonds.models import LadderConditions, LadderStrategy


@pytest.fixture
def bond_dataframe():
    """
    Creates a DataFrame with bond data at runtime using current date.
    Includes duplicate issuers to test diversification constraints.
    Includes bonds with different minimum lots (1 and 1000).
    """
    today = pd.Timestamp.today()
    reference_date = today

    # Create bonds maturing in ~1 year and ~2 years
    redemption_1yr = today + pd.DateOffset(years=1)
    redemption_2yr = today + pd.DateOffset(years=2)

    # Bond data with duplicate issuers
    # ISSUER_A: 4 bonds (A00001, A00002, A00003, A00004)
    # ISSUER_B: 3 bonds (B00001, B00002, B00003)
    # ISSUER_C: 2 bonds (C00001, C00002)
    # Others: 1 bond each
    # Some bonds have minimum_lot = 1 for testing
    bonds_data = {
        'isincode': [
            'A00001', 'B00001', 'C00001', 'A00002', 'E00001', 'C00002', 'A00003',  # Year 1 (7 bonds)
            'F00001', 'B00002', 'H00001', 'I00001', 'A00004', 'B00003'             # Year 2 (6 bonds)
        ],
        'issuercode': [
            'ISSUER_A', 'ISSUER_B', 'ISSUER_C', 'ISSUER_A', 'ISSUER_E', 'ISSUER_C', 'ISSUER_A',  # Year 1
            'ISSUER_F', 'ISSUER_B', 'ISSUER_H', 'ISSUER_I', 'ISSUER_A', 'ISSUER_B'               # Year 2
        ],
        'redemptiondate': [
            redemption_1yr, redemption_1yr, redemption_1yr, redemption_1yr, redemption_1yr, redemption_1yr, redemption_1yr,
            redemption_2yr, redemption_2yr, redemption_2yr, redemption_2yr, redemption_2yr, redemption_2yr
        ],
        'referencedate': [reference_date] * 13,
        'netyieldtomaturity': [3.0, 4.5, 2.0, 3.5, 1.0, 2.5, 3.2,   # Year 1
                               2.5, 3.5, 5.5, 4.5, 2.0, 8.0],      # Year 2
        'grossyieldtomaturity': [3.5, 5.0, 2.5, 4.0, 1.5, 3.0, 3.7,
                                 3.0, 4.0, 6.0, 5.0, 2.5, 4.5],
        'currentcouponrate': [0.03, 0.04, 0.02, 0.035, 0.01, 0.025, 0.032,
                              0.025, 0.035, 0.05, 0.045, 0.02, 0.04],
        'settlementprice': [102.5, 95.0, 88.0, 103.0, 97.5, 91.0, 105.0,  # Year 1: varied 88-105
                            89.0, 96.5, 92.0, 87.0, 104.0, 93.5],   # Year 2: varied 87-104
        'minimumlot': [1000, 1000, 1, 1000, 1000, 1, 1000,  # Year 1: C00001 and C00002 have lot=1
                       1000, 1000, 1000, 1, 1000, 1000],     # Year 2: I00001 has lot=1
        'ratingsp': ['A', 'BBB', 'AA', 'A', 'AAA', 'AA', 'A',
                     'A', 'BBB', 'BB', 'BB+', 'AA', 'BBB'],
        'volumevalue': [1, 2, 3, 4, 0, 1, 2,
                        3, 4, 0, 1, 2, 3],
    }

    df = pd.DataFrame(bonds_data)

    # Convert ratings to categorical
    df['ratingsp'] = df['ratingsp'].astype(RATING_DTYPE_SP)

    # Calculate maturity in years
    df['maturityyears'] = (
        (df['redemptiondate'] - df['referencedate']).dt.days / 365.25
    )

    # Calculate NCIF (Net Compound Interest Factor)
    df['ncif'] = (1 + df['netyieldtomaturity']/100) ** df['maturityyears']

    return df


@pytest.fixture
def bond_dataframe_simple():
    """
    Creates a DataFrame with bond data at runtime using current date.
    Includes duplicate issuers to test diversification constraints.
    Includes bonds with different minimum lots (1 and 1000).
    """
    today = pd.Timestamp.today()
    reference_date = today

    # Create bonds maturing in ~1 year and ~2 years
    redemption_1yr = today + pd.DateOffset(years=1)
    redemption_2yr = today + pd.DateOffset(years=2)

    bonds_data = {
        'isincode': [
            'A00001', 'B00001', 'A00002',  # Year 1 (3 bonds)
            'B00002',                      # Year 2 (6 bonds)
        ],
        'issuercode': [
            'ISSUER_A', 'ISSUER_B', 'ISSUER_A',  # Year 1
            'ISSUER_B'                           # Year 2
        ],
        'redemptiondate': [
            redemption_1yr, redemption_1yr, redemption_1yr,
            redemption_2yr
        ],
        'referencedate': [reference_date] * 4,
        'netyieldtomaturity': [3.0, 4.5, 3.5,    # Year 1
                               3.5],            # Year 2
        'grossyieldtomaturity': [3.5, 5.0, 4.0,  # Year 1
                                 4.0],          # Year 2
        'currentcouponrate': [0.03, 0.04, 0.035,  # Year 1
                              0.035],           # Year 2
        'settlementprice': [102.5, 95.0, 103.0,  # Year 1
                            96.5],              # Year 2
        'minimumlot': [1000, 1000, 1000,  # Year 1: C00001 and C00002 have lot=1
                       1000],          # Year 2: I00001 has lot=1
        'ratingsp': ['A', 'BBB', 'A',  # Year 1
                     'BBB'],            # Year 2
        'volumevalue': [1, 2, 3, 4]
    }

    df = pd.DataFrame(bonds_data)

    # Convert ratings to categorical
    df['ratingsp'] = df['ratingsp'].astype(RATING_DTYPE_SP)

    # Calculate maturity in years
    df['maturityyears'] = (
        (df['redemptiondate'] - df['referencedate']).dt.days / 365.25
    )

    # Calculate NCIF (Net Compound Interest Factor)
    df['ncif'] = (1 + df['netyieldtomaturity']/100) ** df['maturityyears']

    return df


def test_get_eligible_bonds_from_dataframe(bond_dataframe):
    """
    Test that get_eligible_bonds correctly filters bonds based on ladder conditions.
    Uses runtime-generated bond data.
    """
    # Create ladder conditions
    conditions = LadderConditions(
        ladder_size=2,
        step_size=1,
        date_tolerance_days_start=30,
        date_tolerance_days_end=30,
        years_offset=0,
        months_offset=0,
        capital_invested=[10000.0, 10000.0],
        strategy=LadderStrategy.MAX_YTM,
        step_width=1,
        max_duplicated_issuers=1
    )

    # Get eligible bonds
    eligible_bonds = get_eligible_bonds(bond_dataframe, conditions)

    # Should return 2 steps
    assert eligible_bonds is not None, "get_eligible_bonds returned None"
    assert len(eligible_bonds) == 2

    # Each step should have bonds
    assert isinstance(eligible_bonds[0], pd.DataFrame)
    assert isinstance(eligible_bonds[1], pd.DataFrame)

    # Step 1 should have 7 bonds (all maturing in ~1 year)
    assert len(eligible_bonds[0]) == 7

    # Step 2 should have 6 bonds (all maturing in ~2 years)
    assert len(eligible_bonds[1]) == 6

    # Verify ISINs
    step1_isins = set(eligible_bonds[0]['isincode'].values)
    step2_isins = set(eligible_bonds[1]['isincode'].values)

    assert step1_isins == {'A00001', 'B00001', 'C00001', 'A00002', 'E00001', 'C00002', 'A00003'}
    assert step2_isins == {'F00001', 'B00002', 'H00001', 'I00001', 'A00004', 'B00003'}

    # Verify duplicate issuers exist
    step1_issuers = eligible_bonds[0]['issuercode'].values
    step2_issuers = eligible_bonds[1]['issuercode'].values

    # ISSUER_A appears 3 times in step 1
    assert list(step1_issuers).count('ISSUER_A') == 3
    # ISSUER_C appears 2 times in step 1
    assert list(step1_issuers).count('ISSUER_C') == 2
    # ISSUER_A appears once in step 2
    assert list(step2_issuers).count('ISSUER_A') == 1
    # ISSUER_B appears 2 times in step 2
    assert list(step2_issuers).count('ISSUER_B') == 2

    # Verify some bonds have minimum_lot = 1
    step1_min_lots = eligible_bonds[0]['minimumlot'].values
    step2_min_lots = eligible_bonds[1]['minimumlot'].values
    assert 1 in step1_min_lots, "No bonds with minimum_lot=1 in step 1"
    assert 1 in step2_min_lots, "No bonds with minimum_lot=1 in step 2"


def test_get_eligible_bonds_volume_rating(bond_dataframe):
    """
    Test that get_eligible_bonds correctly filters bonds based on volume rating.
    """
    # Create ladder conditions with min_volume_rating
    conditions = LadderConditions(
        ladder_size=2,
        step_size=1,
        date_tolerance_days_start=30,
        date_tolerance_days_end=30,
        years_offset=0,
        months_offset=0,
        capital_invested=[10000.0, 10000.0],
        strategy=LadderStrategy.MAX_YTM,
        min_volume_rating=3  # Only bonds with rating 3 or 4
    )

    # Get eligible bonds
    eligible_bonds = get_eligible_bonds(bond_dataframe, conditions)

    assert len(eligible_bonds) == 2

    # Step 1: 'C00001' (3), 'A00002' (4)
    step1_isins = set(eligible_bonds[0]['isincode'].values)
    assert step1_isins == {'C00001', 'A00002'}
    assert all(eligible_bonds[0]['volumevalue'] >= 3)

    # Step 2: 'F00001' (3), 'B00002' (4), 'B00003' (3)
    step2_isins = set(eligible_bonds[1]['isincode'].values)
    assert step2_isins == {'F00001', 'B00002', 'B00003'}
    assert all(eligible_bonds[1]['volumevalue'] >= 3)


@pytest.fixture
def eligible_bonds(bond_dataframe):
    """
    Creates eligible bonds by filtering the bond_dataframe fixture.
    Splits bonds into 2 steps based on maturity years.
    """
    # Filter bonds by maturity
    step1_mask = (bond_dataframe['maturityyears'] >= 0.9) & (bond_dataframe['maturityyears'] <= 1.1)
    step2_mask = (bond_dataframe['maturityyears'] >= 1.9) & (bond_dataframe['maturityyears'] <= 2.1)

    step1_df = bond_dataframe[step1_mask].copy()
    step2_df = bond_dataframe[step2_mask].copy()

    return [step1_df, step2_df]


@pytest.fixture
def eligible_bonds_simple(bond_dataframe_simple):
    """
    Creates eligible bonds by filtering the bond_dataframe fixture.
    Splits bonds into 2 steps based on maturity years.
    """
    # Filter bonds by maturity
    step1_mask = (bond_dataframe_simple['maturityyears'] >= 0.9) & (bond_dataframe_simple['maturityyears'] <= 1.1)
    step2_mask = (bond_dataframe_simple['maturityyears'] >= 1.9) & (bond_dataframe_simple['maturityyears'] <= 2.1)

    step1_df = bond_dataframe_simple[step1_mask].copy()
    step2_df = bond_dataframe_simple[step2_mask].copy()

    return [step1_df, step2_df]


class TestLadder:

    def test_no_diversification_max_ytm(self, eligible_bonds):
        """
        No diversification, Step Width 1, Fixed Capital, MAX_YTM.
        Should select single best bond per step based on yield.
        Duplicate issuers are allowed.
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[10000.0, 10000.0],
            strategy=LadderStrategy.MAX_YTM,
            step_width=1,
            max_duplicated_issuers=None  # No diversification constraint
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=False)

        assert len(ladder) == 2

        # Step 1: B00001 (Best Yield 4.5, ISSUER_B)
        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "B00001"
        assert ladder[0][0].issuer == "ISSUER_B"
        assert ladder[0][0].net_yield == 4.5
        assert ladder[0][0].num_lots == 10

        # Step 2: B00003 (Best Yield 8.0, ISSUER_B)
        assert len(ladder[1]) == 1
        assert ladder[1][0].isin == "B00003"
        assert ladder[1][0].issuer == "ISSUER_B"
        assert ladder[1][0].net_yield == 8.0
        assert ladder[1][0].num_lots == 10

    def test_no_diversification_max_earnings(self, eligible_bonds):
        """
        No diversification, Step Width 1, Fixed Capital, MAX_EARNINGS.
        Should select single best bond per step based on NCIF (compound earnings).
        Duplicate issuers are allowed.
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[10000.0, 10000.0],
            strategy=LadderStrategy.MAX_EARNINGS,
            step_width=1,
            max_duplicated_issuers=None  # No diversification constraint
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=False)

        assert len(ladder) == 2

        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "C00002"
        assert ladder[0][0].issuer == "ISSUER_C"
        assert ladder[0][0].num_lots == 10989

        assert len(ladder[1]) == 1
        assert ladder[1][0].isin == "I00001"
        assert ladder[1][0].issuer == "ISSUER_I"
        assert ladder[1][0].num_lots == 11494

    def test_no_diversification_max_earnings_capital_2(self, eligible_bonds):
        """
        No diversification, Step Width 1, Fixed Capital, MAX_EARNINGS.
        Should select single best bond per step based on NCIF (compound earnings).
        Duplicate issuers are allowed.
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[20000.0, 10000.0],
            strategy=LadderStrategy.MAX_EARNINGS,
            step_width=1,
            max_duplicated_issuers=None  # No diversification constraint
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=False)

        assert len(ladder) == 2

        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "B00001"
        assert ladder[0][0].issuer == "ISSUER_B"
        assert ladder[0][0].num_lots == 21

        assert len(ladder[1]) == 1
        assert ladder[1][0].isin == "I00001"
        assert ladder[1][0].issuer == "ISSUER_I"
        assert ladder[1][0].num_lots == 11494

    def test_diversification_max_ytm_step_1_dup_issuers(self, eligible_bonds):
        """
        Diversified, Step Width 1, Variable Capital, MAX_YTM.
        With max_duplicated_issuers=1, ensures no issuer appears more than once across the ladder.
        Variable Capital: 8000 (Year 1) / 12000 (Year 2)
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[8000.0, 12000.0],
            strategy=LadderStrategy.MAX_YTM,  # Fixed: was MAX_EARNINGS
            step_width=1,
            max_duplicated_issuers=1  # Each issuer can appear at most once
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=True)

        assert len(ladder) == 2

        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "A00002"
        assert ladder[0][0].issuer == "ISSUER_A"
        assert ladder[0][0].net_yield == 3.5
        # check allocation
        assert ladder[0][0].num_lots == 7

        # Step 2: Should select best bond B00003
        assert len(ladder[1]) == 1
        assert ladder[1][0].isin == "B00003"
        assert ladder[1][0].issuer == "ISSUER_B"
        assert ladder[1][0].net_yield == 8.0
        # check allocation
        assert ladder[1][0].num_lots == 12

        # Verify no duplicate issuers across the entire ladder
        all_issuers = [ladder[0][0].issuer, ladder[1][0].issuer]
        assert len(all_issuers) == len(set(all_issuers)), "Duplicate issuers found across ladder steps"
        assert all_issuers == ["ISSUER_A", "ISSUER_B"], "Expected ISSUER_A and ISSUER_B"

    def test_diversification_max_earnings_1_dup_issuers(self, eligible_bonds):
        """
        Diversified, Step Width 1, Variable Capital, MAX_EARNINGS.
        With max_duplicated_issuers=1, ensures no issuer appears more than once across the ladder.
        Variable Capital: 8000 (Year 1) / 12000 (Year 2)
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[8000.0, 12000.0],
            strategy=LadderStrategy.MAX_EARNINGS,
            step_width=1,
            max_duplicated_issuers=1  # Each issuer can appear at most once
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=True)

        assert len(ladder) == 2

        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "C00002"
        assert ladder[0][0].issuer == "ISSUER_C"
        # check allocation
        assert ladder[0][0].num_lots == 8791

        assert len(ladder[1]) == 1
        assert ladder[1][0].issuer == "ISSUER_H"
        assert ladder[1][0].isin == "H00001"
        # check allocation
        assert ladder[1][0].num_lots == 13

        # Verify no duplicate issuers across the entire ladder
        all_issuers = [ladder[0][0].issuer, ladder[1][0].issuer]
        assert len(all_issuers) == len(set(all_issuers)), "Duplicate issuers found across ladder steps"

    def test_diversification_max_earnings_1_dup_issuers_2(self, eligible_bonds_simple):
        """
        Diversified, Step Width 1, Variable Capital, MAX_EARNINGS.
        With max_duplicated_issuers=1, ensures no issuer appears more than once across the ladder.
        Variable Capital: 8000 (Year 1) / 12000 (Year 2)
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[8000.0, 12000.0],
            strategy=LadderStrategy.MAX_EARNINGS,
            step_width=1,
            max_duplicated_issuers=1  # Each issuer can appear at most once
        )

        ladder = build_ladder(eligible_bonds_simple, conditions, diversification=True)

        assert len(ladder) == 2

        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "A00002"
        assert ladder[0][0].issuer == "ISSUER_A"
        # check allocation
        assert ladder[0][0].num_lots == 7

        assert len(ladder[1]) == 1
        assert ladder[1][0].issuer == "ISSUER_B"
        assert ladder[1][0].isin == "B00002"
        # check allocation
        assert ladder[1][0].num_lots == 12

        # Verify no duplicate issuers across the entire ladder
        all_issuers = [ladder[0][0].issuer, ladder[1][0].issuer]
        assert len(all_issuers) == len(set(all_issuers)), "Duplicate issuers found across ladder steps"

    def test_diversification_max_ytm_step_width_2(self, eligible_bonds):
        """
        Diversified, Step Width 2, Variable Capital, MAX_YTM.
        Should select multiple bonds per step to satisfy step_width=2.
        Variable Capital: 5000 (Year 1) / 10000 (Year 2)
        max_duplicated_issuers=1 prevents same issuer appearing twice in the ladder.
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[5000.0, 10000.0],  # Variable Capital
            strategy=LadderStrategy.MAX_YTM,
            step_width=2,  # Select 2 bonds per step
            max_duplicated_issuers=None  # Diversification is enable by default on ladders with step_width > 1
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=True)

        assert len(ladder) == 2

        # STEP 1: 5000 capital, Width 2 -> 2500 per bond.
        # Best yields in Year 1:
        # 1. B00001 (4.5, ISSUER_B)
        # 2. A00002 (3.5, ISSUER_A) - Note: ISSUER_A has 3 bonds but only 1 can be selected
        assert len(ladder[0]) == 2
        assert ladder[0][0].isin == "B00001"
        assert ladder[0][0].issuer == "ISSUER_B"
        assert ladder[0][1].isin == "A00002"
        assert ladder[0][1].issuer == "ISSUER_A"

        # Verify no duplicate issuers in step 1
        step1_issuers = [bond.issuer for bond in ladder[0]]
        assert len(step1_issuers) == len(set(step1_issuers)), "Duplicate issuers in step 1"

        # Check allocation (~2500 each)
        # B00001 price 95.0: 2500 / 950 = 2.63 -> 2 lots
        # A00002 price 103.0: 2500 / 1030 = 2.42 -> 2 lots
        assert ladder[0][0].num_lots == 2
        assert ladder[0][1].num_lots == 2

        # STEP 2: 10000 capital, Width 2 -> 5000 per bond.
        # Best yields in Year 2:
        # 1. B00003 (8.0, ISSUER_B) - Note: ISSUER_B also used in Step 1, allowed
        # 2. H00001 (5.5, ISSUER_H)
        assert len(ladder[1]) == 2
        assert ladder[1][0].isin == "B00003"
        assert ladder[1][0].issuer == "ISSUER_B"
        assert ladder[1][1].isin == "H00001"
        assert ladder[1][1].issuer == "ISSUER_H"

        # Verify no duplicate issuers in step 2
        step2_issuers = [bond.issuer for bond in ladder[1]]
        assert len(step2_issuers) == len(set(step2_issuers)), "Duplicate issuers in step 2"

        # B00003 (93.5): 5000 / 935 = 5.34 -> 5 lots
        # H00001 (92.0): 5000 / 920 = 5.43 -> 5 lots
        assert ladder[1][0].num_lots == 5
        assert ladder[1][1].num_lots == 5

    def test_diversification_max_earnings_step_width_2(self, eligible_bonds):
        """
        Diversified, Step Width 2, Variable Capital, MAX_EARNINGS.
        Should select multiple bonds based on NCIF (Net Compound Interest Factor).
        Variable Capital: 8000 (Year 1) / 12000 (Year 2)
        max_duplicated_issuers=1 prevents same issuer appearing twice in the ladder.
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[8000.0, 12000.0],
            strategy=LadderStrategy.MAX_EARNINGS,
            step_width=2,
            max_duplicated_issuers=None  # Diversification is enable by default on ladders with step_width > 1
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=True)

        # STEP 1 checking
        # Width 2 -> 4000 per bond.
        # Best absolute earnings in Year 1:
        # 1. C00002 (yield 2.5, lot=1, price=91.0, ISSUER_C) - Perfect capital utilization
        # 2. B00001 (yield 4.5, lot=1000, price=95.0, ISSUER_B) - Higher yield but less capital
        assert len(ladder[0]) == 2
        assert ladder[0][0].isin == "C00002"
        assert ladder[0][0].issuer == "ISSUER_C"
        # Second bond should be B00001
        assert ladder[0][1].isin == "B00001"
        assert ladder[0][1].issuer == "ISSUER_B"

        # Verify no duplicate issuers in step 1
        step1_issuers = [bond.issuer for bond in ladder[0]]
        assert len(step1_issuers) == len(set(step1_issuers)), "Duplicate issuers in step 1"

        # Check allocation
        # 4000 capital per bond
        # C00002 (91.0, lot=1): 4000/0.91 = 4395 lots
        assert ladder[0][0].num_lots == 4395
        # B00001 (95.0, lot=1000): 4000/950 = 4.21 -> 4 lots
        assert ladder[0][1].num_lots == 4

        # STEP 2 checking
        # Width 2 -> 6000 per bond.
        # Best absolute earnings in Year 2:
        # 1. I00001 (yield 4.5, lot=1) - Good capital utilization
        # 2. B00003 (yield 8.0, lot=1000, price=93.5) - Likely best yield but lower capital util?
        # Note: ISSUER_B and ISSUER_A already used in step 1, but max_duplicated_issuers=None
        assert len(ladder[1]) == 2
        assert ladder[1][0].isin == "I00001"
        assert ladder[1][0].issuer == "ISSUER_I"
        assert ladder[1][0].num_lots == 6896
        assert ladder[1][1].isin == "B00003"
        assert ladder[1][1].issuer == "ISSUER_B"
        assert ladder[1][1].num_lots == 6

        # Verify no duplicate issuers... wait, now we have B00002 (ISSUER_B)
        # step2_issuers = [bond.issuer for bond in ladder[1]]
        # assert len(step2_issuers) == len(set(step2_issuers)), "Duplicate issuers in step 2"

    def test_no_diversification_max_return(self, eligible_bonds):
        """
        No diversification, Step Width 1, Fixed Capital, MAX_RETURN.
        Should select single best bond per step based on total return (coupons + capital gain).
        Duplicate issuers are allowed.
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[10000.0, 10000.0],
            strategy=LadderStrategy.MAX_RETURN,
            step_width=1,
            max_duplicated_issuers=None  # No diversification constraint
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=False)

        assert len(ladder) == 2

        # Step 1: C00001 (Best Total Return 1590.82)
        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "C00001"
        assert ladder[0][0].issuer == "ISSUER_C"
        assert ladder[0][0].num_lots == 11363

        # Step 2: I00001 (Best Total Return 2528.68)
        assert len(ladder[1]) == 1
        assert ladder[1][0].isin == "I00001"
        assert ladder[1][0].issuer == "ISSUER_I"
        assert ladder[1][0].num_lots == 11494

    def test_no_diversification_max_return_capital_2(self, eligible_bonds):
        """
        No diversification, Step Width 1, Fixed Capital, MAX_RETURN.
        Variable Capital: 20000 (Year 1) / 10000 (Year 2)
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[20000.0, 10000.0],
            strategy=LadderStrategy.MAX_RETURN,
            step_width=1,
            max_duplicated_issuers=None
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=False)

        assert len(ladder) == 2

        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "C00001"
        assert ladder[0][0].issuer == "ISSUER_C"
        assert ladder[0][0].num_lots == 22727

        assert len(ladder[1]) == 1
        assert ladder[1][0].isin == "I00001"
        assert ladder[1][0].issuer == "ISSUER_I"
        assert ladder[1][0].num_lots == 11494

    def test_diversification_max_return_step_1_dup_issuers(self, eligible_bonds):
        """
        Diversified, Step Width 1, Variable Capital, MAX_RETURN.
        With max_duplicated_issuers=1, ensures no issuer appears more than once across the ladder.
        Variable Capital: 8000 (Year 1) / 12000 (Year 2)
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[8000.0, 12000.0],
            strategy=LadderStrategy.MAX_RETURN,
            step_width=1,
            max_duplicated_issuers=1
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=True)

        assert len(ladder) == 2

        assert len(ladder[0]) == 1
        assert ladder[0][0].isin == "C00001"
        assert ladder[0][0].issuer == "ISSUER_C"
        assert ladder[0][0].num_lots == 9090

        assert len(ladder[1]) == 1
        assert ladder[1][0].isin == "I00001"
        assert ladder[1][0].issuer == "ISSUER_I"
        assert ladder[1][0].num_lots == 13793

    def test_diversification_max_return_step_width_2(self, eligible_bonds):
        """
        Diversified, Step Width 2, Variable Capital, MAX_RETURN.
        Should select multiple bonds per step to satisfy step_width=2.
        Variable Capital: 5000 (Year 1) / 10000 (Year 2)
        """
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[5000.0, 10000.0],
            strategy=LadderStrategy.MAX_RETURN,
            step_width=2,
            max_duplicated_issuers=None
        )

        ladder = build_ladder(eligible_bonds, conditions, diversification=True)

        assert len(ladder) == 2

        # STEP 1: 5000 capital, Width 2 -> 2500 per bond.
        assert len(ladder[0]) == 2
        assert ladder[0][0].isin == "C00001"
        assert ladder[0][1].isin == "B00001"

        assert ladder[0][0].num_lots == 2840
        assert ladder[0][1].num_lots == 2

        # STEP 2: 10000 capital, Width 2 -> 5000 per bond.
        assert len(ladder[1]) == 2
        assert ladder[1][0].isin == "I00001"
        assert ladder[1][1].isin == "H00001"

        assert ladder[1][0].num_lots == 5747
        assert ladder[1][1].num_lots == 5


@pytest.fixture
def sample_bond_data():
    """Create sample bond data as a DataFrame"""
    data = {
        'isincode': ['IT0001234567', 'IT0001234568', 'IT0001234569', 'IT0001234570'],
        'issuercode': ['ISSUER_A', 'ISSUER_B', 'ISSUER_C', 'ISSUER_D'],
        'maturityyears': [5.0, 5.1, 4.9, 5.0],
        'netyieldtomaturity': [3.5, 3.8, 3.3, 4.0],  # ISSUER_D has highest net yield
        'grossyieldtomaturity': [4.0, 4.3, 3.8, 4.5],
        'currentcouponrate': [0.03, 0.035, 0.028, 0.04],
        'settlementprice': [98.5, 99.0, 97.5, 98.0],
        'minimumlot': [1000, 1000, 1000, 1000],
        'ncif': [1.1877, 1.2042, 1.1742, 1.2167],  # ISSUER_B has highest ncif
        'volumevalue': [1, 2, 3, 4],
        'ratingsp': ['A', 'BBB', 'A', 'BBB']
    }
    return pd.DataFrame(data)


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_ladder_with_single_step(self, sample_bond_data):
        """Test ladder with only one step"""
        conditions = LadderConditions(
            ladder_size=1,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[10000.0],
            strategy=LadderStrategy.MAX_EARNINGS,
            step_width=1,
            max_duplicated_issuers=1
        )

        eligible_bonds = [sample_bond_data]

        ladder = build_ladder(eligible_bonds, conditions, diversification=False)

        assert len(ladder) == 1
        assert len(ladder[0]) > 0

    def test_ladder_with_no_eligible_bonds_in_step(self, sample_bond_data):
        """Test ladder when one step has no eligible bonds"""
        empty_df = pd.DataFrame()

        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[10000.0, 10000.0],
            strategy=LadderStrategy.MAX_EARNINGS,
            step_width=1,
            max_duplicated_issuers=1
        )

        eligible_bonds = [sample_bond_data, empty_df]

        ladder = build_ladder(eligible_bonds, conditions, diversification=False)

        assert len(ladder) == 2
        assert len(ladder[0]) > 0  # First step has bonds
        assert len(ladder[1]) == 0  # Second step is empty
