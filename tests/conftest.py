"""
Shared pytest fixtures and configuration
"""
import pytest
import pandas as pd
from optibonds.models import BondSimple, LadderConditions, LadderStrategy


@pytest.fixture
def simple_bond():
    """Create a simple bond for general testing"""
    return BondSimple(
        isin="IT0000000000",
        issuer="TEST_ISSUER",
        maturity_years=3.0,
        net_yield=3.0,
        gross_yield=3.5,
        current_coupon_rate=0.03,
        settlement_price=100.0,
        minimum_lot=1000,
        ncif=1.0927,
        taxation=0.125,
    )


@pytest.fixture
def bond_dataframe():
    """Create a sample DataFrame of bonds"""
    data = {
        'isincode': ['BOND001', 'BOND002', 'BOND003'],
        'issuercode': ['ISSUER_X', 'ISSUER_Y', 'ISSUER_Z'],
        'maturityyears': [2.0, 3.0, 4.0],
        'netyieldtomaturity': [2.5, 3.0, 3.5],
        'grossyieldtomaturity': [2.9, 3.5, 4.0],
        'currentcouponrate': [0.025, 0.030, 0.035],
        'settlementprice': [100.0, 99.5, 98.0],
        'minimumlot': [1000, 1000, 1000],
        'ncif': [1.051, 1.093, 1.148],
        'taxation': [0.125, 0.125, 0.125],
    }
    return pd.DataFrame(data)


@pytest.fixture
def default_ladder_conditions():
    """Create default ladder conditions for testing"""
    return LadderConditions(
        ladder_size=3,
        step_size=1,
        date_tolerance_days_start=30,
        date_tolerance_days_end=30,
        years_offset=1,
        capital_invested=[10000.0, 10000.0, 10000.0],
        strategy=LadderStrategy.MAX_EARNINGS,
        step_width=1,
        max_duplicated_issuers=1
    )
