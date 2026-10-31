"""Normalización del esquema de CardSim.

Este módulo transforma las columnas crudas que devuelve CardSim
(payer_id, payee_id, fraud, etc.) a un esquema canónico con nombres
del dominio de pagos y tipos correctos (enums, booleanos, timestamps).

El mismo módulo se reutiliza tanto en el probe (500 tarjetas) como
en la simulación completa (17.500 tarjetas).
"""

# Importamos pandas: es la librería que usamos para manipular el DataFrame
import pandas as pd


# Diccionario que traduce los valores 0/1 de CardSim a texto legible.
# 1 significa "crédito" y 0 significa "débito".
CARD_TYPE_MAP = {1: "credit", 0: "debit"}

# Diccionario que traduce los valores 0/1 de CardSim a texto legible.
# 1 significa "remoto" (compra online) y 0 significa "presencial" (POS físico).
CHANNEL_MAP = {1: "remote", 0: "in_person"}

# Lista de columnas de CardSim que NO vamos a conservar en el esquema final,
# porque son redundantes o internas del simulador.
COLUMNAS_A_ELIMINAR = ["run_id", "day_index", "date", "time_seconds", "hour"]


def normalize_cardsim_df(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra y transforma las columnas de CardSim al esquema canónico.

    Parámetros
    ----------
    df : pd.DataFrame
        Salida cruda de ``Cardsim.simulate()`` (13 columnas).

    Devuelve
    --------
    pd.DataFrame
        DataFrame con 11 columnas, en este orden:

        - **transaction_id** (str):
          Identificador único de la transacción con formato
          ``TX-YYYYMMDD-NNNNNNN``. Se genera ordenando cronológicamente
          y numerando dentro de cada día.

        - **card_id** (int):
          Identificador de la tarjeta que origina la transacción.
          Proviene de ``payer_id`` en CardSim.

        - **merchant_id** (int):
          Identificador del comercio receptor.
          Proviene de ``payee_id`` en CardSim.

        - **transaction_timestamp** (datetime64[ns]):
          Fecha y hora exacta del evento.
          Proviene de ``date_time`` en CardSim.

        - **amount** (float):
          Importe de la transacción generado por CardSim (lognormal
          calibrada con datos de pagos). Sin moneda asignada.
          Proviene de ``amount`` en CardSim.

        - **card_type** (str):
          Tipo de tarjeta: ``'credit'`` o ``'debit'``.
          Derivado del flag ``credit_card`` (1 → credit, 0 → debit).

        - **channel** (str):
          Canal de la transacción: ``'remote'`` (online) o
          ``'in_person'`` (POS físico).
          Derivado del flag ``remote`` (1 → remote, 0 → in_person).

        - **merchant_distance_km** (float):
          Distancia euclídea entre la ubicación de la tarjeta y la del
          comercio. CardSim trabaja en un grid abstracto; la escala se
          interpreta como kilómetros.
          Proviene de ``distance`` en CardSim.

        - **is_fraud** (bool):
          Etiqueta de fraude: ``True`` si la transacción es fraudulenta,
          ``False`` si es legítima.
          Proviene de ``fraud`` (0/1) en CardSim.

        - **campaign_id** (object, nulo):
          Identificador de la campaña de fraude (Card Testing o Bust-Out).
          Se deja en ``pd.NA`` y se poblará en la fase de inyección de
          campañas. Las transacciones legítimas permanecen nulas.

        - **status** (str):
          Estado de la transacción. Por ahora ``'approved'`` para todas;
          en fases posteriores podrá tomar ``'denied'`` o ``'reversed'``.
    """
    # Hacemos una copia para no modificar el DataFrame original 
    salida = df.copy()

    # -------------------------------------------------------------------
    # PASO 1: Renombrar las columnas de CardSim al vocabulario del dominio
    # -------------------------------------------------------------------
    salida = salida.rename(
        columns={
            "payer_id": "card_id",                    # identificador de tarjeta
            "payee_id": "merchant_id",                # identificador de comercio
            "date_time": "transaction_timestamp",     # fecha y hora del evento
            "distance": "merchant_distance_km",       # distancia tarjeta↔comercio
            "fraud": "is_fraud",                      # etiqueta de fraude (boolean)
            # 'amount' se queda igual: no se renombra
        }
    )

    # -------------------------------------------------------------------
    # PASO 2: Convertir los flags 0/1 en enums de texto legibles
    # -------------------------------------------------------------------
    # .map() recorre cada valor y lo sustituye según el diccionario.
    # 1 → 'credit', 0 → 'debit'
    salida["card_type"] = salida["credit_card"].map(CARD_TYPE_MAP)

    # 1 → 'remote', 0 → 'in_person'
    salida["channel"] = salida["remote"].map(CHANNEL_MAP)

    # -------------------------------------------------------------------
    # PASO 3: Convertir la etiqueta de fraude a booleano real
    # -------------------------------------------------------------------
    # .astype(bool) transforma 1 → True y 0 → False (más legible que int)
    salida["is_fraud"] = salida["is_fraud"].astype(bool)

    # -------------------------------------------------------------------
    # PASO 4: Ordenar cronológicamente para que transaction_id sea determinista
    # -------------------------------------------------------------------
    # Si no ordenamos, cada ejecución con la misma seed generaría IDs distintos
    salida = salida.sort_values("transaction_timestamp").reset_index(drop=True)

    # -------------------------------------------------------------------
    # PASO 5: Añadir un identificador de transacción único y legible
    # -------------------------------------------------------------------
    # Extraemos la parte de fecha en formato YYYYMMDD de cada timestamp
    fecha = salida["transaction_timestamp"].dt.strftime("%Y%m%d")

    # Numeramos las transacciones dentro de cada día (1, 2, 3, ...)
    # .cumcount() empieza en 0, por eso sumamos 1
    secuencia = salida.groupby(fecha).cumcount() + 1

    # Concatenamos: "TX-" + fecha + "-" + secuencia con 7 ceros a la izquierda
    # Resultado: 'TX-20240101-0000001'
    salida["transaction_id"] = (
        "TX-" + fecha + "-" + secuencia.astype(str).str.zfill(7)
    )

    # -------------------------------------------------------------------
    # PASO 6: Añadir columnas reservadas para la inyección de campañas
    # -------------------------------------------------------------------
    # campaign_id: se rellenará más adelante con el ID de la campaña
    # (Card Testing o Bust-Out). De momento, NA (nulo).
    salida["campaign_id"] = pd.NA

    # status: por ahora todas las transacciones son 'approved'.
    # En la fase de campañas se podrá poblar con 'denied'/'reversed'.
    salida["status"] = "approved"

    # -------------------------------------------------------------------
    # PASO 7: Eliminar columnas redundantes o ya transformadas
    # -------------------------------------------------------------------
    # Eliminamos las columnas de CardSim que no usamos + las originales
    # credit_card y remote, ya convertidas a card_type y channel.
    salida = salida.drop(columns=COLUMNAS_A_ELIMINAR + ["credit_card", "remote"])

    # -------------------------------------------------------------------
    # PASO 8: Reordenar las columnas en el orden canónico final
    # -------------------------------------------------------------------
    orden_final = [
        "transaction_id",           # identificador único
        "card_id",                  # tarjeta
        "merchant_id",              # comercio
        "transaction_timestamp",    # cuándo ocurrió
        "amount",                   # importe
        "card_type",                # crédito o débito
        "channel",                  # remoto o presencial
        "merchant_distance_km",     # distancia
        "is_fraud",                 # etiqueta
        "campaign_id",              # campaña (a poblar)
        "status",                   # estado
    ]

    # Devolvemos solo esas columnas, en ese orden
    return salida[orden_final]