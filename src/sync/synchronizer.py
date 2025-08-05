# src/sync/synchronizer.py
import pandas as pd
from datetime import datetime
from decimal import Decimal

from src.config.database import get_db_connection
from src.utils import file_handler
from src.database import queries as db_queries
from src.reports.generator import generar_reporte_sincronizacion

class ClienteSynchronizer:
    def __init__(self, nombre_archivo="DATOS_ESTRATEGIA.xlsx"):
        self.nombre_archivo = nombre_archivo
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                print(f"❌ Ocurrió un error. Revirtiendo transacción: {exc_val}")
                self.conn.rollback()
            else:
                print("✅ Transacción completada con éxito.")
                self.conn.commit()
            self.conn.close()

    def _normalize_for_comparison(self, value):
        """
        Normaliza un valor para una comparación consistente.
        ¡ESTA ES LA VERSIÓN CORREGIDA Y FINAL!
        """
        # 1. Tratar NaN, None y cadenas vacías/espacios como un único concepto: "sin valor"
        if value is None or pd.isna(value) or (isinstance(value, str) and not value.strip()):
            return None
        
        # 2. Convertir números a un formato decimal estándar sin ceros finales
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value)).normalize()

        # 3. Quitar espacios de cualquier otra cadena de texto
        if isinstance(value, str):
            return value.strip()
        
        # 4. Para cualquier otro tipo (fechas, etc.), convertir a string como último recurso
        return str(value)

    def run_synchronization(self, generate_report=True, detailed_output=False):
        inicio = datetime.now()
        print("=" * 60)
        print("INICIANDO SINCRONIZACIÓN OPTIMIZADA DE CLIENTES")
        print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        try:
            path_excel = file_handler.find_excel_file(self.nombre_archivo)
            df_excel = file_handler.load_and_map_excel(path_excel, "clientes_map")
            df_db = db_queries.get_all_clientes_as_df(self.cursor)

            df_nuevos, df_actualizados, dnis_inactivos = self._compare_dataframes(df_excel, df_db)
            
            print("\n🔄 Aplicando cambios en la base de datos...")
            df_para_upsert = pd.concat([df_nuevos, df_actualizados])
            upserted = db_queries.bulk_upsert_clientes(self.cursor, df_para_upsert)
            deactivated = db_queries.bulk_deactivate_clientes(self.cursor, dnis_inactivos)
            print(f"  → {upserted} clientes insertados/actualizados.")
            print(f"  → {deactivated} clientes marcados como inactivos.")

            archivo_resumen = None
            if generate_report and (not df_nuevos.empty or not df_actualizados.empty or dnis_inactivos):
                df_inactivos_reporte = pd.DataFrame(list(dnis_inactivos), columns=['dni'])
                archivo_resumen = generar_reporte_sincronizacion(df_nuevos, df_actualizados, df_inactivos_reporte)

            sin_cambios = len(df_excel) - len(df_nuevos) - len(df_actualizados)
            self._mostrar_resumen(len(df_nuevos), len(df_actualizados), deactivated, sin_cambios, archivo_resumen, inicio)

            if detailed_output and not df_actualizados.empty:
                self._show_detailed_changes(df_actualizados, df_db)

        except Exception as e:
            print(f"\n❌ Error catastrófico durante la sincronización: {e}")
            raise

    def _compare_dataframes(self, df_excel: pd.DataFrame, df_db: pd.DataFrame):
        print("\n🔍 Comparando datos para detectar cambios...")
        if df_excel.empty:
            dnis_inactivos = set(df_db.index) if not df_db.empty else set()
            return pd.DataFrame(), pd.DataFrame(), dnis_inactivos

        df_excel_indexed = df_excel.set_index('dni')
        merged_df = df_excel_indexed.merge(df_db, on='dni', how='outer', suffixes=('_excel', '_db'), indicator=True)

        nuevos_dnis = merged_df[merged_df['_merge'] == 'left_only'].index
        dnis_inactivos = set(merged_df[merged_df['_merge'] == 'right_only'].index)
        
        df_comunes = merged_df[merged_df['_merge'] == 'both'].copy()
        common_cols = [c for c in df_excel_indexed.columns if c in df_db.columns]
        
        mask_cambios = pd.Series(False, index=df_comunes.index)
        for col in common_cols:
            series_excel_norm = df_comunes[f'{col}_excel'].apply(self._normalize_for_comparison)
            series_db_norm = df_comunes[f'{col}_db'].apply(self._normalize_for_comparison)
            mask_cambios |= (series_excel_norm != series_db_norm)
            
        actualizados_dnis = df_comunes[mask_cambios].index
        
        df_nuevos = df_excel_indexed.loc[nuevos_dnis].reset_index()
        df_actualizados = df_excel_indexed.loc[actualizados_dnis].reset_index()
        
        print(f"  → Detectados: {len(df_nuevos)} nuevos, {len(df_actualizados)} actualizados, {len(dnis_inactivos)} inactivos.")
        return df_nuevos, df_actualizados, dnis_inactivos

    def _show_detailed_changes(self, df_actualizados: pd.DataFrame, df_db: pd.DataFrame):
        print("\n" + "=" * 60)
        print("DETALLE DE CAMBIOS EN CLIENTES ACTUALIZADOS")
        print("=" * 60)
        df_actualizados_indexed = df_actualizados.set_index('dni')
        for dni, row in df_actualizados_indexed.iterrows():
            print(f"\n🔄 CLIENTE ACTUALIZADO - DNI: {dni}")
            db_row = df_db.loc[dni]
            for col, new_val in row.items():
                norm_new = self._normalize_for_comparison(new_val)
                norm_old = self._normalize_for_comparison(db_row.get(col))
                if norm_new != norm_old:
                    print(f"     • {col}: {db_row.get(col)} → {new_val}")
    
    def _mostrar_resumen(self, nuevos, actualizados, inactivos, sin_cambios, archivo_resumen, inicio):
        fin = datetime.now()
        duracion = fin - inicio
        
        print("\n" + "=" * 60)
        print("RESUMEN DE SINCRONIZACIÓN")
        print("=" * 60)
        print(f" → Nuevos clientes detectados:     {nuevos}")
        print(f" → Clientes actualizados:          {actualizados}")
        print(f" → Clientes sin cambios:           {sin_cambios}")
        print(f" → Clientes marcados como inactivos: {inactivos}")
        if archivo_resumen:
            print(f" → Resumen exportado en: {archivo_resumen}")
        print(f" → Duración: {str(duracion)}")
        print(f" → Finalización: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)