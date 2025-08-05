import pandas as pd
from psycopg2.extras import execute_values
from typing import Set, Dict

def get_all_clientes_as_df(cursor) -> pd.DataFrame:
    """Obtiene TODOS los clientes activos de la BD en un DataFrame indexado por DNI."""
    cursor.execute("SELECT * FROM clientes WHERE activo = true")
    resultados = cursor.fetchall()
    if not resultados:
        return pd.DataFrame()
    
    columnas = [desc[0] for desc in cursor.description]
    return pd.DataFrame(resultados, columns=columnas).set_index('dni')

def bulk_upsert_clientes(cursor, df_to_upsert: pd.DataFrame):
    """Realiza un UPSERT masivo de clientes usando ON CONFLICT."""
    if df_to_upsert.empty:
        return 0

    df_copy = df_to_upsert.copy()
    df_copy['activo'] = True
    
    # Obtener columnas de la tabla para asegurar el orden y la existencia
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'clientes'")
    table_cols = [row[0] for row in cursor.fetchall()]
    
    # Filtrar el DataFrame para que solo contenga columnas que existen en la tabla
    df_filtered = df_copy[[col for col in df_copy.columns if col in table_cols]]
    
    cols = df_filtered.columns.tolist()
    update_cols_sql = ", ".join([f"{col} = EXCLUDED.{col}" for col in cols if col != 'dni'])
    
    query = f"""
        INSERT INTO clientes ({', '.join(cols)})
        VALUES %s
        ON CONFLICT (dni) DO UPDATE SET {update_cols_sql};
    """
    data_tuples = [tuple(x) for x in df_filtered.to_numpy()]
    execute_values(cursor, query, data_tuples, page_size=1000)
    return len(data_tuples)

def bulk_deactivate_clientes(cursor, dnis_to_deactivate: Set[str]):
    """Marca una lista de clientes como inactivos de forma masiva."""
    if not dnis_to_deactivate:
        return 0
    
    query = "UPDATE clientes SET activo = false WHERE dni IN %s"
    execute_values(cursor, query, [(list(dnis_to_deactivate),)], page_size=1000)
    return len(dnis_to_deactivate)

def bulk_insert_envios(cursor, df_envios: pd.DataFrame):
    """Inserta envíos de forma masiva."""
    if df_envios.empty:
        return 0
        
    cols = ['dni', 'fecha_envio', 'canal', 'nombre_base', 'correo', 'telefono']
    df_insert = df_envios[cols].copy()
    
    query = f"INSERT INTO envios_canales ({', '.join(cols)}) VALUES %s"
    data_tuples = [tuple(x) for x in df_insert.to_numpy()]
    execute_values(cursor, query, data_tuples, page_size=5000)
    return len(data_tuples)

def truncate_envios(cursor):
    """Limpia la tabla de envíos. TRUNCATE es más rápido que DELETE."""
    print("Limpiando tabla 'envios_canales' con TRUNCATE...")
    cursor.execute("TRUNCATE TABLE envios_canales RESTART IDENTITY;")

def get_envios_stats(cursor) -> Dict:
    """Obtiene todas las estadísticas de envíos en una sola consulta."""
    query = """
    SELECT 
        (SELECT COUNT(*) FROM envios_canales) as total,
        (SELECT json_object_agg(canal, count) FROM (SELECT canal, COUNT(*) as count FROM envios_canales GROUP BY canal) as q) as por_canal,
        (SELECT json_object_agg(nombre_base, count) FROM (SELECT nombre_base, COUNT(*) as count FROM envios_canales GROUP BY nombre_base) as q) as por_base,
        (SELECT json_agg(t) FROM (SELECT fecha_envio, COUNT(*) as count FROM envios_canales GROUP BY fecha_envio ORDER BY fecha_envio DESC LIMIT 10) as t) as por_fecha;
    """
    cursor.execute(query)
    stats = cursor.fetchone()
    return {
        'total_envios': stats[0] or 0,
        'envios_por_canal': stats[1] or {},
        'envios_por_base': stats[2] or {},
        'envios_por_fecha': stats[3] or []
    }

# --- Funciones para Metadatos y Hashes ---
def get_last_hash(cursor, source_id: str) -> str:
    """Obtiene el último hash de contenido para una fuente de datos específica."""
    cursor.execute("SELECT last_content_hash FROM sync_metadata WHERE source_id = %s", (source_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def update_sync_metadata(cursor, source_id: str, new_hash: str):
    """Inserta o actualiza el hash y la fecha de una fuente de datos."""
    query = """
        INSERT INTO sync_metadata (source_id, last_content_hash, last_sync_timestamp)
        VALUES (%s, %s, NOW())
        ON CONFLICT (source_id) DO UPDATE SET
            last_content_hash = EXCLUDED.last_content_hash,
            last_sync_timestamp = NOW();
    """
    cursor.execute(query, (source_id, new_hash))