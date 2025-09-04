# app/logic/mail_synchronizer.py
import polars as pl
import logging

from app import database as db
from app.utils import file_utils
from app import settings

logger = logging.getLogger(__name__)

def _deduplicate_by_ranking(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty() or "ranking" not in df.columns or "email" not in df.columns:
        return df

    logger.info("Deduplicando registros de email por ranking...")
    initial_rows = len(df)

    #df_sorted = df.sort("idccliente", "ranking")
    df_sorted = df.sort("ranking")

    df_deduplicated = df_sorted.unique(subset=["email"], keep="first")

    removed_count = initial_rows - len(df_deduplicated)
    logger.info(f"Se eliminaron {removed_count} emails duplicados, priorizando el mejor ranking.")

    return df_deduplicated

def run_mail_synchronization(target: str = "mails"):
    logger.info(f"INICIANDO CARGA DE MAILS en la tabla '{target}'")

    try:
        df_mails = file_utils.load_all_mails_data(settings.MAILS_SOURCE_DIR)

        if df_mails.is_empty():
            logger.warning("No se encontraron archivos o datos válidos en la carpeta de Mails. No se realizarán cambios.")
            return

        logger.info(f"Se han procesado {len(df_mails)} registros desde la carpeta '{settings.MAILS_SOURCE_DIR}'.")

        df_cleaned = df_mails.drop_nulls(subset=["idccliente", "email", "ranking"])
        df_final = _deduplicate_by_ranking(df_cleaned)

        with db.get_db_connection(commit=True) as cursor:
            if target == "mails":
                logger.info("Limpiando la tabla mails...")
                db.truncate_mails(cursor)
                logger.info("Cargando registros en mails...")
                inserted_count = db.copy_mails_from_df(cursor, df_final)

            elif target == "mailssearch":
                logger.info("Limpiando la tabla mailssearch...")
                db.truncate_mailssearch(cursor)
                logger.info("Cargando registros en mailssearch...")
                inserted_count = db.copy_mailssearch_from_df(cursor, df_final)

            else:
                raise ValueError(f"Destino desconocido: {target}")

        logger.info(f"\u2705 Se han insertado con éxito {inserted_count} registros en la tabla '{target}'.")

    except FileNotFoundError as e:
        logger.error(f"\u274C Error de directorio: {e}")
    except Exception as e:
        logger.critical(f"Falló la carga de mails: {e}", exc_info=True)
        raise

    except FileNotFoundError as e:
        logger.error(f"\u274C Error de directorio: {e}")
    except Exception as e:
        logger.critical(f"Falló la carga de mails: {e}", exc_info=True)
        raise