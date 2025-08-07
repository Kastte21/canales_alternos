# app/logic/client_synchronizer.py
import polars as pl
import logging
import pandas as pd
from datetime import datetime
from app import settings
from app import database as db
from app.utils import file_utils
from app.reports import generate_sync_report

logger = logging.getLogger(__name__)

def _show_detailed_changes(df_actualizados: pl.DataFrame, df_db: pl.DataFrame):
    logger.info("=" * 60)
    logger.info("DETALLE DE CAMBIOS EN CLIENTES ACTUALIZADOS")
    logger.info("=" * 60)

    df_db_subset = df_db.filter(pl.col("dni").is_in(df_actualizados.get_column("dni")))
    df_comparison = df_actualizados.join(df_db_subset, on="dni", how="inner", suffix="_db")

    for row in df_comparison.iter_rows(named=True):
        dni = row['dni']
        logger.info(f"🔄 CLIENTE ACTUALIZADO - DNI: {dni}")
        
        for col in df_actualizados.columns:
            if col == 'dni':
                continue
            
            new_val = row[col]
            old_val = row.get(f"{col}_db")

            # Normalizar
            norm_new = file_utils.normalize_column(pl.lit(new_val)).lit_value.lower()
            norm_old = file_utils.normalize_column(pl.lit(old_val)).lit_value.lower()

            if norm_new != norm_old:
                logger.info(f"     • {col}: '{old_val}' → '{new_val}'")

def run_client_synchronization(generate_report=True, detailed_output=False):
    inicio = datetime.now()
    logger.info("INICIANDO CARGA DE CLIENTES")
    
    try:
        # Cargar datos
        df_excel = file_utils.load_client_data(settings.CLIENT_SOURCE_FILE)
        excel_dnis = df_excel.get_column("dni").to_list()

        with db.get_db_connection() as cursor:
            # Obtener solo los datos relevantes de la BD
            logger.info(f"Obteniendo {len(excel_dnis)} clientes de la BD para comparación...")
            df_db = db.get_clients_by_dni(cursor, excel_dnis)
            
            # Comparar y encontrar cambios
            df_nuevos, df_actualizados = _compare_data(df_excel, df_db, detailed_output)
            
            # Encontrar clientes a desactivar
            logger.info("Obteniendo todos los DNIs activos para detectar inactivaciones...")
            db_active_dnis = db.get_all_active_dnis(cursor)
            dnis_inactivos = db_active_dnis - set(excel_dnis)
            logger.info(f"→ Detectados: {len(dnis_inactivos)} clientes para marcar como inactivos.")

        # Aplicar cambios en una nueva transacción si hay algo que cambiar
        if not df_nuevos.is_empty() or not df_actualizados.is_empty() or dnis_inactivos:
            logger.info("Aplicando cambios en la base de datos...")
            with db.get_db_connection(commit=True) as cursor:
                df_upsert = pl.concat([df_nuevos, df_actualizados])
                upserted = db.bulk_upsert_clients(cursor, df_upsert)
                deactivated = db.bulk_deactivate_clients(cursor, dnis_inactivos)
                logger.info(f"→ {upserted} clientes insertados/actualizados.")
                logger.info(f"→ {deactivated} clientes marcados como inactivos.")
        else:
            logger.info("✅ No se detectaron cambios. La base de datos ya está actualizada.")

        if generate_report:
            generate_sync_report(df_nuevos, df_actualizados, dnis_inactivos)
        
        _mostrar_resumen(
            nuevos=len(df_nuevos),
            actualizados=len(df_actualizados),
            inactivos=len(dnis_inactivos),
            sin_cambios=len(df_excel) - len(df_nuevos) - len(df_actualizados),
            inicio=inicio
        )

    except Exception as e:
        logger.critical(f"Falló la sincronización de clientes: {e}", exc_info=True)
        raise

def _compare_data(df_excel: pl.DataFrame, df_db: pl.DataFrame, detailed_output: bool):
    logger.info("Comparando datos para detectar cambios...")
    
    # Unir ambos dataframes
    df_merged = df_excel.join(df_db, on="dni", how="left", suffix="_db")

    # Identificar nuevos clientes (aquellos sin coincidencia en la BD)
    df_nuevos = df_merged.filter(pl.col("cliente_db").is_null()).select(df_excel.columns)
    
    # Identificar registros comunes para buscar actualizaciones
    df_comunes = df_merged.filter(pl.col("cliente_db").is_not_null())

    # Máscara para encontrar filas con al menos un cambio
    mask = pl.lit(False)
    compare_cols = [c for c in df_excel.columns if c in df_db.columns and c != 'dni']
    
    for col in compare_cols:
        # Normalizar ambas columnas para una comparación robusta
        excel_norm = file_utils.normalize_column(pl.col(col))
        db_norm = file_utils.normalize_column(pl.col(f"{col}_db"))
        mask = mask | (excel_norm != db_norm)

    df_actualizados = df_comunes.filter(mask).select(df_excel.columns)
    
    logger.info(f"→ Detectados: {len(df_nuevos)} nuevos, {len(df_actualizados)} actualizados.")
    
    if detailed_output and not df_actualizados.is_empty():
        _show_detailed_changes(df_actualizados, df_db)
        
    return df_nuevos, df_actualizados

def _mostrar_resumen(nuevos, actualizados, inactivos, sin_cambios, inicio):
    fin = datetime.now()
    duracion = fin - inicio
    
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN DE CARGA DE CLIENTES")
    logger.info("=" * 60)
    logger.info(f" → Nuevos clientes detectados:     {nuevos}")
    logger.info(f" → Clientes actualizados:          {actualizados}")
    logger.info(f" → Clientes sin cambios:           {sin_cambios}")
    logger.info(f" → Clientes marcados como inactivos: {inactivos}")
    logger.info(f" → Duración total:                 {str(duracion)}")
    logger.info(f" → Finalización:                   {fin.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)