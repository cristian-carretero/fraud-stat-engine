# fraud-stat-engine

Foundational synthetic data and statistical engine for transactional fraud
detection. Rebuilds the mathematical and computational foundations of a payment
fraud system from first principles.

## Current State

- Reproducible Python 3.12 environment managed with `uv` (deterministic lockfile).
- **CardSim** (Federal Reserve DCPC-calibrated simulator) configured with bundled
  local DCPC CSVs for reproducible offline traffic generation.
- **Calibration probe** (`notebooks/01_probe_cardsim.ipynb`): 500 cards x 30 days
  (14,583 transactions, 1.0012% fraud rate, 0.9722 tx/card/day) used to size the
  full-scale simulation and audit raw CardSim columns.
- **Canonical schema normalization** (`src/fraud_stat_engine/schema.py`): maps
  raw 13-column CardSim output to an 11-column payment-domain schema.
- **Baseline dataset builder** (`scripts/build_dataset.py`): generates 17,500
  cards x 12 days (4,000 merchants; 209,185 transactions, 1.0015% baseline fraud)
  and persists `data/raw/cardsim_base.parquet` with integrity assertions.
- **Baseline EDA** (`notebooks/02_eda_cardsim_base.ipynb`): schema and sentinel
  audit, lognormal amount geometry and robust estimators, entity overdispersion,
  temporal/channel patterns, and baseline fraud profile with calibration anchors
  for downstream Card Testing and Bust-Out injectors. Figures exported to
  `reports/figures/`.

## Project Structure

```text
fraud-stat-engine/
├── data/
│   └── raw/                             # Generated Parquet datasets (gitignored)
├── notebooks/
│   ├── 01_probe_cardsim.ipynb           # Calibration probe (500 cards x 30 days)
│   └── 02_eda_cardsim_base.ipynb        # Baseline dataset EDA
├── reports/
│   └── figures/
│       ├── 02_amount_distribution.png
│       ├── 02_entity_frequency.png
│       └── 02_temporal_patterns.png
├── scripts/
│   └── build_dataset.py                 # Full baseline generation -> Parquet
├── src/
│   └── fraud_stat_engine/
│       ├── __init__.py
│       ├── py.typed                     # PEP 561 typed package marker
│       └── schema.py                    # Canonical CardSim schema normalization
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

Build and persist the normalized baseline dataset (`data/raw/cardsim_base.parquet`):

```bash
uv run python scripts/build_dataset.py
```

Calibration and exploratory analysis live in `notebooks/` (`01_probe_cardsim.ipynb`
and `02_eda_cardsim_base.ipynb`), executed against the project's `uv` virtual
environment kernel.

## Stack

- Python 3.12
- `numpy`, `pandas`, `scipy`, `statsmodels`, `pyarrow`
- `cardsim` (git)
- `matplotlib`, `seaborn` (EDA)
- `pytest`, `pytest-cov`, `ruff`, `mypy`, `ipykernel`
