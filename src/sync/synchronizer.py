import pandas as pd
from datetime import datetime
from tqdm import tqdm

from src.config.database import conectar_db, obtener_clientes_actuales
from src.utils.file_utils import buscar_archivo_excel, cargar_datos_excel
from src.utils.comparison import comparar_cambios, comparar_filas_detallado
from src.database.queries import generar_upsert_query, upsert_cliente, marcar_clientes_inactivos
from src.reports.generator import generar_reportes_excel, crear_dataframes_resumen

class ClienteSynchronizer:    
    def __init__(self, nombre_archivo="DATOS_ESTRATEGIA.xlsx"):
        self.nombre_archivo = nombre_archivo
        self.conn = None
        self.cursor = None
        
    def __enter__(self):
        self.conn = conectar_db()
        self.cursor = self.conn.cursor()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()
    
    def cargar_datos(self):
        archivo = buscar_archivo_excel(self.nombre_archivo)
        print(f"Archivo encontrado: {archivo}")
        
        df_nuevo = cargar_datos_excel(archivo)
        print(f"Datos cargados: {len(df_nuevo)} registros")
        
        return df_nuevo
    
    def sincronizar_detallado(self):
        try:
            inicio = datetime.now()
            print("=" * 60)
            print("SINCRONIZACIÓN DETALLADA DE CLIENTES")
            print("=" * 60)
            print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            df_nuevo = self.cargar_datos()
            clientes_actuales = obtener_clientes_actuales(self.cursor)
            
            nuevos = actualizados = sin_cambios = 0
            columnas_comparacion = [col for col in df_nuevo.columns if col != 'dni']
            
            print("=" * 60)
            print("PROCESANDO CAMBIOS")
            print("=" * 60)
            
            for idx, row_nuevo in df_nuevo.iterrows():
                dni = str(row_nuevo['dni'])
                actual = clientes_actuales[clientes_actuales.index == dni]
                
                if actual.empty:
                    print(f"\n → CLIENTE NUEVO - DNI: {dni}")
                    print(f"   Nombre: {row_nuevo.get('cliente', 'N/A')}")
                    upsert_cliente(self.cursor, row_nuevo)
                    nuevos += 1
                else:
                    row_actual = actual.iloc[0].to_dict()
                    cambios = comparar_filas_detallado(row_nuevo, row_actual, columnas_comparacion)
                    
                    if cambios:
                        print(f"\n → CLIENTE ACTUALIZADO - DNI: {dni}")
                        print(f"   Nombre: {row_nuevo.get('cliente', 'N/A')}")
                        print("   Cambios detectados:")
                        for col, val in cambios.items():
                            print(f"     • {col}: {val['antes']} → {val['despues']}")
                        upsert_cliente(self.cursor, row_nuevo)
                        actualizados += 1
                    else:
                        sin_cambios += 1
                
                if (idx + 1) % 10000 == 0:
                    print(f"  → Procesados: {idx + 1}")
            
            self._mostrar_resumen_detallado(nuevos, actualizados, sin_cambios, inicio)
            
        except Exception as e:
            print(f"\nERROR: {e}")
            raise
    
    def sincronizar_simplificado(self):
        try:
            inicio = datetime.now()
            print("=" * 60)
            print("SINCRONIZACIÓN SIMPLIFICADA DE CLIENTES")
            print("=" * 60)
            print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            df_nuevo = self.cargar_datos()
            procesados = 0
            
            print("=" * 60)
            print("PROCESANDO CON UPSERT DIRECTO")
            print("=" * 60)
            
            for idx, row in df_nuevo.iterrows():
                upsert_cliente(self.cursor, row)
                procesados += 1
                
                if idx % 10000 == 0:
                    print(f"  → Procesados: {procesados}")
            
            self._mostrar_resumen_simplificado(procesados, inicio)
            
        except Exception as e:
            print(f"\nERROR: {e}")
            raise
    
    def sincronizar_optimizado(self):
        try:
            inicio = datetime.now()
            print("=" * 60)
            print("SINCRONIZACIÓN OPTIMIZADA DE CLIENTES")
            print("=" * 60)
            print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            df_nuevo = self.cargar_datos()
            clientes_actuales = obtener_clientes_actuales(self.cursor)
            
            columnas = df_nuevo.columns.tolist()
            query = generar_upsert_query(columnas)
            
            nuevos = actualizados = sin_cambios = 0
            batch = []
            
            dni_excel = set(df_nuevo['dni'])
            dni_bd = set(clientes_actuales.index)
            
            for _, row in tqdm(df_nuevo.iterrows(), total=len(df_nuevo), desc="Procesando"):
                dni = row['dni']
                row_dict = row.to_dict()
                
                if dni not in clientes_actuales.index:
                    nuevos += 1
                    batch.append([row_dict[col] for col in columnas])
                else:
                    actual_row = clientes_actuales.loc[dni].to_dict()
                    if comparar_cambios(row_dict, actual_row):
                        actualizados += 1
                        batch.append([row_dict[col] for col in columnas])
                    else:
                        sin_cambios += 1
                
                if len(batch) >= 500:
                    self.cursor.executemany(query, batch)
                    batch = []
            
            if batch:
                self.cursor.executemany(query, batch)
            
            # Marcar inactivos
            inactivos = marcar_clientes_inactivos(self.cursor, dni_bd, dni_excel)
            
            # Generar reportes
            df_actualizados, df_nuevos, df_inactivos = crear_dataframes_resumen(
                df_nuevo, clientes_actuales, comparar_cambios
            )
            
            archivo_resumen = generar_reportes_excel(
                df_nuevo, df_actualizados, df_nuevos, df_inactivos
            )
            
            self._mostrar_resumen_optimizado(nuevos, actualizados, sin_cambios, inactivos, archivo_resumen, inicio)
            
        except Exception as e:
            print(f"\nERROR: {e}")
            raise
    
    def _mostrar_resumen_detallado(self, nuevos, actualizados, sin_cambios, inicio):
        fin = datetime.now()
        duracion = fin - inicio
        
        print("\n" + "=" * 60)
        print("RESUMEN FINAL")
        print("=" * 60)
        print(f" → Nuevos insertados:     {nuevos}")
        print(f" → Clientes actualizados: {actualizados}")
        print(f" →  Sin cambios:           {sin_cambios}")
        print(f" → Duración: {str(duracion)}")
        print(f" → Finalización: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def _mostrar_resumen_simplificado(self, procesados, inicio):
        fin = datetime.now()
        duracion = fin - inicio
        
        print("\n" + "=" * 60)
        print("RESUMEN DE SINCRONIZACIÓN")
        print("=" * 60)
        print(f"Total de clientes procesados: {procesados}")
        print(f"Duración: {str(duracion)}")
        print(f"Finalización: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def _mostrar_resumen_optimizado(self, nuevos, actualizados, sin_cambios, inactivos, archivo_resumen, inicio):
        fin = datetime.now()
        duracion = fin - inicio
        
        print("\n" + "=" * 60)
        print("RESUMEN DE SINCRONIZACIÓN")
        print("=" * 60)
        print(f" → Nuevos clientes detectados:     {nuevos}")
        print(f" → Clientes actualizados:          {actualizados}")
        print(f" →  Clientes sin cambios:          {sin_cambios}")
        print(f" → Clientes marcados como inactivos: {inactivos}")
        print(f" → Resumen exportado en: {archivo_resumen}")
        print(f" → Duración: {str(duracion)}")
        print(f" → Finalización: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60) 