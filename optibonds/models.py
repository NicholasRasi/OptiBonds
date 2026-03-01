# Models
from enum import Enum
import yaml
from typing import Self


class BondSimple:
    def __init__(
            self,
            isin: str,
            issuer: str,
            maturity_years: float,
            net_yield: float,
            gross_yield: float,
            current_coupon_rate: float,
            settlement_price: float,
            minimum_lot: int,
            ncif: float, # net compounded interest factor = (1 + net_yield)**maturity_years
            taxation: float,
            volume_rating: int = 0,
            rating: str = ""
    ):
        self.isin: str = isin
        self.issuer: str = issuer
        self.maturity_years: float = maturity_years
        self.net_yield: float = net_yield
        self.gross_yield: float = gross_yield
        self.current_coupon_rate: float = current_coupon_rate
        self.settlement_price: float = settlement_price
        self.minimum_lot: int = minimum_lot
        self.ncif: float = ncif
        self.taxation: float = taxation
        self.volume_rating: int = volume_rating
        self.rating: str = rating
        self.capital_invested: float = 0.0
        self.num_lots: int = 0


class LadderStrategy(Enum):
    MAX_EARNINGS = "max_earnings"
    MAX_YTM = "max_ytm"
    MAX_YTM_CAPITAL = "max_ytm_capital"
    MAX_RETURN = "max_return"

class LadderConditions:
    def __init__(self,
                 ladder_size: int,
                 step_size: int,
                 date_tolerance_days_start: int,
                 date_tolerance_days_end: int,
                 years_offset: int,
                 capital_invested: float | list[float],
                 strategy: LadderStrategy,
                 step_width: int = 1,
                 months_offset: int = 0,
                 min_rating: str | None = None,
                 currencies: list[str] | None = None,
                 max_duplicated_issuers: int = 1,
                 include_issuer_codes: list[str] | None = None,
                 exclude_issuer_codes: list[str] | None = None,
                 include_isins: list[str] | None = None,
                 exclude_isins: list[str] | None = None,
                 max_last_price: float | None = None,
                 min_coupon_rate: float | None = None,
                 min_volume_rating: int | None = None):
        self.ladder_size: int = ladder_size
        self.step_size: int = step_size
        self.step_width: int = step_width
        self.date_tolerance_days_start: int = date_tolerance_days_start
        self.date_tolerance_days_end: int = date_tolerance_days_end
        self.years_offset: int = years_offset
        self.months_offset: int = months_offset
        if isinstance(capital_invested, (int, float)):
            self.capital_invested: list[float] = [float(capital_invested)] * ladder_size
        else:
            self.capital_invested: list[float] = [float(c) for c in capital_invested] if capital_invested else [1.0] * ladder_size
        self.strategy: LadderStrategy = strategy
        self.min_rating: str | None = min_rating
        self.currencies: list[str] | None = currencies
        self.max_duplicated_issuers: int = max_duplicated_issuers
        self.include_issuer_codes: list[str] | None = include_issuer_codes
        self.exclude_issuer_codes: list[str] | None = exclude_issuer_codes
        self.include_isins: list[str] | None = include_isins
        self.exclude_isins: list[str] | None = exclude_isins
        self.max_last_price: float | None = max_last_price
        self.min_coupon_rate: float | None = min_coupon_rate
        self.min_volume_rating: int | None = min_volume_rating

    @classmethod
    def from_yaml(cls, file_path: str) -> Self:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)

        # Convert strategy string to Enum
        if "strategy" in config:
            config["strategy"] = LadderStrategy(config["strategy"])

        return cls(**config)


class Investment:
    def __init__(self, isin: str, nominal_value: float):
        self.isin = isin
        self.nominal_value = nominal_value


class PortfolioConditions:
    def __init__(self, investments: list[dict], ladder_conditions: dict):
        self.investments: list[Investment] = [
            Investment(i["isin"], i.get("nominal_value", 0)) for i in investments
        ]
        self.ladder_conditions: dict = ladder_conditions


    @classmethod
    def from_yaml(cls, file_path: str) -> Self:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)

        return cls(**config)
