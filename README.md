# fraud-stat-engine

Foundational synthetic data and statistical engine for transactional fraud
detection. Rebuilds the mathematical and computational foundations of a payment
fraud system from first principles.

## Current State

- Reproducible Python 3.12 environment managed with `uv` (deterministic lockfile).
- **CardSim** (Federal Reserve DCPC-calibrated simulator) configured with local
  calibration data for baseline payment traffic generation.
- **Validated calibration probe**: 500 cards x 30 days (~14,583 transactions,
  ~1.00% fraud rate, 0.972 tx/card/day).
- **Canonical schema normalization** (`src/fraud_stat_engine/schema.py`): maps
  raw CardSim output to an 11-column payment-domain schema.
- **Baseline dataset builder** (`scripts/build_dataset.py`): generates 17,500
  cards x 12 days (4,000 merchants) and persists `data/raw/cardsim_base.parquet`
  with integrity assertions.
- **Baseline EDA notebook** (`notebooks/01_eda_cardsim_base.ipynb`): initial
  schema audit and exploratory analysis setup.

## Project Structure

```text
fraud-stat-engine/
├── notebooks/
│   └── 01_eda_cardsim_base.ipynb   # Baseline dataset EDA
├── scripts/
│   ├── probe_cardsim.py            # Calibration probe (500 cards x 30 days)
│   └── build_dataset.py            # Full baseline generation -> Parquet
├── src/
│   └── fraud_stat_engine/
│       ├── __init__.py
│       ├── py.typed                # PEP 561 typed package marker
│       └── schema.py               # Canonical CardSim schema normalization
├── .gitignore
├── pyproject.toml
├── README.md
└── uv.lock
```

## Setup

```bash
uv sync
uv run python --version
```

## Usage

Run the CardSim calibration probe:

```bash
uv run python scripts/probe_cardsim.py
```

Build and persist the normalized baseline dataset (`data/raw/cardsim_base.parquet`):

```bash
uv run python scripts/build_dataset.py
```

## Stack

- Python 3.12
- `numpy`, `pandas`, `scipy`, `statsmodels`, `pyarrow`
- `cardsim` (git)
- `matplotlib`, `seaborn` (EDA)
- `pytest`, `pytest-cov`, `ruff`, `mypy`, `ipykernel`
