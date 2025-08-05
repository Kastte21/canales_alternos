import pandas as pd

def comparar_cambios(row_nuevo, row_actual):
    def normalizar(val):
        if pd.isna(val): 
            return None
        if isinstance(val, str): 
            return val.strip()
        if isinstance(val, (int, float)): 
            return str(val)
        return str(val)
    
    return any(
        normalizar(row_nuevo.get(col)) != normalizar(row_actual.get(col))
        for col in row_nuevo.keys() if col != 'dni'
    )

def comparar_filas_detallado(row_nuevo, row_actual, columnas_comparacion):
    cambios = {}
    for columna in columnas_comparacion:
        nuevo = row_nuevo.get(columna)
        actual = row_actual.get(columna)
        
        if pd.isna(nuevo): 
            nuevo = None
        if pd.isna(actual): 
            actual = None
            
        if str(nuevo) != str(actual):
            cambios[columna] = {
                'antes': actual,
                'despues': nuevo
            }
    
    return cambios 