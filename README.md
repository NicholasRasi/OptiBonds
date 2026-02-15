<div align="center">
    <img src="./media/logo.png" alt="logo" width="200" height="200"/>
    <h1>OptiBonds</h1>
    <h3><em>Build, optimize, and visualize bond ladders.</em></h3>
</div>

<p align="center">
    <strong>
    OptiBonds is a tool designed to build, optimize, and visualize bond ladders. It automates the complex process of selecting the best bonds to manage risk while maximizing your investment goals.
    </strong>
</p>

---

## Table of Contents
1. [What is a Bond Ladder?](#what-is-a-bond-ladder)
2. [Strategies: Growth vs. Income](#strategies-growth-vs-income)
3. [Diversification](#diversification)
4. [Ladder Shape](#ladder-shape)
5. [Advanced Filters](#advanced-filters)
6. [Setup Guide](#setup-guide)
7. [Run](#run)

---

## What is a Bond Ladder?

**Bond laddering is a fixed-income investing strategy where you spread your capital across bonds that mature at different times, much like rungs on a ladder.**

By staggering maturity dates, you ensure a regular stream of liquidity and reduce the impact of interest rate fluctuations.

### Single bond per step
```
Step 1   |==== Bond A ====|
Step 2   |====== Bond B ======|
Step 3   |======== Bond C =========|

---> time to maturity
```

**Example:**
- **Step 1:** Bond A matures in 1 year.
- **Step 2:** Bond B matures in 2 years.
- **Step 3:** Bond C matures in 3 years.

### Multiple bonds per step
You can also build a more diversified ladder with multiple bonds for each rung.

```
Step 1   |==== Bond A ====|==== Bond B ====|
Step 2   |====== Bond C ======|====== Bond D ======|
Step 3   |======== Bond E ========|======== Bond F ========|

---> time to maturity
```

**Example:**
- **Step 1:** Bonds A and B mature in 1 year.
- **Step 2:** Bonds C and D mature in 2 years.
- **Step 3:** Bonds E and F mature in 3 years.

### Why use a Bond Ladder?
1.  **Steady Cash Flow:** You receive a consistent return of principal as each "rung" matures.
2.  **Strategic Risk Management:**
    - **Rising Rates:** Short-term bonds mature quickly, allowing you to reinvest at current higher rates.
    - **Falling Rates:** Your longer-term bonds continue to pay out at their locked-in higher yields.
3.  **Adaptive Flexibility:** You avoid the trap of trying to time the market by diversifying across time.


## Strategies: Growth vs. Income

OptiBonds identifies the *mathematically optimal* bonds for your specific financial objectives. You can select your preferred strategy in the `conditions.yml` configuration file.

OptiBonds calculates the best capital allocation to match the values defined in your `capital_invested` list as closely as possible.

### Variables
- $C$: Capital invested
- $Y$: Net yield
- $M$: Maturity (years)

### 1. Max Earnings (Growth)
`LadderStrategy.MAX_EARNINGS`

This strategy focuses on the power of **Compound Interest**. It assumes that every coupon payment is immediately reinvested at the same rate.

> This strategy maximizes total compound earnings:
>
> $C \times (1 + Y)^M$


### 2. Max YTM (Income)
`LadderStrategy.MAX_YTM`

This strategy focuses on **Yield to Maturity (YTM)**. It identifies bonds offering the highest annualized percentage yield at their current market price.

> This strategy maximizes annualized earnings:
>
> $C \times Y$


### 3. Max Return (Balanced)
`LadderStrategy.MAX_RETURN`

This strategy focuses on **Total Return**. It calculates the sum of all coupon payments plus the capital gain (the difference between purchase price and face value).

> This strategy maximizes the total absolute return:
>
> $\text{Coupons} + \text{Capital Gain}$

## Diversification

Diversification is the cornerstone of a safe bond ladder. OptiBonds helps spread risk across different issuers, currencies, and maturity profiles.

### Strategic Diversification
- **No Diversification:** Set `max_duplicated_issuers` to `None` to simply pick the single best bond for each step.
- **Enabled Diversification:** Set `max_duplicated_issuers` to a value (e.g., `1`) to prevent over-exposure to a single entity across the ladder.

### Intrastep Diversification
When using multiple bonds per step, diversification is automatically applied to ensure you don't buy the same issuer multiple times for the same maturity date.


## Ladder Conditions
Customize the structure and safety parameters of your ladder in `conditions.yml`.

### Ladder Shape
- **`ladder_size`**: The total number of "rungs" or steps.
    - *Example: `15` creates a 15-step strategy.*
- **`step_size`**: The time gap between rungs.
    - *Example: `1` means bonds mature annually (1yr, 2yr, 3yr).*
    - *Example: `2` means bonds mature every two years (2yr, 4yr, 6yr).*
- **`capital_invested`**: The target investment for each rung. The capital allocated will be as close as possible to the values in the `capital_invested` list.
    - *Single value (e.g., `10000`) for equal investment across all rungs.*
    - *List (e.g., `[5000, 10000, 5000]`) for custom allocation.*
- **`years_offset` / `months_offset`**: Delays the start of the ladder.
    - *Useful if you want to start your ladder several months or years in the future.*
- **`step_width`**: The number of *different* bonds to buy per rung.
    - *Set to `1` for the single best bond per year.*
    - *Set to `2+` to split the investment across multiple bonds for better diversification.*

### Safety & Constraints
- **`max_duplicated_issuers`**: Limits exposure to any single issuer.
    - *Example: `1` ensures that if you buy an Italian Government bond for Year 1, the tool skips that issuer for all subsequent years.*
- **`min_rating`**: Minimum credit quality (e.g., `'BBB-'`).

### Advanced Filters
- **`date_tolerance_days_start` / `_end`**: Defines how much a bond's maturity can deviate from the target step date.
- **`exclude_isins` / `exclude_issuer_codes`**: Blacklist specific bonds or issuers.
- **`include_issuer_codes`**: Whitelist specific issuers.
- **`currencies`**: Limit searches to specific currencies (e.g., `['EUR', 'USD']`).
- **`max_last_price`**: Ignore bonds trading above a certain price (e.g., `100`).
- **`min_coupon_rate`**: Focus on bonds with a minimum interest payment.
- **`min_volume_rating`**: Ensures liquidity by filtering by average daily volume (0-4 scale). The value is calculated as follows: the average daily volume over the last 20 days is calculated, the value is converted to Euro using the last available exchange rate, and a value from 0 to 4 is then assigned considering the following ranges:
    - **0**: no trades in the considered period
    - **1**: average volume between 0 and 100,000
    - **2**: average volume between 100,000 and 1,000,000
    - **3**: average volume between 1,000,000 and 2,500,000
    - **4**: average volume greater than 2,500,000
---

## Setup Guide

Follow these steps to get OptiBonds running on your computer.

### 1. Prerequisites
You need **Python** installed.
You also need **Poetry**, a tool that manages the software libraries.
*   **Install Poetry:** Open your terminal and run: `pip install poetry`

### 2. Install Project Dependencies
Navigate to the project folder in your terminal and run:
```bash
poetry install
```

### 3. Download Market Data
You need fresh data to make decisions. We provide a script to fetch the latest bond prices.
```bash
poetry run python download_data.py
```
*This downloads a file to `data/data.csv`. You should run this whenever you want updated prices.*


## Run 

### Step 1: Configure Your Strategy
Open the file `conditions.yml` and modify the settings.

```yaml
ladder_size: 10
step_size: 1
capital_invested: 5000
min_rating: "A"
strategy: "max_earnings"
# ... other settings
```
Change these values to match your investment plan.

### Step 2: Calculate
Run the calculator command:
```bash
poetry run python calculator.py
```
By default, it uses `conditions.yml`. You can specify a custom configuration file using `--config` or `-c`:
```bash
poetry run python calculator.py --config my_conditions.yml
```

You can also save the generated portfolio to a YAML file using `--save` or `-s`. This file can then be used with `earnings.py`:
```bash
poetry run python calculator.py --save my_portfolio.yml
```

### Step 3: Calculate Earnings for an Existing Portfolio
If you already have a portfolio (or want to review one generated by `calculator.py`) and want to calculate its expected earnings, use `earnings.py`.

1. **Configure Your Portfolio**: Update `portfolio.yml` with your ISINs and invested amounts.
2. **Run the Earnings Calculator**:
```bash
poetry run python earnings.py
```
Similar to the calculator, you can specify a custom portfolio file:
```bash
poetry run python earnings.py --config portfolio_1.yml
```

### Step 4: Review Your Portfolio
It will print the generated **Portfolio**.

The portfolio is a list of recommended bonds to purchase, one for each step of your ladder.

For each step, it provides:
*   **ISIN**: The unique identifier for the bond.
*   **Name/Issuer**: The entity you are lending to.
*   **Lots**: The number of units to purchase.
*   **Capital**: The exact cost of the investment.

The results conclude with a **Summary** showing your Total Yield and Average Annual Return.


## Testing
See `tests/README.md` for test instructions.