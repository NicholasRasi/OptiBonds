import pandas as pd


RATING_ORDER_SP = [
    "D", "C", "CC",
    "CCC-", "CCC", "CCC+",
    "B-", "B", "B+",
    "BB-", "BB", "BB+",
    "BBB-", "BBB", "BBB+",
    "A-", "A", "A+",
    "AA-", "AA", "AA+",
    "AAA"
]

RATING_DTYPE_SP = pd.CategoricalDtype(
    categories=RATING_ORDER_SP,
    ordered=True
)


def load_dataset(filepath: str) -> pd.DataFrame:
    # Open CSV using pandas
    df = pd.read_csv(filepath,
                     sep=';',
                     decimal=",",
                     parse_dates=["redemptiondate", "referencedate"],
                     dayfirst=True
                     )
    # Remove unnamed columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # Set ISIN code as index
    df = df.set_index("isincode", drop=False)
    df.index.name = "isincode"

    # Map SP ratings to numerical values
    df["ratingsp"] = df["ratingsp"].astype(RATING_DTYPE_SP)

    # Calculate maturity in years
    df["maturityyears"] = (
        (df["redemptiondate"] - df["referencedate"]).dt.days / 365.25
    )

    # Calculate compound interest factor
    df["ncif"] = (
        (1 + df["netyieldtomaturity"]/100) ** (df["maturityyears"])
    )
    return df