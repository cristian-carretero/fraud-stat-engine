"""Probe de CardSim: simulación de prueba con 500 tarjetas y 30 días.

Objetivo:
  1. Verificar que CardSim está bien instalado y calibrado.
  2. Medir la frecuencia real de transacciones por tarjeta y día.
  3. Ver qué columnas devuelve el simulador antes de normalizar.

Este script se ejecuta ANTES del módulo de normalización y sirve para
calibrar los parámetros de la simulación completa (17.500 tarjetas).
"""

# Importamos la clase del simulador de la Reserva Federal.
from cardsim import Cardsim


# Ruta local a los CSV de calibración (DCPC: Diary of Consumer Payment Choice).
# CardSim intenta descargarlos de internet por defecto, pero la web de la
# Reserva Federal de Atlanta ha cambiado el formato. Al pasar la ruta local
# evitamos el fallo y usamos los 6 CSV que vienen dentro del paquete.
DCPC_FOLDER = r"C:/Users/Cristian/Documents/Proyectos/fraud-stat-engine/.venv/Lib/site-packages/cardsim/dcpc"


# Creamos el simulador. Este paso es 'costoso': lee los CSV DCPC,
# construye las distribuciones de frecuencia e importe, y prepara el mundo.
sim = Cardsim(
    seed=42,                       # semilla fija → reproducibilidad total
    fraud_rate=0.01,               # prior de fraude: 1% (coherente con el proyecto)
    fraud_flag_threshold=0.01,     # etiqueta como fraude el top 1% por odds posteriores
    dcpc_folder=DCPC_FOLDER,       # le decimos dónde están los CSV de calibración
)


# Generamos las transacciones del probe. Este paso es 'rápido': usa las
# distribuciones ya calculadas en el paso anterior para producir filas.
# Los parámetros de volumen van AQUÍ, no en el constructor.
df = sim.simulate(
    n_payers=500,                  # número de tarjetas a simular (probe pequeño)
    n_days=30,                     # ventana temporal: 30 días
    start_date='2024-01-01',       # fecha ficticia de inicio
)


# -------------------------------------------------------------------
# 1. Volumen total de transacciones generadas
# -------------------------------------------------------------------
# len(df) cuenta las filas. Con :, se muestra con separador de miles.
print(f"Transacciones generadas: {len(df):,}")
# Esperado en el probe: ~14.583 transacciones


# -------------------------------------------------------------------
# 2. Tasa de fraude observada
# -------------------------------------------------------------------
# .mean() sobre una columna 0/1 calcula la proporción de 1s.
# Con :.4% se formatea como porcentaje con 4 decimales.
print(f"Tasa de fraude: {df['fraud'].mean():.4%}")
# Esperado en el probe: ~1.0012% (coincide con fraud_rate=0.01)


# -------------------------------------------------------------------
# 3. Número de tarjetas únicas en el dataset
# -------------------------------------------------------------------
# .nunique() cuenta los valores distintos de payer_id.
# Debe coincidir con n_payers=500.
print(f"Payers únicos: {df['payer_id'].nunique()}")
# Esperado en el probe: 500


# -------------------------------------------------------------------
# 4. Número de comercios únicos en el dataset
# -------------------------------------------------------------------
# .nunique() cuenta los valores distintos de payee_id.
# CardSim usa un ratio por defecto de 10:1 → 500 / 10 = 50 comercios.
print(f"Payees únicos: {df['payee_id'].nunique()}")
# Esperado en el probe: 50


# -------------------------------------------------------------------
# 5. Columnas que devuelve CardSim
# -------------------------------------------------------------------
# list(df.columns) convierte el índice de columnas en una lista normal
# para imprimirlo legiblemente. Esto nos dice qué información tenemos
# antes de normalizar el esquema.
print(f"\nColumnas: {list(df.columns)}")
# Esperado: ['run_id', 'day_index', 'date', 'time_seconds', 'hour',
#            'date_time', 'payer_id', 'payee_id', 'credit_card', 'remote',
#            'distance', 'amount', 'fraud']


# -------------------------------------------------------------------
# 6. Primeras 5 filas para inspección visual
# -------------------------------------------------------------------
# .head() muestra las primeras 5 filas del DataFrame. Sirve para
# comprobar de un vistazo que los valores son plausibles.
print(f"\nPrimeras 5 filas:")
print(df.head())
# Esperado: 5 filas con columnas como run_id='S42P500D30',
#           date='2024-01-01', credit_card=0/1, amount=float, fraud=0/1