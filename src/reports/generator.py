import pandas as pd
from src.utils.file_handler import get_output_dir

def generar_reporte_sincronizacion(df_nuevos, df_actualizados, df_inactivos, nombre_archivo="resumen_sincronizacion.xlsx"):
    """
    Genera un archivo Excel con el resumen de la sincronización.
    """
    output_path = get_output_dir() / nombre_archivo
    print(f"📊 Generando reporte en: {output_path}")
    
    with pd.ExcelWriter(output_path) as writer:
        df_nuevos.to_excel(writer, sheet_name="Nuevos", index=False)
        df_actualizados.to_excel(writer, sheet_name="Actualizados", index=False)
        df_inactivos.to_excel(writer, sheet_name="Inactivos", index=False)
    
    return output_path