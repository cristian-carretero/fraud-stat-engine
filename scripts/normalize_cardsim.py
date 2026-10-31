"""Ejecuta el probe de CardSim y normaliza el esquema de salida."""

from cardsim import Cardsim

from fraud_stat_engine.schema import normalize_cardsim_df

# Ruta local a los CSV de calibración (los que vienen con CardSim)
RUTA_DCPC = r"C:/Users/Cristian/Documents/Proyectos/fraud-stat-engine/.venv/Lib/site-packages/cardsim/dcpc"

# Crear el simulador
sim = Cardsim(
    seed=42,
    fraud_rate=0.01,
    fraud_flag_threshold=0.01,
    dcpc_folder=RUTA_DCPC,
)

# Probe: 500 tarjetas, 30 días
raw = sim.simulate(n_payers=500, n_days=30, start_date="2024-01-01")

print("=" * 70)
print("SALIDA CRUDA (CardSim)")
print("=" * 70)
print(f"Dimensiones:  {raw.shape}")
print(f"Columnas:     {list(raw.columns)}")
print(raw.head(3))

# Normalizar
df = normalize_cardsim_df(raw)

print()
print("=" * 70)
print("SALIDA NORMALIZADA")
print("=" * 70)
print(f"Dimensiones:  {df.shape}")
print(f"Columnas:     {list(df.columns)}")
print()
print("Tipos de dato:")
print(df.dtypes)
print()
print("Muestra:")
print(df.head(5).to_string())
print()
print("Comprobaciones de integridad:")
print(f"  Tasa de fraude:          {df['is_fraud'].mean():.4%}")
print(f"  Valores de card_type:    {df['card_type'].unique()}")
print(f"  Valores de channel:      {df['channel'].unique()}")
print(f"  Valores de status:       {df['status'].unique()}")
print(f"  campaign_id todos nulos: {df['campaign_id'].isna().all()}")
print(f"  transaction_id únicos:   {df['transaction_id'].is_unique}")