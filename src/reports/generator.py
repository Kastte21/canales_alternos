import pandas as pd
from src.utils.file_utils import obtener_directorio_output

def generar_reportes_excel(df_nuevo, df_actualizados, df_nuevos, df_inactivos, nombre_archivo="resumen_sincronizacion.xlsx"):
    output_dir = obtener_directorio_output()
    archivo_resumen = output_dir / nombre_archivo
    
    with pd.ExcelWriter(archivo_resumen) as writer:
        df_actualizados.to_excel(writer, sheet_name="Actualizados", index=False)
        df_nuevos.to_excel(writer, sheet_name="Nuevos", index=False)
        df_inactivos.to_excel(writer, sheet_name="Inactivos", index=False)
    
    return archivo_resumen

def crear_dataframes_resumen(df_nuevo, clientes_actuales, comparar_cambios_func):
    dni_bd = set(clientes_actuales.index)
    
    # Clientes actualizados
    df_actualizados = df_nuevo[
        df_nuevo['dni'].isin(dni_bd) & 
        df_nuevo.apply(
            lambda row: comparar_cambios_func(
                row.to_dict(), 
                clientes_actuales.loc[row['dni']].to_dict()
            ) if row['dni'] in clientes_actuales.index else False, 
            axis=1
        )
    ]
    
    # Clientes nuevos
    df_nuevos = df_nuevo[~df_nuevo['dni'].isin(dni_bd)]
    
    # Clientes inactivos
    dni_excel = set(df_nuevo['dni'])
    df_inactivos = pd.DataFrame({'dni': list(dni_bd - dni_excel)})
    
    return df_actualizados, df_nuevos, df_inactivos 