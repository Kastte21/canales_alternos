# Sincronización de Clientes y Envíos - PostgreSQL

Este proyecto permite sincronizar datos de clientes desde archivos Excel hacia una base de datos PostgreSQL, comparando cada fila usando el campo 'dni' como identificador único. También incluye funcionalidad para cargar envíos desde archivos consolidados. El proyecto está estructurado de manera modular para facilitar el mantenimiento y extensión.

## Características Generales

- Compara cada fila del Excel con los datos actuales en la BD
- Identifica exactamente qué columnas cambiaron
- Muestra los valores anteriores y nuevos
- Inserta clientes nuevos automáticamente
- Actualiza solo las columnas que cambiaron
- Reporte detallado en consola de todos los cambios
- Soporte para variables de entorno (.env)
- Estructura modular y reutilizable
- **NUEVO:** Carga de envíos desde archivos consolidados
- **NUEVO:** Procesamiento de múltiples canales (CORREO, SMS)

## Estructura del Proyecto

```
Carga_CANALES_ALTERNOS/
├── data/
│   ├── input/
│   │   ├── DATOS_ESTRATEGIA.xlsx
│   │   └── CONSOLIDADO/
│   │       └── CONSOLIDADO_CA_30_07_2025.xlsx
│   └── output/
│       └── resumen_sincronizacion.xlsx
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── database.py              # Configuración de BD clientes
│   │   └── envios_database.py       # Configuración de BD envíos
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py            # Manejo de archivos clientes
│   │   ├── envios_file_utils.py     # Manejo de archivos envíos
│   │   └── comparison.py            # Comparaciones y validaciones
│   ├── database/
│   │   ├── __init__.py
│   │   ├── queries.py               # Consultas SQL clientes
│   │   └── envios_queries.py        # Consultas SQL envíos
│   ├── reports/
│   │   ├── __init__.py
│   │   └── generator.py             # Generación de reportes
│   ├── sync/
│   │   ├── __init__.py
│   │   ├── synchronizer.py          # Lógica principal de sincronización
│   │   └── envios_synchronizer.py   # Lógica de sincronización envíos
│   ├── sync_detallado.py            # Script detallado
│   ├── sync_simplificado.py         # Script simplificado
│   ├── sync_optimizado.py           # Script optimizado
│   ├── sync_envios.py               # Script de envíos
│   └── __init__.py
├── notebooks/
│   ├── cargar.ipynb                 # Notebook de análisis
│   └── bases de datos.psql          # Scripts SQL
├── main.py                          # Script principal con menú
├── requirements.txt
└── README.md
```

## Tipos de Sincronización

### 1. Sincronización Detallada

**Script:** `src/sync_detallado.py`

**Características:**

- Comparación detallada fila por fila
- Muestra cambios específicos con valores antes/después
- Reporte en consola de cada cliente nuevo o actualizado
- Procesamiento individual de cada registro
- Ideal para análisis detallado de cambios

**Uso:**

```bash
python src/sync_detallado.py
```

### 2. Sincronización Simplificada

**Script:** `src/sync_simplificado.py`

**Características:**

- Upsert directo sin comparaciones previas
- Procesamiento más rápido
- Menos uso de memoria
- Reporte básico de progreso
- Ideal para sincronizaciones masivas

**Uso:**

```bash
python src/sync_simplificado.py
```

### 3. Sincronización Optimizada

**Script:** `src/sync_optimizado.py`

**Características:**

- Procesamiento en lotes (batch) para mejor rendimiento
- Detección de clientes inactivos
- Generación de reportes Excel automáticos
- Campo 'activo' para soft delete
- Comparación optimizada de cambios

**Uso:**

```bash
python src/sync_optimizado.py
```

### 4. Carga de Envíos desde CONSOLIDADO

**Script:** `src/sync_envios.py`

**Características:**

- Carga automática de todos los archivos Excel en `data/input/CONSOLIDADO/`
- Mapeo inteligente de columnas
- Estadísticas detalladas por canal y base
- Procesamiento en lotes optimizado

**Uso:**

```bash
python src/sync_envios.py
```

## Instalación

1. **Instalar las dependencias:**

```bash
pip install -r requirements.txt
```

2. **Configurar variables de entorno:**
   Crear archivo `.env` en la raíz del proyecto:

```env
DB_NAME=canalesalternos
DB_USER=user
DB_PASSWORD=pass
DB_HOST=localhost
DB_PORT=5432
```

## Uso

### Script Principal con Menú

```bash
python main.py
```

### Ejecución Directa de Scripts

```bash
# Versión detallada (recomendada para análisis)
python src/sync_detallado.py

# Versión simplificada (recomendada para carga masiva)
python src/sync_simplificado.py

# Versión optimizada (recomendada para producción y análisis})
python src/sync_optimizado.py

# Carga de envíos (nueva funcionalidad)
python src/sync_envios.py
```

### Uso como Módulo

```python
from src.sync.synchronizer import ClienteSynchronizer
from src.sync.envios_synchronizer import EnviosSynchronizer

with ClienteSynchronizer() as sync:
    sync.sincronizar_optimizado()

with EnviosSynchronizer() as sync:
    sync.sincronizar_envios()
```

## Formatos de Archivos Excel

### Archivo de Clientes (`DATOS_ESTRATEGIA.xlsx`)

Debe contener las siguientes columnas:

- `dni` (identificador único)
- `cliente`
- `deudatotalacumulado`
- `campaña` (se mapea a `campania`)
- `estado`
- `subcartera`
- `tipo_contacto`
- `contacto_dinamico`
- `rango_antiguedad`
- `SEGMENTACION` (se mapea a `segmentacion`)
- `deudacampania`
- `clientesnuevos`
- `COBERTURADOHUMANO` (se mapea a `coberturadohumano`)
- `CAJAS_MEDICION` (se mapea a `cajas_medicion`)
- `estado_cliente`
- `situacion_laboral`

### Archivos de Envíos (`data/input/CONSOLIDADO/*.xlsx`)

Debe contener las siguientes columnas:

- `NOMBRE DE BASE` (nombre de la campaña/base)
- `IDC` (DNI del cliente)
- `CORREO` (email del cliente)
- `TELEFONO` (teléfono, se limpia automáticamente el .0)
- `FECHA` (fecha del envío, formato dd/mm/yyyy)
- `CANAL` (tipo de canal: CORREO, SMS, etc.)
- `CARTERA` (tipo de cartera)

## Salida de los Scripts

### Sincronización Detallada

```
============================================================
SINCRONIZACIÓN DETALLADA DE CLIENTES
============================================================
Inicio: 2024-01-15 14:30:25

Archivo encontrado: data/input/DATOS_ESTRATEGIA.xlsx
Datos cargados: 7 registros

============================================================
PROCESANDO CAMBIOS
============================================================

🆕 CLIENTE NUEVO - DNI: 173257780
   Nombre: PEREDA MINANO ALBERTH GIUSEPPE

🔄 CLIENTE ACTUALIZADO - DNI: 173261033
   Nombre: CLAUDET CHUSHO JEAN PIERRE
   Cambios detectados:
     • deudatotalacumulado: 55000.00 → 59788.15
     • campania: 50% → 55%

============================================================
RESUMEN FINAL
============================================================
🆕 Nuevos insertados:     1
🔄 Clientes actualizados: 1
⏸️  Sin cambios:          5
🕔 Duración: 0:00:03.123456
🕔 Finalización: 2024-01-15 14:30:28
============================================================
```

### Carga de Envíos

```
============================================================
CARGA DE ENVÍOS DESDE CONSOLIDADO
============================================================
Inicio: 2025-08-04 17:54:54

📁 Archivos encontrados en CONSOLIDADO: 1

📄 Procesando: CONSOLIDADO_CA_30_07_2025.xlsx
✅ Datos procesados: 453,130 registros
   • DNI: 215,543 únicos
   • Canal: ['CORREO' 'SMS']

Procesando archivos: 100%|██████████| 1/1 [00:45<00:00, 45.23s/it]
✅ Insertados 453,130 registros

============================================================
RESUMEN DE CARGA DE ENVÍOS
============================================================
📁 Archivos procesados:     1
📊 Registros insertados:     453,130
📈 Total envíos en BD:       453,130
⏱️  Duración:                0:00:45.123456
🕔 Finalización:             2025-08-04 17:55:39

📊 Envíos por canal:
   • CORREO: 350,000
   • SMS: 103,130

📋 Envíos por nombre de base:
   • 30_SOFIA_CO: 453,130

📅 Últimos envíos por fecha:
   • 2025-07-30: 453,130
============================================================
```

## Tablas de Base de Datos

### Tabla `clientes`

```sql
CREATE TABLE clientes (
    dni VARCHAR(20) PRIMARY KEY,
    cliente TEXT,
    deudatotalacumulado DECIMAL,
    campania TEXT,
    estado TEXT,
    subcartera TEXT,
    tipo_contacto TEXT,
    contacto_dinamico TEXT,
    rango_antiguedad TEXT,
    segmentacion TEXT,
    deudacampania DECIMAL,
    clientesnuevos TEXT,
    coberturadohumano INTEGER,
    cajas_medicion TEXT,
    estado_cliente TEXT,
    situacion_laboral TEXT,
    activo BOOLEAN DEFAULT true
);
```

### Tabla `envios_canales`

```sql
CREATE TABLE envios_canales (
    id_envio SERIAL PRIMARY KEY,
    dni VARCHAR(20) NOT NULL,
    fecha_envio DATE NOT NULL,
    canal TEXT NOT NULL,
    nombre_base TEXT NOT NULL,
    correo TEXT,
    telefono TEXT
);
```

## Reportes Generados

La versión optimizada genera automáticamente un archivo Excel con tres hojas:

- **Actualizados:** Clientes que fueron modificados
- **Nuevos:** Clientes recién insertados
- **Inactivos:** Clientes que ya no están en el Excel

## Arquitectura Modular

### Módulos Principales

#### `src/config/`

- **`database.py`** - Configuración de conexión a BD para clientes
- **`envios_database.py`** - Configuración de conexión a BD para envíos

#### `src/utils/`

- **`file_utils.py`** - Búsqueda y carga de archivos Excel de clientes
- **`envios_file_utils.py`** - Búsqueda y carga de archivos Excel de envíos
- **`comparison.py`** - Comparaciones entre registros

#### `src/database/`

- **`queries.py`** - Generación de consultas SQL para clientes
- **`envios_queries.py`** - Generación de consultas SQL para envíos

#### `src/sync/`

- **`synchronizer.py`** - Clase principal de sincronización de clientes
- **`envios_synchronizer.py`** - Clase principal de sincronización de envíos

#### `src/reports/`

- **`generator.py`** - Generación de reportes Excel

## Dependencias

```
et_xmlfile==2.0.0
numpy==2.3.2
openpyxl==3.1.5
pandas==2.3.1
psycopg2==2.9.10
python-dateutil==2.9.0.post0
python-dotenv==1.1.1
pytz==2025.2
six==1.17.0
tzdata==2025.2
tqdm==4.66.1
```

## Notas Importantes

- **Transacciones:** Todos los scripts usan transacciones para garantizar consistencia
- **Rollback automático:** Si ocurre un error, se hace rollback automático
- **Manejo de NULL:** Los valores NULL se manejan correctamente en las comparaciones
- **Idempotencia:** Los scripts son idempotentes (se pueden ejecutar múltiples veces)
- **Variables de entorno:** Configuración segura de credenciales de BD
- **Múltiples rutas:** Búsqueda automática del archivo Excel en diferentes ubicaciones
- **Context Manager:** Uso de context managers para manejo seguro de conexiones
- **Limpieza de datos:** Teléfonos se limpian automáticamente (remueve .0)
- **Mapeo inteligente:** Columnas se mapean automáticamente según el formato del Excel

## Recomendaciones de Uso

- **Sincronización Detallada:** Para análisis detallado y auditoría de cambios
- **Sincronización Simplificada:** Para sincronizaciones rápidas y masivas
- **Sincronización Optimizada:** Para entornos de producción con reportes automáticos
- **Carga de Envíos:** Para procesar archivos consolidados de campañas de marketing

## Ventajas de la Nueva Estructura

1. **Modularidad:** Código organizado en módulos específicos
2. **Reutilización:** Funciones y clases reutilizables
3. **Mantenibilidad:** Fácil de mantener y extender
4. **Testabilidad:** Estructura que facilita las pruebas unitarias
5. **Escalabilidad:** Fácil agregar nuevas funcionalidades
6. **Separación de responsabilidades:** Cada módulo tiene una función específica
7. **Flexibilidad:** Soporte para múltiples tipos de archivos y formatos
8. **Robustez:** Manejo de errores y validaciones mejoradas
