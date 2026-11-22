"""CardSim calibration probe (500 cards x 30 days).

Verifies simulator installation and local DCPC calibration, measures empirical
transaction frequency per card-day, and inspects raw output columns prior to
running the full-scale simulation.
"""

from pathlib import Path

import cardsim
from cardsim import Cardsim

# Use bundled DCPC calibration CSVs; the Atlanta Fed remote endpoint changed format
# and breaks CardSim's default download behavior.
DCPC_DIR = str(Path(cardsim.__file__).resolve().parent / "dcpc")

SEED = 42
FRAUD_RATE = 0.01
FRAUD_FLAG_THRESHOLD = 0.01
N_PAYERS = 500
N_DAYS = 30
START_DATE = "2024-01-01"


def main() -> None:
    sim = Cardsim(
        seed=SEED,
        fraud_rate=FRAUD_RATE,
        fraud_flag_threshold=FRAUD_FLAG_THRESHOLD,
        dcpc_folder=DCPC_DIR,
    )

    df = sim.simulate(
        n_payers=N_PAYERS,
        n_days=N_DAYS,
        start_date=START_DATE,
    )

    # Expected baseline: ~14,583 tx, ~1.00% fraud, 500 payers, 50 payees (default 10:1 ratio).
    print(f"Generated transactions: {len(df):,}")
    print(f"Observed fraud rate:    {df['fraud'].mean():.4%}")
    print(f"Unique payers:          {df['payer_id'].nunique():,}")
    print(f"Unique payees:          {df['payee_id'].nunique():,}")
    print(f"\nRaw columns ({len(df.columns)}): {list(df.columns)}")
    print("\nSample rows:")
    print(df.head())


if __name__ == "__main__":
    main()
