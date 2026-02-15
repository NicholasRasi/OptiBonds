"""
Tests for bond_calc.utils module
"""
import pytest
from optibonds.models import BondSimple
from optibonds.utils import (
    allocate_capital_to_bond,
    allocate_capital_to_bonds,
    compute_permutations_bonds,
    get_annualized_earning,
    get_annualized_earnings,
    get_compounding_earning,
    get_compounding_earnings,
    compute_mean_weighted_maturity,
    compute_bond_coupons,
    compute_bonds_coupons,
    compute_bond_capital_gain,
    compute_bonds_capital_gain,
    compute_total_gain_yield,
    compute_total_simple_yield,
    compute_net_value,
)


@pytest.fixture
def sample_bond():
    """Create a sample bond for testing"""
    return BondSimple(
        isin="IT0001234567",
        issuer="ISSUER_A",
        maturity_years=5.0,
        net_yield=3.5,
        gross_yield=4.0,
        current_coupon_rate=0.03,
        settlement_price=98.5,
        minimum_lot=1000,
        ncif=1.1877  # (1.035)^5
    )


@pytest.fixture
def sample_bond_2():
    """Create another sample bond for testing"""
    return BondSimple(
        isin="IT0009876543",
        issuer="ISSUER_B",
        maturity_years=3.0,
        net_yield=2.8,
        gross_yield=3.2,
        current_coupon_rate=0.025,
        settlement_price=99.0,
        minimum_lot=1000,
        ncif=1.0869  # (1.028)^3
    )


class TestCapitalAllocation:
    """Tests for capital allocation functions"""

    def test_allocate_capital_to_bond(self, sample_bond):
        """Test allocating capital to a single bond"""
        capital = 10000.0
        result = allocate_capital_to_bond(sample_bond, capital)

        # Check that capital was allocated
        assert result.capital_invested > 0
        assert result.num_lots > 0

        # Capital invested should not exceed available capital
        assert result.capital_invested <= capital

        # Verify calculation
        expected_num_lots = int(capital / (sample_bond.minimum_lot * sample_bond.settlement_price / 100))
        assert result.num_lots == expected_num_lots

    def test_allocate_capital_insufficient(self, sample_bond):
        """Test allocation with insufficient capital"""
        capital = 100.0  # Not enough for even one lot
        result = allocate_capital_to_bond(sample_bond, capital)

        assert result.num_lots == 0
        assert result.capital_invested == 0

    def test_allocate_capital_to_bonds(self, sample_bond, sample_bond_2):
        """Test allocating capital to multiple bonds"""
        bonds = [sample_bond, sample_bond_2]
        capital_invested = [10000.0, 15000.0]

        result = allocate_capital_to_bonds(bonds, capital_invested)

        assert len(result) == 2
        assert result[0].capital_invested > 0
        assert result[1].capital_invested > 0
        assert result[0].num_lots > 0
        assert result[1].num_lots > 0

        # Verify calculation
        expected_num_lots_1 = int(capital_invested[0] / (sample_bond.minimum_lot * sample_bond.settlement_price / 100))
        expected_num_lots_2 = int(capital_invested[1] /
                                  (sample_bond_2.minimum_lot * sample_bond_2.settlement_price / 100))
        assert result[0].num_lots == expected_num_lots_1
        assert result[1].num_lots == expected_num_lots_2


class TestEarningsCalculations:
    """Tests for earnings calculation functions"""

    def test_get_compounding_earning(self, sample_bond):
        """Test compounding earning calculation for a single bond"""
        sample_bond.capital_invested = 10000.0

        earning = get_compounding_earning(sample_bond)

        # Should be capital * ncif
        expected = 10000.0 * sample_bond.ncif
        assert abs(earning - expected) < 0.01

    def test_get_compounding_earnings(self, sample_bond, sample_bond_2):
        """Test compounding earnings for multiple bonds"""
        sample_bond.capital_invested = 10000.0
        sample_bond_2.capital_invested = 15000.0

        bonds = [sample_bond, sample_bond_2]
        total_earning = get_compounding_earnings(bonds)

        expected = (10000.0 * sample_bond.ncif) + (15000.0 * sample_bond_2.ncif)
        assert abs(total_earning - expected) < 0.01

    def test_get_annualized_earning(self, sample_bond):
        """Test annualized earning calculation"""
        sample_bond.capital_invested = 10000.0

        earning = get_annualized_earning(sample_bond)

        # Should be capital * (net_yield / 100)
        expected = 10000.0 * (sample_bond.net_yield / 100)
        assert abs(earning - expected) < 0.01

    def test_get_annualized_earnings(self, sample_bond, sample_bond_2):
        """Test annualized earnings for multiple bonds"""
        sample_bond.capital_invested = 10000.0
        sample_bond_2.capital_invested = 15000.0

        bonds = [sample_bond, sample_bond_2]
        total_earning = get_annualized_earnings(bonds)

        expected = (10000.0 * (sample_bond.net_yield / 100)) + (15000.0 * (sample_bond_2.net_yield / 100))
        assert abs(total_earning - expected) < 0.01


class TestPermutations:
    """Tests for permutation generation"""

    def test_compute_permutations_bonds_simple(self, sample_bond, sample_bond_2):
        """Test simple permutation generation"""
        # Create a simple 2x2 matrix
        bond_a1 = BondSimple(
            isin="A1",
            issuer="ISSUER_A",
            maturity_years=1.0,
            net_yield=3.0,
            gross_yield=3.5,
            current_coupon_rate=0.03,
            settlement_price=100,
            minimum_lot=1000,
            ncif=1.03
        )
        bond_a2 = BondSimple(
            isin="A2",
            issuer="ISSUER_A",
            maturity_years=1.0,
            net_yield=3.0,
            gross_yield=3.5,
            current_coupon_rate=0.03,
            settlement_price=100,
            minimum_lot=1000,
            ncif=1.03
        )
        bond_b1 = BondSimple(
            isin="B1",
            issuer="ISSUER_B",
            maturity_years=2.0,
            net_yield=4.0,
            gross_yield=4.5,
            current_coupon_rate=0.04,
            settlement_price=100,
            minimum_lot=1000,
            ncif=1.08
        )
        bond_b2 = BondSimple(
            isin="B2",
            issuer="ISSUER_B",
            maturity_years=2.0,
            net_yield=4.0,
            gross_yield=4.5,
            current_coupon_rate=0.04,
            settlement_price=100,
            minimum_lot=1000,
            ncif=1.08
        )

        matrix = [[bond_a1, bond_a2], [bond_b1, bond_b2]]

        result = compute_permutations_bonds(matrix, max_duplicated_issuers=1)

        # With max_duplicated_issuers=1, we should have 4 permutations (2x2)
        assert len(result) == 4

        # Check that specific valid permutations are present
        perm_isins = [set(b.isin for b in p) for p in result]
        assert {'A1', 'B1'} in perm_isins
        assert {'A1', 'B2'} in perm_isins
        assert {'A2', 'B1'} in perm_isins
        assert {'A2', 'B2'} in perm_isins

    def test_compute_permutations_bonds_with_issuer_limit(self):
        """Test permutation generation with issuer constraints"""
        # All bonds from same issuer
        bond1 = BondSimple(
            isin="A1",
            issuer="ISSUER_A",
            maturity_years=1.0,
            net_yield=3.0,
            gross_yield=3.5,
            current_coupon_rate=0.03,
            settlement_price=100,
            minimum_lot=1000,
            ncif=1.03
        )
        bond2 = BondSimple(
            isin="A2",
            issuer="ISSUER_A",
            maturity_years=2.0,
            net_yield=3.0,
            gross_yield=3.5,
            current_coupon_rate=0.03,
            settlement_price=100,
            minimum_lot=1000,
            ncif=1.06
        )
        bond3 = BondSimple(
            isin="A3",
            issuer="ISSUER_A",
            maturity_years=3.0,
            net_yield=3.0,
            gross_yield=3.5,
            current_coupon_rate=0.03,
            settlement_price=100,
            minimum_lot=1000,
            ncif=1.09
        )

        matrix = [[bond1], [bond2], [bond3]]

        # With max_duplicated_issuers=1, should have 0 permutations (can't use same issuer 3 times)
        result = compute_permutations_bonds(matrix, max_duplicated_issuers=1)
        assert len(result) == 0

        # With max_duplicated_issuers=3, should have 1 permutation
        result = compute_permutations_bonds(matrix, max_duplicated_issuers=3)
        assert len(result) == 1

        # Check valid permutation
        perm_isins = set(b.isin for b in result[0])
        assert perm_isins == {'A1', 'A2', 'A3'}


class TestYieldCalculations:
    """Tests for yield calculation functions"""

    def test_compute_mean_weighted_maturity(self, sample_bond, sample_bond_2):
        """Test mean weighted maturity calculation"""
        sample_bond.capital_invested = 10000.0
        sample_bond_2.capital_invested = 10000.0

        bonds = [sample_bond, sample_bond_2]

        # Use 0.3/0.7 ratio
        capital_1 = 3000.0
        capital_2 = 7000.0
        sample_bond.capital_invested = capital_1
        sample_bond_2.capital_invested = capital_2
        total_capital = capital_1 + capital_2

        mean_maturity = compute_mean_weighted_maturity(bonds, total_capital)

        # Should be weighted average
        weight_1 = capital_1 / total_capital
        weight_2 = capital_2 / total_capital
        expected = (sample_bond.maturity_years * weight_1) + (sample_bond_2.maturity_years * weight_2)
        assert abs(mean_maturity - expected) < 0.01


class TestCouponCalculations:
    """Tests for coupon calculation functions"""

    def test_compute_bond_coupons(self, sample_bond):
        """Test coupon calculation for a single bond"""
        sample_bond.num_lots = 10

        coupons = compute_bond_coupons(sample_bond)

        # coupons = num_lots * minimum_lot * coupon_rate * maturity_years
        expected = sample_bond.num_lots * sample_bond.minimum_lot * sample_bond.current_coupon_rate * sample_bond.maturity_years
        assert abs(coupons - expected) < 0.01

    def test_compute_bonds_coupons(self, sample_bond, sample_bond_2):
        """Test coupon calculation for multiple bonds"""
        sample_bond.num_lots = 10
        sample_bond_2.num_lots = 15

        bonds = [sample_bond, sample_bond_2]
        total_coupons = compute_bonds_coupons(bonds)

        expected = (
            (sample_bond.num_lots * sample_bond.minimum_lot * sample_bond.current_coupon_rate * sample_bond.maturity_years) +
            (sample_bond_2.num_lots * sample_bond_2.minimum_lot *
             sample_bond_2.current_coupon_rate * sample_bond_2.maturity_years)
        )
        assert abs(total_coupons - expected) < 0.01


class TestCapitalGainCalculations:
    """Tests for capital gain calculation functions"""

    def test_compute_bond_capital_gain(self, sample_bond):
        """Test capital gain calculation for a single bond"""
        sample_bond.num_lots = 10
        sample_bond.capital_invested = 9850.0  # 10 lots * 1000 * 98.5%

        capital_gain = compute_bond_capital_gain(sample_bond)

        # nominal = 10 * 1000 = 10000
        # capital_gain = 10000 - 9850 = 150
        expected = 10000 - 9850
        assert abs(capital_gain - expected) < 0.01

    def test_compute_bonds_capital_gain(self, sample_bond, sample_bond_2):
        """Test capital gain for multiple bonds"""
        sample_bond.num_lots = 10
        sample_bond.capital_invested = 9850.0
        sample_bond_2.num_lots = 15
        sample_bond_2.capital_invested = 14850.0

        bonds = [sample_bond, sample_bond_2]
        total_gain = compute_bonds_capital_gain(bonds)

        expected = (10000 - 9850) + (15000 - 14850)
        assert abs(total_gain - expected) < 0.01


class TestTotalYieldCalculations:
    """Tests for total yield calculation functions"""

    def test_compute_total_gain_yield(self):
        """Test total gain yield calculation"""
        total_coupons = 1500.0
        total_capital_gain = 150.0
        total_capital_invested = 10000.0

        yield_val = compute_total_gain_yield(total_coupons, total_capital_gain, total_capital_invested)

        # (total_capital + total_coupons + total_capital_gain) / total_capital - 1
        expected = ((total_capital_invested + total_coupons + total_capital_gain) / total_capital_invested) - 1
        assert abs(yield_val - expected) < 0.001

    def test_compute_total_simple_yield(self):
        """Test total simple yield calculation"""
        total_coupons = 1500.0
        total_capital_gain = 150.0
        total_capital_invested = 10000.0
        mean_weighted_maturity = 5.0

        yield_val = compute_total_simple_yield(
            total_coupons, total_capital_gain, total_capital_invested, mean_weighted_maturity
        )

        # Should be total_gain_yield / maturity
        total_gain = ((total_capital_invested + total_coupons + total_capital_gain) / total_capital_invested) - 1
        expected = total_gain / mean_weighted_maturity
        assert abs(yield_val - expected) < 0.001


class TestTaxCalculations:
    """Tests for tax calculation functions"""

    def test_compute_net_value(self):
        """Test net value calculation with tax"""
        gross_value = 1000.0

        net_value = compute_net_value(gross_value)

        # Tax rate is 12.5%, so net = 1000 * 0.875 = 875
        expected = 1000.0 * 0.875
        assert abs(net_value - expected) < 0.01


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_zero_capital_allocation(self, sample_bond):
        """Test allocation with zero capital"""
        result = allocate_capital_to_bond(sample_bond, 0.0)

        assert result.num_lots == 0
        assert result.capital_invested == 0

    def test_empty_bond_list_earnings(self):
        """Test earnings calculation with empty bond list"""
        bonds = []

        total_earning = get_compounding_earnings(bonds)
        assert total_earning == 0

        total_annualized = get_annualized_earnings(bonds)
        assert total_annualized == 0

    def test_single_bond_permutation(self, sample_bond):
        """Test permutation with single bond in each step"""
        matrix = [[sample_bond]]

        result = compute_permutations_bonds(matrix, max_duplicated_issuers=1)

        assert len(result) == 1
        assert len(result[0]) == 1
