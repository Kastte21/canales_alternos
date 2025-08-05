import pandas as pd
import yaml
from pathlib import Path
from typing import List
import re
import math

# Cargar la configuración de mapeos una sola vez
CONFIG_PATH = Path(__file__).parent.parent.parent / "config/mappings.yml"
with open(CONFIG_PATH, 'r') as f:
    MAPPINGS = yaml.safe_load(f)

def calcular_deuda_campania(row):
    """
    Calcula la deuda de campaña basado en la deuda total y el porcentaje de campaña.
    Redondea el resultado hacia arriba al entero más cercano.
    """
    try:
        deuda_base = pd.to_numeric(row.get('deudatotal', row.get('deudatotalacumulado', 0)))
        campania_str = str(row.get('campania', '0%'))

        # Extraer el número del string de campaña (ej: "50%" -> 50)
        match = re.search(r'(\d+\.?\d*)', campania_str)
        if not match:
            return deuda_base

        porcentaje_descuento = float(match.group(1))
        
        valor_calculado = deuda_base * (1 - (porcentaje_descuento / 100.0))
        
        # Redondear hacia ARRIBA al entero más cercano (Ceiling)
        return math.ceil(valor_calculado)

    except (ValueError, TypeError):
        return None

def find_excel_file(pattern: str) -> Path:
    """Busca un archivo Excel en varias rutas comunes."""
    base_path = Path(__file__).parent.parent.parent
    possible_paths = [
        base_path / "data/input" / pattern,
        base_path / "src/data/input" / pattern
    ]
    for path in possible_paths:
        if path.exists():
            return path
    raise FileNotFoundError(f"No se encontró el archivo '{pattern}' en las rutas buscadas.")

def find_all_excel_in_dir(dir_name: str) -> List[Path]:
    """Encuentra todos los archivos Excel en un directorio."""
    base_path = Path(__file__).parent.parent.parent
    consolidado_dir = base_path / "data/input" / dir_name
    if not consolidado_dir.exists():
        raise FileNotFoundError(f"No se encontró el directorio '{consolidado_dir}'")
    return list(consolidado_dir.glob('*.xlsx')) + list(consolidado_dir.glob('*.xls'))

def load_and_map_excel(path: Path, mapping_key: str) -> pd.DataFrame:
    """Carga un archivo Excel, lo limpia, mapea sus columnas y realiza cálculos."""
    if not path.exists():
        raise FileNotFoundError(f"El archivo {path} no existe.")
        
    print(f"📄 Cargando y procesando archivo: {path.name}")
    df = pd.read_excel(path, dtype={'dni': str, 'IDC': str, 'TELEFONO': str})
    
    column_map = MAPPINGS.get(mapping_key)
    if not column_map:
        raise ValueError(f"No se encontró la clave de mapeo '{mapping_key}' en mappings.yml")
    
    df.rename(columns=lambda c: c.strip(), inplace=True)
    df.rename(columns=column_map, inplace=True)
    
    if mapping_key == 'clientes_map':
        print("    -> Calculando 'deudacampania' dinámicamente...")
        df['deudacampania'] = df.apply(calcular_deuda_campania, axis=1)

    if 'dni' in df.columns:
        df['dni'] = df['dni'].astype(str).str.strip()
    if 'telefono' in df.columns:
        df['telefono'] = df['telefono'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    if 'fecha_envio' in df.columns:
        df['fecha_envio'] = pd.to_datetime(df['fecha_envio'], errors='coerce').dt.date

    final_columns = [col for col in column_map.values() if col in df.columns]
    # Asegurarnos de que la columna calculada esté presente si no venía en el Excel
    if 'deudacampania' not in final_columns and 'deudacampania' in df.columns:
        final_columns.append('deudacampania')
        
    return df[final_columns]

def get_output_dir() -> Path:
    """Obtiene el directorio de salida, creándolo si no existe."""
    output_dir = Path(__file__).parent.parent.parent / "data/output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir