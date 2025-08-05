import os
import pandas as pd
from pathlib import Path

def buscar_archivo_excel(nombre_archivo="DATOS_ESTRATEGIA.xlsx"):
    posibles_rutas = [
        f"data/input/{nombre_archivo}",
        f"../data/input/{nombre_archivo}",
        f"src/../data/input/{nombre_archivo}"
    ]
    
    archivo = next((ruta for ruta in posibles_rutas if os.path.exists(ruta)), None)
    if not archivo:
        raise FileNotFoundError(f"Archivo {nombre_archivo} no encontrado. Rutas probadas: {posibles_rutas}")
    
    return archivo

def cargar_datos_excel(path):
    df = pd.read_excel(path)
    
    # Mapeo de columnas
    mapeo_columnas = {
        'campaña': 'campania',
        'SEGMENTACION': 'segmentacion',
        'COBERTURADOHUMANO': 'coberturadohumano',
        'CAJAS_MEDICION': 'cajas_medicion'
    }
    
    df.rename(columns=mapeo_columnas, inplace=True)
    df.columns = [col.lower() for col in df.columns]
    df['dni'] = df['dni'].astype(str)
    df['activo'] = True
    
    return df

def obtener_directorio_output():
    posibles_output_dirs = [
        Path("data/output/"),
        Path("../data/output/"),
        Path("src/../data/output/")
    ]
    
    output_dir = next((ruta for ruta in posibles_output_dirs if ruta.exists()), posibles_output_dirs[0])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir 