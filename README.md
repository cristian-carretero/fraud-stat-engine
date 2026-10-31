# fraud-stat-engine

Motor fundacional de datos y estadística para detección de fraude
transaccional. Reconstruye desde cero los fundamentos matemáticos y 
computacionales de un sistema de detección de fraude.

## Estado actual

- Entorno Python 3.12 reproducible con `uv` (lockfile determinista).
- **CardSim** (Reserva Federal) instalado como simulador base de tráfico.
- **Probe validado**: 500 tarjetas x 30 días -> 14.583 transacciones con
  tasa de fraude 1.0012%.
- **Módulo de normalización** (`src/fraud_stat_engine/schema.py`) que
  transforma el esquema crudo de CardSim al vocabulario del dominio de
  pagos (11 columnas canónicas).

## Estructura

```
fraud-stat-engine/
├── scripts/
│   ├── explore_cardsim.py      # Probe: 500 tarjetas x 30 días
│   └── normalize_cardsim.py    # Probe + normalización
├── src/
│   └── fraud_stat_engine/
│       ├── __init__.py
│       ├── py.typed            # Marca el paquete como tipado (PEP 561)
│       └── schema.py           # Normalización del esquema de CardSim
├── pyproject.toml
├── README.md
└── uv.lock
```

## Setup

```bash
uv sync
uv run python --version
```

## Uso

Ejecutar el probe de CardSim:

```bash
uv run python scripts/explore_cardsim.py
```

Ejecutar el probe con normalización de esquema:

```bash
uv run python scripts/normalize_cardsim.py
```

## Stack

- Python 3.12
- `numpy`, `pandas`, `scipy`, `statsmodels`
- `cardsim` (git)
- `pytest`, `pytest-cov`, `ruff`, `mypy`, `ipykernel`