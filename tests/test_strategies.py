"""
Tests for bond_calc.strategies module
"""
import pytest
import pandas as pd
from optibonds.models import BondSimple, LadderConditions, LadderStrategy
from optibonds.strategies import (
    select_best_ladder,
    get_best_bond,
    select_strategy_function,
)
from optibonds.utils import (
    get_compounding_earning,
    get_compounding_earnings,
    get_annualized_earning,
    get_annualized_earnings,
)


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
        'ratingsp': ['BBB', 'A', 'BBB-', 'A+']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_bond_data_2():
    """Create another sample bond data as a DataFrame"""
    data = {
        'isincode': ['IT0009876543', 'IT0009876544', 'IT0009876545'],
        'issuercode': ['ISSUER_D', 'ISSUER_E', 'ISSUER_F'],
        'maturityyears': [3.0, 3.1, 2.9],
        'netyieldtomaturity': [2.8, 3.0, 2.7],
        'grossyieldtomaturity': [3.2, 3.4, 3.1],
        'currentcouponrate': [0.025, 0.027, 0.024],
        'settlementprice': [99.0, 99.5, 98.0],
        'minimumlot': [1000, 1000, 1000],
        'ncif': [1.0869, 1.0927, 1.0835],
        'volumevalue': [1, 2, 3],
        'ratingsp': ['BBB-', 'A-', 'BBB']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_bond_data_same_issuer():
    """Create sample bond data with same issuer"""
    data = {
        'isincode': ['IT0001111111', 'IT0001111112', 'IT0001111113'],
        'issuercode': ['ISSUER_A', 'ISSUER_A', 'ISSUER_A'],
        'maturityyears': [5.0, 5.1, 4.9],
        'netyieldtomaturity': [3.5, 3.8, 3.3],
        'grossyieldtomaturity': [4.0, 4.3, 3.8],
        'currentcouponrate': [0.03, 0.035, 0.028],
        'settlementprice': [98.5, 99.0, 97.5],
        'minimumlot': [1000, 1000, 1000],
        'ncif': [1.1877, 1.2042, 1.1742],
        'volumevalue': [4, 3, 2],
        'ratingsp': ['BBB', 'A', 'BBB-']
    }
    return pd.DataFrame(data)

# Convenience fixtures for specific configurations (for tests that need specific setup)


@pytest.fixture
def ladder_conditions_max_earnings():
    """Create ladder conditions with MAX_EARNINGS strategy"""
    return LadderConditions(
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


@pytest.fixture
def ladder_conditions_max_ytm():
    """Create ladder conditions with MAX_YTM strategy"""
    return LadderConditions(
        ladder_size=2,
        step_size=1,
        date_tolerance_days_start=30,
        date_tolerance_days_end=30,
        years_offset=1,
        capital_invested=[10000.0, 10000.0],
        strategy=LadderStrategy.MAX_YTM,
        step_width=1,
        max_duplicated_issuers=1
    )


@pytest.fixture
def ladder_conditions_diversification():
    """Create ladder conditions with step width > 1"""
    return LadderConditions(
        ladder_size=2,
        step_size=1,
        date_tolerance_days_start=30,
        date_tolerance_days_end=30,
        years_offset=1,
        capital_invested=[10000.0, 10000.0],
        strategy=LadderStrategy.MAX_EARNINGS,
        step_width=3,  # Enable ladder with step width > 1
        max_duplicated_issuers=1
    )


class TestStrategyFunctionSelection:
    """Tests for strategy function selection"""

    def test_select_strategy_function_max_earnings_single(self):
        """Test selecting MAX_EARNINGS strategy for single bond"""
        func = select_strategy_function(LadderStrategy.MAX_EARNINGS, lists=False)

        assert func == get_compounding_earning

    def test_select_strategy_function_max_earnings_list(self):
        """Test selecting MAX_EARNINGS strategy for bond list"""
        func = select_strategy_function(LadderStrategy.MAX_EARNINGS, lists=True)

        assert func == get_compounding_earnings

    def test_select_strategy_function_max_ytm_single(self):
        """Test selecting MAX_YTM strategy for single bond"""
        func = select_strategy_function(LadderStrategy.MAX_YTM, lists=False)

        assert func == get_annualized_earning

    def test_select_strategy_function_max_ytm_list(self):
        """Test selecting MAX_YTM strategy for bond list"""
        func = select_strategy_function(LadderStrategy.MAX_YTM, lists=True)

        assert func == get_annualized_earnings

    def test_select_strategy_function_invalid(self):
        """Test selecting invalid strategy raises error"""
        with pytest.raises(ValueError):
            select_strategy_function("INVALID_STRATEGY", lists=False)


class TestGetBestBond:
    """Tests for get_best_bond function"""

    def test_get_best_bond_max_earnings(self, sample_bond_data):
        """Test getting best bond with MAX_EARNINGS strategy"""
        capital = 10000.0

        best_bond = get_best_bond(sample_bond_data, capital, LadderStrategy.MAX_EARNINGS)

        assert best_bond is not None
        assert isinstance(best_bond, BondSimple)
        assert best_bond.capital_invested > 0
        assert best_bond.num_lots > 0

        # Should select the bond with highest ncif (ISSUER_D with 1.2167)
        assert best_bond.issuer == 'ISSUER_D'
        assert best_bond.isin == 'IT0001234570'

    def test_get_best_bond_max_ytm(self, sample_bond_data):
        """Test getting best bond with MAX_YTM strategy"""
        capital = 10000.0

        best_bond = get_best_bond(sample_bond_data, capital, LadderStrategy.MAX_YTM)

        assert best_bond is not None
        assert isinstance(best_bond, BondSimple)

        # Should select the bond with highest net yield (ISSUER_D with 4.0)
        assert best_bond.issuer == 'ISSUER_D'
        assert best_bond.isin == 'IT0001234570'

    def test_get_best_bond_insufficient_capital(self, sample_bond_data):
        """Test getting best bond with insufficient capital"""
        capital = 100.0  # Not enough for any bond

        best_bond = get_best_bond(sample_bond_data, capital, LadderStrategy.MAX_EARNINGS)

        # With insufficient capital, the function still returns the best bond
        # but it will have 0 lots allocated
        if best_bond is not None:
            assert best_bond.num_lots == 0
        # Note: Depending on implementation, it might return None

    def test_get_best_bond_empty_dataframe(self):
        """Test getting best bond from empty DataFrame"""
        empty_df = pd.DataFrame()
        capital = 10000.0

        best_bond = get_best_bond(empty_df, capital, LadderStrategy.MAX_EARNINGS)

        assert best_bond is None


class TestSelectBestLadder:
    """Tests for select_best_ladder function"""

    def test_select_best_ladder_basic(self, ladder_conditions_max_earnings):
        """Test selecting best ladder from permutations"""
        # Create simple bond lists
        bond1_a = BondSimple(
            isin="A1",
            issuer="ISSUER_A",
            maturity_years=5.0,
            net_yield=3.5,
            gross_yield=4.0,
            current_coupon_rate=0.03,
            settlement_price=98.5,
            minimum_lot=1000,
            ncif=1.1877
        )
        bond1_b = BondSimple(
            isin="B1",
            issuer="ISSUER_B",
            maturity_years=5.0,
            net_yield=3.8,
            gross_yield=4.3,
            current_coupon_rate=0.035,
            settlement_price=99.0,
            minimum_lot=1000,
            ncif=1.2042
        )

        bond2_a = BondSimple(
            isin="A2",
            issuer="ISSUER_C",
            maturity_years=3.0,
            net_yield=2.8,
            gross_yield=3.2,
            current_coupon_rate=0.025,
            settlement_price=99.0,
            minimum_lot=1000,
            ncif=1.0869
        )
        bond2_b = BondSimple(
            isin="B2",
            issuer="ISSUER_D",
            maturity_years=3.0,
            net_yield=3.0,
            gross_yield=3.4,
            current_coupon_rate=0.027,
            settlement_price=99.5,
            minimum_lot=1000,
            ncif=1.0927
        )

        bonds = [[bond1_a, bond1_b], [bond2_a, bond2_b]]

        best_ladder = select_best_ladder(bonds, ladder_conditions_max_earnings)

        # Should return a list of bonds
        assert len(best_ladder) == 2
        assert all(isinstance(b, BondSimple) for b in best_ladder)

        # Should select bonds with highest earnings
        # Expected: bond1_b (higher ncif) and bond2_b (higher ncif)
        assert best_ladder[0].issuer == 'ISSUER_B'
        assert best_ladder[1].issuer == 'ISSUER_D'

    def test_select_best_ladder_with_issuer_constraint(self, capsys):
        """Test selecting best ladder with issuer constraints"""
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[10000.0, 10000.0],
            strategy=LadderStrategy.MAX_EARNINGS,
            step_width=1,
            max_duplicated_issuers=1  # Can't use same issuer twice
        )

        # Create bonds where best option would violate issuer constraint
        bond1 = BondSimple(
            isin="A1",
            issuer="ISSUER_A",
            maturity_years=5.0,
            net_yield=4.0,
            gross_yield=4.5,
            current_coupon_rate=0.04,
            settlement_price=98.5,
            minimum_lot=1000,
            ncif=1.22
        )
        bond2_same = BondSimple(
            isin="A2",
            issuer="ISSUER_A",
            maturity_years=3.0,
            net_yield=3.5,
            gross_yield=4.0,
            current_coupon_rate=0.035,
            settlement_price=99.0,
            minimum_lot=1000,
            ncif=1.11
        )
        bond2_diff = BondSimple(
            isin="B2",
            issuer="ISSUER_B",
            maturity_years=3.0,
            net_yield=3.0,
            gross_yield=3.5,
            current_coupon_rate=0.03,
            settlement_price=99.0,
            minimum_lot=1000,
            ncif=1.09
        )

        bonds = [[bond1], [bond2_same, bond2_diff]]

        best_ladder = select_best_ladder(bonds, conditions)

        # Should select bond1 and bond2_diff (different issuers)
        assert len(best_ladder) == 2
        assert best_ladder[0].issuer == 'ISSUER_A'
        assert best_ladder[1].issuer == 'ISSUER_B'

    def test_select_best_ladder_max_ytm(self, capsys):
        """Test selecting best ladder with MAX_YTM strategy"""
        conditions = LadderConditions(
            ladder_size=2,
            step_size=1,
            date_tolerance_days_start=30,
            date_tolerance_days_end=30,
            years_offset=1,
            capital_invested=[10000.0, 10000.0],
            strategy=LadderStrategy.MAX_YTM,
            step_width=1,
            max_duplicated_issuers=1
        )

        bond1_a = BondSimple(
            isin="A1",
            issuer="ISSUER_A",
            maturity_years=5.0,
            net_yield=3.5,
            gross_yield=4.0,
            current_coupon_rate=0.03,
            settlement_price=98.5,
            minimum_lot=1000,
            ncif=1.1877
        )
        bond1_b = BondSimple(
            isin="B1",
            issuer="ISSUER_B",
            maturity_years=5.0,
            net_yield=3.8,
            gross_yield=4.3,
            current_coupon_rate=0.035,
            settlement_price=99.0,
            minimum_lot=1000,
            ncif=1.2042
        )

        bond2_a = BondSimple(
            isin="A2",
            issuer="ISSUER_C",
            maturity_years=3.0,
            net_yield=2.8,
            gross_yield=3.2,
            current_coupon_rate=0.025,
            settlement_price=99.0,
            minimum_lot=1000,
            ncif=1.0869
        )
        bond2_b = BondSimple(
            isin="B2",
            issuer="ISSUER_D",
            maturity_years=3.0,
            net_yield=3.0,
            gross_yield=3.4,
            current_coupon_rate=0.027,
            settlement_price=99.5,
            minimum_lot=1000,
            ncif=1.0927
        )

        bonds = [[bond1_a, bond1_b], [bond2_a, bond2_b]]

        best_ladder = select_best_ladder(bonds, conditions)

        # Should select bonds with highest yields
        assert best_ladder[0].net_yield == 3.8
        assert best_ladder[0].isin == 'B1'
        assert best_ladder[1].net_yield == 3.0
        assert best_ladder[1].isin == 'B2'
