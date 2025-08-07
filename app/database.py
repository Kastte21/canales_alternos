# app/database.py
import psycopg2
import polars as pl
from contextlib import contextmanager
from psycopg2.extras import execute_values
from typing import Set, List
from io import StringIO

from . import settings

@contextmanager
def get_db_connection(commit=False):
    conn = None
    try:
        conn = psycopg2.connect(**settings.DB_CONFIG)
        yield conn.cursor()
        if commit:
            conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# --- Client Queries ---
def get_clients_by_dni(cursor, dnis: List[str]) -> pl.DataFrame:
    if not dnis:
        return pl.DataFrame()
    
    query = "SELECT * FROM clientes WHERE dni = ANY(%s) AND activo = true"
    cursor.execute(query, (dnis,))
    
    if cursor.rowcount == 0:
        return pl.DataFrame()
        
    column_names = [desc[0] for desc in cursor.description]
    return pl.DataFrame(cursor.fetchall(), schema=column_names)

def get_all_active_dnis(cursor) -> Set[str]:
    cursor.execute("SELECT dni FROM clientes WHERE activo = true")
    return {row[0] for row in cursor.fetchall()}

def bulk_upsert_clients(cursor, df_to_upsert: pl.DataFrame):
    if df_to_upsert.is_empty():
        return 0
    
    df_upsert = df_to_upsert.with_columns(pl.lit(True).alias("activo"))
    cols = df_upsert.columns
    update_cols_sql = ", ".join([f"{col} = EXCLUDED.{col}" for col in cols if col != 'dni'])
    
    query = f"""
        INSERT INTO clientes ({', '.join(cols)})
        VALUES %s
        ON CONFLICT (dni) DO UPDATE SET {update_cols_sql};
    """
    data_tuples = df_upsert.to_numpy().tolist()
    execute_values(cursor, query, data_tuples, page_size=2000)
    return len(data_tuples)

def bulk_deactivate_clients(cursor, dnis_to_deactivate: Set[str]):
    if not dnis_to_deactivate:
        return 0
    
    query = "UPDATE clientes SET activo = false WHERE dni IN %s"
    execute_values(cursor, query, [(list(dnis_to_deactivate),)], page_size=2000)
    return len(dnis_to_deactivate)

# --- Send Queries ---
def get_existing_send_hashes(cursor) -> Set[str]:
    cursor.execute("SELECT row_hash FROM envios_canales WHERE row_hash IS NOT NULL")
    return {row[0] for row in cursor.fetchall()}

def copy_send_from_df(cursor, df: pl.DataFrame):
    if df.is_empty():
        return 0
        
    s_buf = StringIO()
    cols = ['dni', 'fecha_envio', 'canal', 'nombre_base', 'correo', 'telefono', 'row_hash']
    
    existing_cols_in_df = [col for col in cols if col in df.columns]
    
    df.select(existing_cols_in_df).write_csv(s_buf, include_header=False)
    s_buf.seek(0)
    
    cursor.copy_expert(f"COPY envios_canales ({','.join(existing_cols_in_df)}) FROM STDIN WITH CSV", s_buf)
    return cursor.rowcount