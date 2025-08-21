# app/logic/campaign_synchronizer.py
import logging
from app import database as db
from app.utils import file_utils
from app import settings

logger = logging.getLogger(__name__)

def run_campaign_synchronization():
    logger.info("INICIANDO CARGA DE CAMPAÑA")
    
    try:
        df_campaigns = file_utils.load_all_campaign_data(settings.CAMPANIA_SOURCE_DIR)

        if df_campaigns.is_empty():
            logger.warning("No se encontraron archivos o datos válidos en la carpeta de campañas. No se realizarán cambios.")
            return

        logger.info(f"Se han procesado {len(df_campaigns)} registros desde la carpeta '{settings.CAMPANIA_SOURCE_DIR}'.")

        with db.get_db_connection(commit=True) as cursor:
            logger.info("Limpiando la tabla de campañas existentes...")
            db.truncate_campaigns(cursor)
            
            logger.info("Cargando registros de campañas...")
            inserted_count = db.copy_campaigns_from_df(cursor, df_campaigns)
            
            logger.info(f"✅ Se han insertado con éxito {inserted_count} registros de campaña.")

    except FileNotFoundError as e:
        logger.error(f"❌ Error de directorio: {e}")
    except Exception as e:
        logger.critical(f"Falló la carga de campañas: {e}", exc_info=True)
        raise