"""Schema normalization for raw CardSim simulation output.

Transforms raw CardSim columns (``payer_id``, ``payee_id``, ``fraud``, etc.)
into the canonical payment-domain schema with explicit string enums, booleans,
and deterministic transaction identifiers.
"""

import pandas as pd

CARD_TYPE_MAP: dict[int, str] = {1: "credit", 0: "debit"}
CHANNEL_MAP: dict[int, str] = {1: "remote", 0: "in_person"}

DROP_COLUMNS: list[str] = [
    "run_id",
    "day_index",
    "date",
    "time_seconds",
    "hour",
    "credit_card",
    "remote",
]

CANONICAL_COLUMNS: list[str] = [
    "transaction_id",
    "card_id",
    "merchant_id",
    "transaction_timestamp",
    "amount",
    "card_type",
    "channel",
    "merchant_distance_km",
    "is_fraud",
    "campaign_id",
    "status",
]


def normalize_cardsim_df(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw CardSim output to the canonical 11-column payment schema.

    Parameters
    ----------
    df : pd.DataFrame
        Raw output returned by ``Cardsim.simulate()`` (13 columns).

    Returns
    -------
    pd.DataFrame
        Normalized DataFrame with 11 canonical columns:

        - ``transaction_id`` (str): Deterministic ID (``TX-YYYYMMDD-NNNNNNN``)
          assigned by daily chronological sequence.
        - ``card_id`` (int): Originating card identifier (from ``payer_id``).
        - ``merchant_id`` (int): Receiving merchant identifier (from ``payee_id``).
        - ``transaction_timestamp`` (datetime64[us]): Event timestamp (from ``date_time``).
        - ``amount`` (float): Currency-agnostic transaction amount (lognormal DCPC fit).
        - ``card_type`` (str): ``"credit"`` or ``"debit"``.
        - ``channel`` (str): ``"remote"`` (online) or ``"in_person"`` (physical POS).
        - ``merchant_distance_km`` (float): Euclidean distance on CardSim's abstract grid,
          interpreted in kilometers.
        - ``is_fraud`` (bool): Fraud label (``True`` if fraudulent).
        - ``campaign_id`` (object): Reserved for synthetic fraud campaign injection
          (``pd.NA`` for baseline traffic).
        - ``status`` (str): Transaction authorization status (``"approved"`` in baseline;
          extended with ``"denied"`` / ``"reversed"`` in later stages).
    """
    out = df.copy()

    out = out.rename(
        columns={
            "payer_id": "card_id",
            "payee_id": "merchant_id",
            "date_time": "transaction_timestamp",
            "distance": "merchant_distance_km",
            "fraud": "is_fraud",
        }
    )

    out["card_type"] = out["credit_card"].map(CARD_TYPE_MAP)
    out["channel"] = out["remote"].map(CHANNEL_MAP)
    out["is_fraud"] = out["is_fraud"].astype(bool)

    # Sort chronologically before ID generation to guarantee deterministic IDs per seed.
    out = out.sort_values("transaction_timestamp").reset_index(drop=True)

    date_str = out["transaction_timestamp"].dt.strftime("%Y%m%d")
    daily_seq = out.groupby(date_str).cumcount() + 1
    out["transaction_id"] = (
        "TX-" + date_str + "-" + daily_seq.astype(str).str.zfill(7)
    )

    # Reserved fields populated during downstream fraud-campaign injection.
    out["campaign_id"] = pd.NA
    out["status"] = "approved"

    out = out.drop(columns=DROP_COLUMNS)
    return out[CANONICAL_COLUMNS]
