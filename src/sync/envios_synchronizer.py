import pandas as pd
from datetime import datetime
from tqdm import tqdm
import os

from src.config.envios_database import conectar_db_envios, limpiar_tabla_envios
from src.utils.envios_file_utils import buscar_archivos_consolidado, cargar_datos_envios, validar_datos_envios
from src.database.envios_queries import insertar_envios_batch, obtener_estadisticas_envios

class EnviosSynchronizer:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def __enter__(self):
        self.conn = conectar_db_envios()
        self.cursor = self.conn.cursor()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()
    
    def cargar_archivos_consolidado(self):
        try:
            archivos = buscar_archivos_consolidado()
            print(f"📁 Archivos encontrados en CONSOLIDADO: {len(archivos)}")
            
            if not archivos:
                print(" →  No se encontraron archivos Excel en la carpeta CONSOLIDADO")
                return []
            
            datos_consolidados = []
            
            for archivo in archivos:
                nombre_archivo = os.path.basename(archivo)
                print(f"\n📄 Procesando: {nombre_archivo}")
                
                df = cargar_datos_envios(archivo, nombre_archivo)
                
                if df is not None and validar_datos_envios(df):
                    print(f"✅ Datos válidos: {len(df)} registros")
                    datos_consolidados.append(df)
                else:
                    print(f"❌ Datos inválidos en: {nombre_archivo}")
            
            return datos_consolidados
            
        except Exception as e:
            print(f"❌ Error cargando archivos: {e}")
            return []
    
    def sincronizar_envios(self, limpiar_anterior=True):
        try:
            inicio = datetime.now()
            print("=" * 60)
            print("CARGA DE ENVÍOS DESDE CONSOLIDADO")
            print("=" * 60)
            print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            datos_archivos = self.cargar_archivos_consolidado()
            
            if not datos_archivos:
                print("❌ No hay datos válidos para procesar")
                return
            
            if limpiar_anterior:
                limpiar_tabla_envios(self.cursor)
            
            total_registros = 0
            archivos_procesados = 0
            
            for df in tqdm(datos_archivos, desc="Procesando archivos"):
                try:
                    registros_insertados = insertar_envios_batch(self.cursor, df)
                    total_registros += registros_insertados
                    archivos_procesados += 1
                    print(f"✅ Insertados {registros_insertados} registros")
                except Exception as e:
                    print(f"❌ Error procesando archivo: {e}")
            
            estadisticas = obtener_estadisticas_envios(self.cursor)
            
            self._mostrar_resumen_envios(
                archivos_procesados, 
                total_registros, 
                estadisticas, 
                inicio
            )
            
        except Exception as e:
            print(f"\n❌ Error en sincronización de envíos: {e}")
            raise
    
    def _mostrar_resumen_envios(self, archivos_procesados, total_registros, estadisticas, inicio):
        """Muestra resumen de la carga de envíos"""
        fin = datetime.now()
        duracion = fin - inicio
        
        print("\n" + "=" * 60)
        print("RESUMEN DE CARGA DE ENVÍOS")
        print("=" * 60)
        print(f"📁 Archivos procesados:     {archivos_procesados}")
        print(f"📊 Registros insertados:     {total_registros}")
        print(f"📈 Total envíos en BD:       {estadisticas['total_envios']}")
        print(f"⏱️  Duración:                {str(duracion)}")
        print(f"🕔 Finalización:             {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if estadisticas['envios_por_canal']:
            print(f"\n📊 Envíos por canal:")
            for canal, cantidad in estadisticas['envios_por_canal']:
                print(f"   • {canal}: {cantidad}")
        
        if estadisticas['envios_por_base']:
            print(f"\n📋 Envíos por nombre de base:")
            for nombre_base, cantidad in estadisticas['envios_por_base']:
                print(f"   • {nombre_base}: {cantidad}")
        
        if estadisticas['envios_por_fecha']:
            print(f"\n📅 Últimos envíos por fecha:")
            for fecha, cantidad in estadisticas['envios_por_fecha'][:5]:
                print(f"   • {fecha}: {cantidad}")
        
        print("=" * 60) 