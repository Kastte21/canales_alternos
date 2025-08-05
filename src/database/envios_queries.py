def insertar_envio(cursor, row):
    # Inserta un registro de envío en la tabla
    query = """
        INSERT INTO envios_canales (dni, fecha_envio, canal, nombre_base, correo, telefono)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    values = (
        row.get('dni'),
        row.get('fecha_envio'),
        row.get('canal'),
        row.get('nombre_base'),
        row.get('correo'),
        row.get('telefono')
    )
    
    cursor.execute(query, values)

def insertar_envios_batch(cursor, df):
    # Inserta múltiples envíos en lote
    query = """
        INSERT INTO envios_canales (dni, fecha_envio, canal, nombre_base, correo, telefono)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    # Preparar datos para inserción
    datos = []
    for _, row in df.iterrows():
        datos.append((
            row.get('dni'),
            row.get('fecha_envio'),
            row.get('canal'),
            row.get('nombre_base'),
            row.get('correo'),
            row.get('telefono')
        ))
    
    # Insertar en lotes
    batch_size = 25000
    for i in range(0, len(datos), batch_size):
        batch = datos[i:i + batch_size]
        cursor.executemany(query, batch)
    
    return len(datos)

def obtener_estadisticas_envios(cursor):
    # Total de envíos
    cursor.execute("SELECT COUNT(*) FROM envios_canales")
    total_envios = cursor.fetchone()[0]
    
    # Envíos por canal
    cursor.execute("SELECT canal, COUNT(*) FROM envios_canales GROUP BY canal")
    envios_por_canal = cursor.fetchall()
    
    # Envíos por fecha
    cursor.execute("SELECT fecha_envio, COUNT(*) FROM envios_canales GROUP BY fecha_envio ORDER BY fecha_envio DESC LIMIT 10")
    envios_por_fecha = cursor.fetchall()
    
    # Envíos por nombre_base
    cursor.execute("SELECT nombre_base, COUNT(*) FROM envios_canales GROUP BY nombre_base")
    envios_por_base = cursor.fetchall()
    
    return {
        'total_envios': total_envios,
        'envios_por_canal': envios_por_canal,
        'envios_por_fecha': envios_por_fecha,
        'envios_por_base': envios_por_base
    } 