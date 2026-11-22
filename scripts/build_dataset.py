"""Generate and persist the baseline CardSim dataset.

Runs the full-scale simulation using parameters calibrated from the probe
(500 cards x 30 days -> 0.972 tx/card/day):

- 17,500 cards (``n_payers``)
- 12 days (``n_days`` -> ~204k-209k transactions)
- 4.375 card-to-merchant ratio (``payer_payee_factor`` -> 4,000 merchants)
- Seed 42 (shared with probe for traceability)
- Start date: 2024-01-01

Applies canonical schema normalization and writes ``data/raw/cardsim_base.parquet``.
"""

import time
from pathlib import Path

import cardsim
from cardsim import Cardsim

from fraud_stat_engine.schema import normalize_cardsim_df

# Use bundled DCPC calibration CSVs; the Atlanta Fed remote endpoint changed format
# and breaks CardSim's default download behavior.
DCPC_DIR = str(Path(cardsim.__file__).resolve().parent / "dcpc")
OUTPUT_PATH = Path("data/raw/cardsim_base.parquet")

SEED = 42
FRAUD_RATE = 0.01            # 1% target prior
FRAUD_FLAG_THRESHOLD = 0.01  # Flag top 1% by posterior odds
N_PAYERS = 17_500
N_DAYS = 12
PAYER_PAYEE_FACTOR = 4.375   # 17,500 / 4.375 = 4,000 merchants
START_DATE = "2024-01-01"


def main() -> None:
    print("=" * 70)
    print("SIMULATOR CONFIGURATION")
    print("=" * 70)
    print(f"  Cards:       {N_PAYERS:,}")
    print(f"  Days:        {N_DAYS}")
    print(f"  Ratio:       {PAYER_PAYEE_FACTOR} -> {int(N_PAYERS / PAYER_PAYEE_FACTOR):,} merchants")
    print(f"  Fraud rate:  {FRAUD_RATE:.2%}")
    print(f"  Seed:        {SEED}")
    print(f"  Start date:  {START_DATE}")

    sim = Cardsim(
        seed=SEED,
        fraud_rate=FRAUD_RATE,
        fraud_flag_threshold=FRAUD_FLAG_THRESHOLD,
        payer_payee_factor=PAYER_PAYEE_FACTOR,
        dcpc_folder=DCPC_DIR,
    )

    print("\n" + "=" * 70)
    print("GENERATING TRANSACTIONS")
    print("=" * 70)
    t0 = time.perf_counter()
    raw = sim.simulate(
        n_payers=N_PAYERS,
        n_days=N_DAYS,
        start_date=START_DATE,
    )
    elapsed = time.perf_counter() - t0
    print(f"  Simulation completed in {elapsed:.1f} s")

    print("\n" + "=" * 70)
    print("NORMALIZING SCHEMA")
    print("=" * 70)
    df = normalize_cardsim_df(raw)
    print(f"  Raw columns:       {raw.shape[1]}")
    print(f"  Canonical columns: {df.shape[1]}")
    print(f"  Rows:              {len(df):,}")

    print("\n" + "=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)
    print(f"  Shape:            {df.shape}")
    print(f"  Transactions:     {len(df):,}")
    print(f"  Fraud rate:       {df['is_fraud'].mean():.4%}")
    print(f"  Fraud count:      {df['is_fraud'].sum():,}")
    print(f"  Unique cards:     {df['card_id'].nunique():,}")
    print(f"  Unique merchants: {df['merchant_id'].nunique():,}")
    print(f"  Time span:        {df['transaction_timestamp'].min()} -> {df['transaction_timestamp'].max()}")
    print("\n  Card type distribution:")
    for card_type, count in df["card_type"].value_counts().items():
        print(f"    {card_type:>8}: {count:,}")
    print("\n  Channel distribution:")
    for channel, count in df["channel"].value_counts().items():
        print(f"    {channel:>10}: {count:,}")

    print("\n" + "=" * 70)
    print("INTEGRITY CHECKS")
    print("=" * 70)
    assert df["transaction_id"].is_unique, "transaction_id must be unique"
    assert df["is_fraud"].dtype == bool, "is_fraud must be boolean"
    assert df["campaign_id"].isna().all(), "campaign_id must be null in baseline dataset"
    assert set(df["card_type"].unique()) == {"credit", "debit"}, "Invalid card_type values"
    assert set(df["channel"].unique()) == {"in_person", "remote"}, "Invalid channel values"
    assert set(df["status"].unique()) == {"approved"}, "Invalid status values"
    print("  All integrity assertions passed.")

    print("\n" + "=" * 70)
    print("PERSISTING PARQUET")
    print("=" * 70)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    size_mb = OUTPUT_PATH.stat().st_size / (1024**2)
    print(f"  Output: {OUTPUT_PATH}")
    print(f"  Size:   {size_mb:.2f} MB")
    print("\nBaseline dataset ready.")


if __name__ == "__main__":
    main()
