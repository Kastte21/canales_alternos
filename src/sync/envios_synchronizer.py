from datetime import datetime
import pandas as pd
from tqdm import tqdm
import hashlib # Importamos la librería para hashing

from src.config.database import get_db_connection
from src.utils import file_handler
from src.database import queries as db_queries

class EnviosSynchronizer:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.source_id = 'CONSOLIDADO_ENVIOS'

    def __enter__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                # Evitamos el doble print si el error ya fue manejado
                if exc_val is not None:
                     print(f"❌ Ocurrió un error. Revirtiendo transacción: {exc_val}")
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()

    def _calculate_dataframe_hash(self, df: pd.DataFrame) -> str:
        """
        Calcula un hash SHA256 consistente para un DataFrame.
        """
        if df.empty:
            return hashlib.sha256(b'').hexdigest()
            
        # Convertir el DataFrame a un formato de string canónico (CSV en memoria)
        # Esto asegura que el hash sea reproducible.
        csv_string = df.to_csv(index=False, header=True, lineterminator='\n')
        
        # Calcular y devolver el hash
        return hashlib.sha256(csv_string.encode('utf-8')).hexdigest()

    def sincronizar_envios(self, limpiar_anterior=True):
        inicio = datetime.now()
        print("=" * 60)
        print("CARGA DE ENVÍOS DESDE CONSOLIDADO")
        print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            archivos = file_handler.find_all_excel_in_dir("CONSOLIDADO")
            if not archivos:
                print("No se encontraron archivos en 'data/input/CONSOLIDADO'.")
                return

            todos_los_datos = []
            for archivo_path in tqdm(archivos, desc="Cargando y validando archivos Excel", unit="archivo"):
                df = file_handler.load_and_map_excel(archivo_path, "envios_map")
                todos_los_datos.append(df)
            
            if not todos_los_datos:
                print("No se encontraron datos válidos para procesar.")
                return

            df_final = pd.concat(todos_los_datos, ignore_index=True).sort_values(by=['dni', 'nombre_base']).reset_index(drop=True)

            # --- VERIFICACIÓN POR HASH ---
            print("\n🔍 Verificando si los datos han cambiado...")
            current_hash = self._calculate_dataframe_hash(df_final)
            last_hash = db_queries.get_last_hash(self.cursor, self.source_id)

            if current_hash == last_hash:
                print("✅ Los datos de origen son idénticos a la última carga exitosa. No se requiere ninguna acción.")
                print("=" * 60)
                # No hacemos commit ni rollback, simplemente salimos sin cambiar nada.
                self.conn = None # Evita que __exit__ intente hacer commit
                return

            print("❗️ Los datos han cambiado. Procediendo con la actualización completa.")
            # ---------------------------

            if limpiar_anterior:
                db_queries.truncate_envios(self.cursor)

            print(f"\n✅ Total de registros a insertar: {len(df_final)}")
            registros_insertados = db_queries.bulk_insert_envios(self.cursor, df_final)
            print(f"  → {registros_insertados} registros insertados en la base de datos.")

            # Actualizar el hash en la tabla de metadatos
            db_queries.update_sync_metadata(self.cursor, self.source_id, current_hash)
            print("  → Huella digital (hash) de los datos actualizada.")

            estadisticas = db_queries.get_envios_stats(self.cursor)
            self._mostrar_resumen(len(archivos), registros_insertados, estadisticas, inicio)
            print("✅ Transacción completada con éxito.")

        except Exception as e:
            print(f"\n❌ Error en sincronización de envíos: {e}")
            raise

    def _mostrar_resumen(self, archivos_procesados, total_registros, estadisticas, inicio):
        # (Esta función no cambia)
        fin = datetime.now()
        duracion = fin - inicio
        
        print("\n" + "=" * 60)
        print("RESUMEN DE CARGA DE ENVÍOS")
        print("=" * 60)
        print(f"📁 Archivos procesados:     {archivos_procesados}")
        print(f"📊 Registros insertados:     {total_registros}")
        print(f"📈 Total envíos en BD:       {estadisticas['total_envios']}")
        print(f"⏱️  Duración:                {str(duracion)}")
        
        if estadisticas['envios_por_canal']:
            print(f"\n📊 Envíos por canal:")
            for canal, cantidad in estadisticas['envios_por_canal'].items():
                print(f"   • {canal}: {cantidad}")
        
        if estadisticas['envios_por_base']:
            print(f"\n📋 Envíos por nombre de base:")
            for base, cantidad in estadisticas['envios_por_base'].items():
                print(f"   • {base}: {cantidad}")
        
        print("=" * 60)