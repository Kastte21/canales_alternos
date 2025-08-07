# app/reports.py
import pandas as pd
from typing import Set
from app import settings

def generate_sync_report(
    df_new, 
    df_updated, 
    dnis_inactive: Set[str], 
    file_name: str = "resumen_sincronizacion.xlsx"
):
    if df_new.is_empty() and df_updated.is_empty() and not dnis_inactive:
        return

    output_path = settings.OUTPUT_DIR / file_name
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Convertir los DataFrames de Polars a pandas
    df_new_pd = df_new.to_pandas()
    df_updated_pd = df_updated.to_pandas()
    df_inactive_pd = pd.DataFrame({"dni": list(dnis_inactive)})

    try:
        import xlsxwriter
        engine = "xlsxwriter"
    except ImportError:
        engine = "openpyxl"

    with pd.ExcelWriter(output_path, engine=engine) as writer:
        df_new_pd.to_excel(writer, sheet_name="Nuevos", index=False)
        df_updated_pd.to_excel(writer, sheet_name="Actualizados", index=False)
        df_inactive_pd.to_excel(writer, sheet_name="Inactivos", index=False)