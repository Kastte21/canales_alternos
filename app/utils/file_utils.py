# app/utils/file_utils.py
import polars as pl
from pathlib import Path

from app import settings

def _calculate_debt_expression() -> pl.Expr:
    deuda_base = pl.col('deudatotalacumulado').fill_null(0).cast(pl.Float64)
    porcentaje_str = pl.col('campania').str.extract(r"(\d+\.?\d*)", 1).cast(pl.Float64, strict=False)
    factor_descuento = 1 - (porcentaje_str / 100.0)
    valor_calculado = (deuda_base * factor_descuento).ceil().cast(pl.Int64)
    return pl.when(porcentaje_str.is_not_null()).then(valor_calculado).otherwise(deuda_base.cast(pl.Int64))

def normalize_column(expr: pl.Expr) -> pl.Expr:
    numeric_expr = expr.cast(pl.Float64, strict=False)

    # Convertir todo lo que no sea numérico a string, limpiar y poner en minusculas.
    string_expr = (
        expr.cast(pl.Utf8)
        .str.strip_chars()
        .str.to_lowercase()
        .fill_null("") # Trata nulos y cadenas vacías como lo mismo
    )

    # Usar la versión numérica si la conversión fue exitosa, de lo contrario, usar la versión de texto.
    return (
        pl.when(expr.is_null())
        .then(pl.lit(None))
        .when(numeric_expr.is_not_null())
        .then(numeric_expr)
        .otherwise(string_expr)
    )

def normalize_value(val) -> str:
    if val is None:
        return ""
    return str(val).strip().lower()

def load_and_map_excel(path: Path, mapping_key: str) -> pl.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"El archivo {path} no existe.")
        
    df = pl.read_excel(path, engine='openpyxl')
    
    column_map = settings.MAPPINGS.get(mapping_key)
    if not column_map:
        raise ValueError(f"No se encontró la clave de mapeo '{mapping_key}' en mappings.yml")

    df = df.rename({col: col.strip() for col in df.columns})
    df = df.rename(column_map)
    
    final_columns = [col for col in column_map.values() if col in df.columns]
    df = df.select(final_columns)

    if 'dni' in df.columns:
        df = df.with_columns(pl.col('dni').cast(pl.Utf8).str.strip_chars())
        
    if 'telefono' in df.columns:
        df = df.with_columns(
            pl.col('telefono').cast(pl.Utf8).str.replace(r"\.0$", "").str.strip_chars()
        )
        
    if 'fecha_envio' in df.columns:
        if df.schema['fecha_envio'] == pl.String:
            df = df.with_columns(
                pl.col('fecha_envio').str.to_date(format="%Y-%m-%d", strict=False)
            )
            
    if mapping_key == 'clientes_map':
        df = df.with_columns(
            _calculate_debt_expression().alias("deudacampania")
        )

    return df

def load_client_data(file_name: str) -> pl.DataFrame:
    file_path = settings.INPUT_DIR / file_name
    return load_and_map_excel(file_path, "clientes_map")

def load_all_send_data(dir_name: str) -> pl.DataFrame:
    shipment_dir = settings.INPUT_DIR / dir_name
    if not shipment_dir.exists():
        raise FileNotFoundError(f"No se encontró el directorio de envíos: '{shipment_dir}'")
        
    all_files = list(shipment_dir.glob('*.xlsx')) + list(shipment_dir.glob('*.xls'))
    if not all_files:
        return pl.DataFrame()

    df_list = [load_and_map_excel(f, "envios_map") for f in all_files]
    
    return pl.concat(df_list, how="vertical")

def load_all_campaign_data(dir_name: str) -> pl.DataFrame:
    campaign_dir = settings.INPUT_DIR / dir_name
    if not campaign_dir.exists():
        raise FileNotFoundError(f"No se encontró el directorio de campañas: '{campaign_dir}'")
        
    all_files = list(campaign_dir.glob('*.xlsx')) + list(campaign_dir.glob('*.xls'))
    if not all_files:
        return pl.DataFrame()

    df_list = [load_and_map_excel(f, "campaign_map") for f in all_files]
    
    if not df_list:
        return pl.DataFrame()

    return pl.concat(df_list, how="vertical")