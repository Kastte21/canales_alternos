import psycopg2
import os
from dotenv import load_dotenv

def conectar_db():
    load_dotenv()
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def obtener_clientes_actuales(cursor):
    cursor.execute("SELECT * FROM clientes")
    resultados = cursor.fetchall()
    columnas = [desc[0] for desc in cursor.description]
    import pandas as pd
    df = pd.DataFrame(resultados, columns=columnas)
    df['dni'] = df['dni'].astype(str)
    return df.set_index('dni') 