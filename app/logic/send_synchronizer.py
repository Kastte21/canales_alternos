# app/logic/send_synchronizer.py
import polars as pl
import hashlib
import logging

from app import database as db
from app.utils import file_utils
from app import settings

logger = logging.getLogger(__name__)

def _add_row_hash_to_df(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df

    hash_cols = ['dni', 'fecha_envio', 'canal', 'nombre_base', 'correo', 'telefono']
    hash_source = pl.concat_str(
        [pl.col(c).cast(pl.Utf8).fill_null("") for c in hash_cols],
        separator='|'
    )
    return df.with_columns(
        hash_source.map_elements(lambda x: hashlib.md5(x.encode()).hexdigest(), return_dtype=pl.Utf8)
        .alias("row_hash")
    )

def run_send_synchronization():
    logger.info("INICIANDO CARGA DE ENVÍOS")

    df_origen = file_utils.load_all_send_data(settings.SEND_SOURCE_DIR)
    if df_origen.is_empty():
        logger.warning("No se encontraron datos de envíos válidos para procesar.")
        return
        
    df_con_hash = _add_row_hash_to_df(df_origen)
    logger.info(f"Se han procesado {len(df_con_hash)} registros desde los archivos de origen.")

    with db.get_db_connection(commit=True) as cursor:
        logger.info("Consultando hashes existentes en la base de datos...")
        hashes_existentes = db.get_existing_send_hashes(cursor)
        logger.info(f"Se encontraron {len(hashes_existentes)} registros existentes en la tabla de envíos.")

        df_para_insertar = df_con_hash.filter(
            ~pl.col("row_hash").is_in(hashes_existentes)
        )
        
        if df_para_insertar.is_empty():
            logger.info("✅ No se encontraron nuevos envíos para insertar. La base de datos ya está actualizada.")
            return

        logger.info(f"Se han detectado {len(df_para_insertar)} nuevos registros para insertar.")
        
        inserted_count = db.copy_send_from_df(cursor, df_para_insertar)
        logger.info(f"✅ Se han insertado con éxito {inserted_count} nuevos registros en la base de datos.")