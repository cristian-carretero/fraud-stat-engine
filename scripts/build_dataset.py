"""Simulación completa de CardSim: genera el dataset base del proyecto.

Este script ejecuta la simulación definitiva con los parámetros calibrados
en el probe (500 tarjetas x 30 días -> 0,972 tx/tarjeta/día):

  - 17.500 tarjetas       (n_payers)
  - 12 días               (n_days)
  - factor 4,375          (payer_payee_factor -> 4.000 comercios)
  - semilla 42            (misma que el probe -> trazabilidad)
  - inicio 2024-01-01

Aplica la normalización del esquema y persiste el resultado en:
    data/raw/cardsim_base.parquet

Salida esperada: ~204.000 transacciones con 11 columnas canónicas y una
tasa de fraude del 1,00%.
"""

import time
from pathlib import Path

from cardsim import Cardsim

from fraud_stat_engine.schema import normalize_cardsim_df


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

# Ruta local a los CSV de calibración DCPC que vienen con CardSim.
# CardSim intenta descargarlos de internet por defecto, pero la web de la
# Reserva Federal de Atlanta ha cambiado el formato y falla. Al pasar la
# ruta local, usamos los 6 CSV incluidos en el propio paquete.
RUTA_DCPC = r"C:/Users/Cristian/Documents/Proyectos/fraud-stat-engine/.venv/Lib/site-packages/cardsim/dcpc"

# Ruta de salida del dataset base (relativa a la raíz del proyecto).
RUTA_SALIDA = Path("data/raw/cardsim_base.parquet")

# Parámetros calibrados en el probe.
SEMILLA = 42
FRAUD_RATE = 0.01                 # prevalencia objetivo: 1%
FRAUD_FLAG_THRESHOLD = 0.01       # etiqueta el top 1% por odds posteriores
N_PAYERS = 17_500                 # número de tarjetas
N_DAYS = 12                       # ventana temporal (12 días -> ~204.000 tx)
PAYER_PAYEE_FACTOR = 4.375        # 17.500 / 4.375 = 4.000 comercios
START_DATE = "2024-01-01"         # fecha ficticia de inicio


# ---------------------------------------------------------------------------
# 1. Configurar el simulador
# ---------------------------------------------------------------------------
print("=" * 70)
print("CONFIGURANDO SIMULADOR")
print("=" * 70)
print(f"  Tarjetas:       {N_PAYERS:,}")
print(f"  Días:           {N_DAYS}")
print(f"  Factor:         {PAYER_PAYEE_FACTOR} -> {int(N_PAYERS / PAYER_PAYEE_FACTOR):,} comercios")
print(f"  Tasa de fraude: {FRAUD_RATE:.2%}")
print(f"  Semilla:        {SEMILLA}")
print(f"  Inicio:         {START_DATE}")

sim = Cardsim(
    seed=SEMILLA,                          # reproducibilidad
    fraud_rate=FRAUD_RATE,                 # prior de fraude
    fraud_flag_threshold=FRAUD_FLAG_THRESHOLD,  # etiqueta el top 1%
    payer_payee_factor=PAYER_PAYEE_FACTOR, # ratio tarjetas/comercios
    dcpc_folder=RUTA_DCPC,                 # CSV de calibración locales
)


# ---------------------------------------------------------------------------
# 2. Generar la simulación completa
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("GENERANDO TRANSACCIONES")
print("=" * 70)

inicio = time.time()

raw = sim.simulate(
    n_payers=N_PAYERS,
    n_days=N_DAYS,
    start_date=START_DATE,
)

duracion = time.time() - inicio
print(f"  Simulación completada en {duracion:.1f} s")


# ---------------------------------------------------------------------------
# 3. Normalizar el esquema
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("NORMALIZANDO ESQUEMA")
print("=" * 70)

df = normalize_cardsim_df(raw)

print(f"  Columnas crudas:     {raw.shape[1]}")
print(f"  Columnas canónicas:  {df.shape[1]}")
print(f"  Filas:               {len(df):,}")


# ---------------------------------------------------------------------------
# 4. Resumen del resultado
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("RESULTADO")
print("=" * 70)
print(f"  Dimensiones:       {df.shape}")
print(f"  Transacciones:     {len(df):,}")
print(f"  Tasa de fraude:    {df['is_fraud'].mean():.4%}")
print(f"  Fraudes totales:   {df['is_fraud'].sum():,}")
print(f"  Tarjetas únicas:   {df['card_id'].nunique():,}")
print(f"  Comercios únicos:  {df['merchant_id'].nunique():,}")
print(f"  Rango temporal:    {df['transaction_timestamp'].min()} -> {df['transaction_timestamp'].max()}")
print()
print("  Distribución por tipo de tarjeta:")
for tipo, n in df["card_type"].value_counts().items():
    print(f"    {tipo:>8}: {n:,}")
print()
print("  Distribución por canal:")
for canal, n in df["channel"].value_counts().items():
    print(f"    {canal:>10}: {n:,}")


# ---------------------------------------------------------------------------
# 5. Comprobaciones de integridad
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("COMPROBACIONES DE INTEGRIDAD")
print("=" * 70)

assert df["transaction_id"].is_unique, "transaction_id debe ser único"
assert df["is_fraud"].dtype == bool, "is_fraud debe ser booleano"
assert df["campaign_id"].isna().all(), "campaign_id debe ser nulo en el dataset base"
assert set(df["card_type"].unique()) == {"credit", "debit"}, "card_type inválido"
assert set(df["channel"].unique()) == {"in_person", "remote"}, "channel inválido"
assert set(df["status"].unique()) == {"approved"}, "status inválido"

print("  transaction_id único:  OK")
print("  is_fraud booleano:     OK")
print("  campaign_id nulo:      OK")
print("  card_type válido:      OK")
print("  channel válido:        OK")
print("  status válido:         OK")


# ---------------------------------------------------------------------------
# 6. Persistir en Parquet
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("GUARDANDO DATASET")
print("=" * 70)

# Crea la carpeta de salida si no existe.
RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)

# Guarda el DataFrame en formato Parquet (columnar, comprimido, tipado).
df.to_parquet(RUTA_SALIDA, index=False)

# Muestra el tamaño del archivo resultante en MB.
tamano_mb = RUTA_SALIDA.stat().st_size / (1024 ** 2)
print(f"  Archivo:  {RUTA_SALIDA}")
print(f"  Tamaño:   {tamano_mb:.2f} MB")
print()
print("Dataset base listo.")