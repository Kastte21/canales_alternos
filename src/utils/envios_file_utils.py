import os
import pandas as pd
from pathlib import Path
from datetime import datetime

def buscar_archivos_consolidado():
    posibles_rutas = [
        "data/input/CONSOLIDADO/",
        "../data/input/CONSOLIDADO/",
        "src/../data/input/CONSOLIDADO/"
    ]
    
    carpeta = next((ruta for ruta in posibles_rutas if os.path.exists(ruta)), None)
    if not carpeta:
        raise FileNotFoundError(f"Carpeta CONSOLIDADO no encontrada. Rutas probadas: {posibles_rutas}")
    
    archivos_excel = []
    for archivo in os.listdir(carpeta):
        if archivo.endswith(('.xlsx', '.xls')):
            archivos_excel.append(os.path.join(carpeta, archivo))
    
    return archivos_excel

def cargar_datos_envios(path, nombre_archivo):
    try:
        df = pd.read_excel(path)
        
        # DEBUG: Mostrar columnas originales
        print(f"🔍 Columnas originales en {nombre_archivo}:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1}. '{col}'")
        
        # Normalizar columnas a minúsculas
        df.columns = [col.lower().strip() for col in df.columns]
        
        # DEBUG: Mostrar columnas normalizadas
        print(f"🔍 Columnas normalizadas:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1}. '{col}'")
        
        # Mapeo de columnas según la estructura real del Excel
        mapeo_columnas = {
            'idc': 'dni',                    # IDC → DNI
            'correo': 'correo',              # CORREO → correo
            'telefono': 'telefono',          # TELEFONO → telefono
            'canal': 'canal',                # CANAL → canal
            'nombre de base': 'nombre_base', # NOMBRE DE BASE → nombre_base
            'fecha': 'fecha_envio',          # FECHA → fecha_envio
            'cartera': 'cartera'             # CARTERA → cartera
        }
        
        for col_original, col_nuevo in mapeo_columnas.items():
            if col_original in df.columns:
                df.rename(columns={col_original: col_nuevo}, inplace=True)
        
        if 'telefono' in df.columns:
            df['telefono'] = df['telefono'].astype(str).str.replace('.0', '')
        
        if 'dni' in df.columns:
            df['dni'] = df['dni'].astype(str)
        
        if 'fecha_envio' in df.columns:
            try:
                df['fecha_envio'] = pd.to_datetime(df['fecha_envio'], format='%d/%m/%Y').dt.date
            except:
                df['fecha_envio'] = datetime.now().date()
        else:
            df['fecha_envio'] = datetime.now().date()
        
        print(f"✅ Datos procesados: {len(df)} registros")
        print(f"   • DNI: {df['dni'].nunique()} únicos")
        print(f"   • Canal: {df['canal'].unique()}")
        print(f"   • Nombre base: {df['nombre_base'].unique()}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error cargando {nombre_archivo}: {e}")
        return None

def validar_datos_envios(df):
    if df is None or df.empty:
        return False
    
    if 'dni' not in df.columns:
        print("❌ Error: Columna 'dni' (IDC) no encontrada")
        return False
    
    if 'correo' not in df.columns and 'telefono' not in df.columns:
        print("❌ Error: Se requiere al menos 'correo' o 'telefono'")
        return False
    
    return True 