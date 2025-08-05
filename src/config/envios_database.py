import psycopg2
import os
from dotenv import load_dotenv

def conectar_db_envios():
    load_dotenv()
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def obtener_envios_actuales(cursor):
    cursor.execute("SELECT * FROM envios_canales")
    resultados = cursor.fetchall()
    columnas = [desc[0] for desc in cursor.description]
    import pandas as pd
    df = pd.DataFrame(resultados, columns=columnas)
    return df

def limpiar_tabla_envios(cursor):
    cursor.execute("DELETE FROM envios_canales")
    print("Tabla de envíos limpiada") 