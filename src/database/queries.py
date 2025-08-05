def generar_upsert_query(columnas):
    # Genera la consulta SQL para upsert
    if 'activo' not in columnas:
        columnas.append('activo')
    
    columnas_str = ", ".join(columnas)
    placeholders = ", ".join(["%s"] * len(columnas))
    update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in columnas if col != 'dni'])
    
    return f"""
        INSERT INTO clientes ({columnas_str})
        VALUES ({placeholders})
        ON CONFLICT (dni) DO UPDATE SET {update_clause}
    """

def upsert_cliente(cursor, row):
    # Realiza upsert de un cliente individual
    columnas = [col for col in row.index if col != 'dni']
    placeholders = ", ".join(["%s"] * len(columnas))
    columnas_str = ", ".join(columnas)
    update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in columnas])
    
    query = f"""
        INSERT INTO clientes (dni, {columnas_str})
        VALUES (%s, {placeholders})
        ON CONFLICT (dni) DO UPDATE SET {update_clause}
    """
    
    values = [row['dni']] + [row[col] for col in columnas]
    cursor.execute(query, values)

def marcar_clientes_inactivos(cursor, existentes, detectados):
    # Marca como inactivos los clientes que ya no están en el Excel
    no_detectados = existentes - detectados
    if no_detectados:
        cursor.executemany(
            "UPDATE clientes SET activo = false WHERE dni = %s",
            [(dni,) for dni in no_detectados]
        )
    return len(no_detectados) 