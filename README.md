# Sincronización de Clientes y Envíos - PostgreSQL (Versión Optimizada)

Este proyecto ofrece una solución robusta y de alto rendimiento para sincronizar datos desde archivos Excel hacia una base de datos PostgreSQL. Ha sido completamente refactorizado para procesar grandes volúmenes de datos de manera eficiente, precisa y segura, utilizando operaciones en lote y una arquitectura modular y escalable.

Incluye dos módulos principales:

1. **Sincronización de Clientes:** Compara un archivo excel de clientes con la base de datos, identificando registros nuevos, actualizados e inactivos, y aplicando los cambios en lote.
2. **Carga de Envíos:** Carga archivos consolidados de canales de forma idempotente, verificando si los datos han cambiado antes de realizar cualquier operación en la base de datos.

---

## Características Principales

- **Rendimiento Extremo:**
  - Utiliza Polars
  - Operaciones `bulk` de PostgreSQL (`execute_values` y `COPY`) para inserciones y actualizaciones masivas
  - Procesamiento vectorizado para comparaciones y transformaciones
- **Comparación Inteligente:**
  - Lógica de comparación robusta usando expresiones Polars
  - Manejo inteligente de tipos de datos y valores nulos
  - Normalización automática de datos para comparaciones consistentes
- **Carga Idempotente:**
  - Hash MD5 para detectar cambios en registros
  - Evita operaciones duplicadas en la base de datos
  - Verificación eficiente de datos existentes
- **Configuración Flexible:**
  - Mapeo de columnas via YAML (`config/mappings.yml`)
  - Fácil adaptación a nuevos formatos de datos
  - Configuración centralizada de parámetros
- **Lógica de Negocio Integrada:**
  - Cálculo vectorizado de campos derivados (ej: `deudacampania`)
  - Expresiones Polars optimizadas para transformaciones
  - Limpieza automática de datos de entrada
- **Reportes Automáticos:**
  - Generación de reportes Excel detallados
  - Seguimiento de cambios en los datos
  - Resúmenes de operaciones realizadas
- **Interfaz de Usuario Sencilla:**
  - Menú interactivo en consola
  - Feedback detallado de operaciones
  - Modo de auditoría para debugging
- **Arquitectura Modular:**
  - Código organizado en módulos funcionales
  - Separación clara de responsabilidades
  - Fácil mantenimiento y extensión

---

## Estructura del Proyecto

La estructura ha sido simplificada y optimizada para eliminar redundancia y mejorar la mantenibilidad.

## Estructura del Proyecto

```
Carga_CANALES_ALTERNOS/
├── app/                      		# Módulo principal de la aplicación
│   ├── logic/                		# Lógica de negocio
│   │   ├── __init__.py
│   │   ├── client_synchronizer.py  	# Sincronización de clientes
│   │   └── send_synchronizer.py    	# Sincronización de envíos
│   ├── utils/
│   │   ├── __init__.py
│   │   └── file_utils.py    		# Procesamiento de archivos con Polars
│   ├── __init__.py
│   ├── database.py          		# Operaciones de base de datos
│   ├── reports.py           		# Generación de reportes Excel
│   └── settings.py          		# Configuración de la aplicación
├── config/
│   └── mappings.yml         		# Mapeo de columnas Excel -> BD
├── data/
│   ├── input/              		# Archivos de entrada
│   │   ├── DATOS_ESTRATEGIA.xlsx
│   │   └── CONSOLIDADO/
│   │       └── CONSOLIDADO_CA_*.xlsx
│   └── output/             		# Archivos de salida
│       └── resumen_sincronizacion.xlsx
├── .env                   		# Variables de entorno
├── main.py               		# Script principal
├── requirements.txt
└── README.md
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

## Formatos de Archivos Excel

### Archivo de Clientes (`DATOS_ESTRATEGIA.xlsx`)

Debe contener las siguientes columnas:

- `dni` (identificador único)
- `cliente`
- `moneda`
- `deudatotal`
- `deudatotalsoles`
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
- `CARTERA`

## Tablas de Base de Datos

### Tabla `clientes`

```sql
CREATE TABLE clientes (
    dni VARCHAR(20) PRIMARY KEY,
    cliente TEXT,
    deudatotalacumulado NUMERIC,
    campania TEXT,
    estado TEXT,
    subcartera TEXT,
    tipo_contacto TEXT,
    contacto_dinamico TEXT,
    rango_antiguedad TEXT,
    segmentacion TEXT,
    deudacampania NUMERIC,
    clientesnuevos TEXT,
    coberturadohumano INTEGER,
    cajas_medicion TEXT,
    estado_cliente TEXT,
    situacion_laboral TEXT,
    moneda VARCHAR(5),
    deudatotal NUMERIC,
    deudatotalsoles NUMERIC,
    activo BOOLEAN DEFAULT true
);
```

### Tabla `envios_canales`

```sql
CREATE TABLE envios_canales (
    id_envio SERIAL PRIMARY KEY,
    dni VARCHAR(20) NOT NULL,
    fecha_envio DATE,
    canal TEXT,
    nombre_base TEXT,
    correo TEXT,
    telefono TEXT,
    row_hash VARCHAR(64)
);
```

## Uso

### Script Principal con Menú

```bash
python main.py
```

Aparecerá el menú principal con las opciones optimizadas:

```bash
============================================================
                       MENÚ PRINCIPAL
============================================================
 1. Cargar Clientes (Rápido, con reporte)
 2. Cargar Clientes (Modo Auditoría Detallada)
 3. Cargar Envíos desde CONSOLIDADO
 4. Salir
============================================================
Seleccione una opción (1-4):
```

- **Opción 1:** La opción estándar para producción. Rápida, eficiente y genera el reporte en Excel.
- **Opción 2:** Ideal para depuración. Hace lo mismo que la opción 1, pero además imprime en consola los valores exactos que cambiaron para cada cliente actualizado.
- **Opción 3:** Carga los envíos.

## Reportes Generados

Genera un archivo Excel con tres hojas:

- **Actualizados:** Clientes que fueron modificados
- **Nuevos:** Clientes recién insertados
- **Inactivos:** Clientes que ya no están en el Excel

## Notas Importantes

- **Idempotencia Real:** Ambos módulos están diseñados para ser idempotentes. Puedes ejecutar el script de sincronización de clientes o el de carga de envíos múltiples veces con los mismos datos de entrada y el estado final de la base de datos será el mismo, minimizando operaciones de escritura innecesarias.
- **Rendimiento de la Comparación:** La comparación de clientes se realiza utilizando Polars, un motor de procesamiento de datos ultrarrápido escrito en Rust. Las operaciones vectorizadas y la gestión eficiente de memoria hacen que las comparaciones sean órdenes de magnitud más rápidas que las implementaciones tradicionales.
- **Consistencia de Datos en `deudacampania`:** El script ignora los valores de la columna `deudacampania` del archivo Excel de clientes. En su lugar, la recalcula usando la lógica definida en `src/utils/file_handler.py`. Esto garantiza que los datos en la base de datos sean siempre consistentes y correctos, independientemente de la calidad de esa columna en el archivo de origen.
- **Manejo de "Soft Delete":** Los clientes que desaparecen del archivo Excel no se eliminan de la base de datos. En su lugar, se marcan como inactivos (`activo = false`). Esto preserva el historial y permite reactivarlos si vuelven a aparecer en futuras sincronizaciones.
- **Limpieza de Datos Automática:** El script realiza limpiezas de datos básicas de forma automática, como eliminar espacios en blanco (`strip()`) de los strings y limpiar el sufijo `.0` de los números de teléfono que a veces añade Excel.
- **Flexibilidad del Mapeo de Columnas:** Si un nuevo archivo Excel tiene columnas con nombres diferentes, no es necesario modificar el código Python. Simplemente ajusta el archivo `config/mappings.yml` para que coincida con la nueva estructura.

---
