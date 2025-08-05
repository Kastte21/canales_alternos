# Sincronización de Clientes y Envíos - PostgreSQL (Versión Optimizada)

Este proyecto ofrece una solución robusta y de alto rendimiento para sincronizar datos desde archivos Excel hacia una base de datos PostgreSQL. Ha sido completamente refactorizado para procesar grandes volúmenes de datos de manera eficiente, precisa y segura, utilizando operaciones en lote y una arquitectura modular y escalable.

Incluye dos módulos principales:

1. **Sincronización de Clientes:** Compara un archivo maestro de clientes con la base de datos, identificando registros nuevos, actualizados e inactivos, y aplicando los cambios en lote.
2. **Carga de Envíos:** Carga archivos consolidados de canales de forma idempotente, verificando si los datos han cambiado antes de realizar cualquier operación en la base de datos.

---

## ✨ Características Principales

- **🚀 Rendimiento Extremo:** Utiliza operaciones `bulk` de PostgreSQL (`execute_values`) para inserciones y actualizaciones masivas, procesando cientos de miles de registros en segundos.
- **💡 Comparación Inteligente:** La lógica de comparación de clientes es inmune a diferencias de tipos de datos (ej. `float` vs `Decimal`) y maneja correctamente valores nulos y cadenas vacías para evitar falsos positivos.
- **🔄 Carga Idempotente:** El módulo de carga de envíos calcula una "huella digital" (hash) de los datos de origen. Si los datos no han cambiado desde la última carga, **no se realiza ninguna operación de escritura en la base de datos**.
- **🔧 Configuración Flexible:** El mapeo de columnas de Excel a la base de datos se gestiona a través de un archivo externo (`config/mappings.yml`), permitiendo adaptar el script a nuevos formatos sin modificar el código.
- **⚙️ Lógica de Negocio Integrada:** Capacidad para calcular campos dinámicamente durante la carga de datos, como el campo `deudacampania` basado en el porcentaje de la campaña.
- **📊 Reportes Automáticos:** Genera un resumen detallado en formato Excel (`.xlsx`) de los clientes nuevos, actualizados e inactivos después de cada sincronización.
- **🖥️ Interfaz de Usuario Sencilla:** Un menú interactivo en la consola guía al usuario para ejecutar las diferentes tareas.
- **🧱 Arquitectura Modular:** El código está organizado en módulos con responsabilidades claras (configuración, utilidades, base de datos, sincronización), facilitando su mantenimiento y extensión.

---

## 📂 Estructura del Proyecto (Refactorizada)

La estructura ha sido simplificada y optimizada para eliminar redundancia y mejorar la mantenibilidad.

## Estructura del Proyecto

```
Carga_CANALES_ALTERNOS/
├── config/
│ └── mappings.yml 		# Mapeo de columnas Excel -> BD
├── data/
│ ├── input/
│ │ ├── DATOS_ESTRATEGIA.xlsx
│ │ └── CONSOLIDADO/
│ │ └── CONSOLIDADO_CA_30_07_2025.xlsx
│ └── output/
│ └── resumen_sincronizacion.xlsx
├── src/
│ ├── config/
│ │ └── database.py 		# Lógica de conexión a BD centralizada
│ ├── database/
│ │ └── queries.py 		# TODAS las consultas a la BD
│ ├── reports/
│ │ └── generator.py 		# Generador de reportes Excel
│ ├── sync/
│ │ ├── envios_synchronizer.py 	# Lógica de sincronización de envíos (con hash)
│ │ └── synchronizer.py 	# Lógica de sincronización de clientes
│ └── utils/
│ └── file_handler.py 		# Manejador de archivos y lógica de cálculo
├── .env 			# Credenciales de la base de datos
├── main.py 			# Script principal con menú interactivo
├── requirements.txt 		# Dependencias del proyecto
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
- `CARTERA` (tipo de cartera)

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
    telefono TEXT
);
```

### Tabla `sync_metadata`

```sql
CREATE TABLE envios_canales (
    id_envio SERIAL PRIMARY KEY,
    dni VARCHAR(20) NOT NULL,
    fecha_envio DATE,
    canal TEXT,
    nombre_base TEXT,
    correo TEXT,
    telefono TEXT
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
MENÚ PRINCIPAL DE SINCRONIZACIÓN
============================================================
1. Sincronizar Clientes (Rápido, con reporte)
2. Sincronizar Clientes (Modo Auditoría Detallada)
3. Cargar Envíos desde CONSOLIDADO
4. Salir
============================================================
```

- **Opción 1:** La opción estándar para producción. Rápida, eficiente y genera el reporte en Excel.
- **Opción 2:** Ideal para depuración. Hace lo mismo que la opción 1, pero además imprime en consola los valores exactos que cambiaron para cada cliente actualizado.
- **Opción 3:** Carga los envíos.

## Reportes Generados

Genera un archivo Excel con tres hojas:

- **Actualizados:** Clientes que fueron modificados
- **Nuevos:** Clientes recién insertados
- **Inactivos:** Clientes que ya no están en el Excel

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

- **Idempotencia Real:** Ambos módulos están diseñados para ser idempotentes. Puedes ejecutar el script de sincronización de clientes o el de carga de envíos múltiples veces con los mismos datos de entrada y el estado final de la base de datos será el mismo, minimizando operaciones de escritura innecesarias.
- **Rendimiento de la Comparación:** La comparación de clientes se realiza en memoria utilizando las capacidades vectorizadas de Pandas después de una normalización de datos exhaustiva. Esto es órdenes de magnitud más rápido que iterar y comparar fila por fila.
- **Consistencia de Datos en `deudacampania`:** El script **ignora deliberadamente** los valores de la columna `deudacampania` del archivo Excel de clientes. En su lugar, la **recalcula** usando la lógica definida en `src/utils/file_handler.py`. Esto garantiza que los datos en la base de datos sean siempre consistentes y correctos, independientemente de la calidad de esa columna en el archivo de origen.
- **Manejo de "Soft Delete":** Los clientes que desaparecen del archivo Excel no se eliminan de la base de datos. En su lugar, se marcan como inactivos (`activo = false`). Esto preserva el historial y permite reactivarlos si vuelven a aparecer en futuras sincronizaciones.
- **Limpieza de Datos Automática:** El script realiza limpiezas de datos básicas de forma automática, como eliminar espacios en blanco (`strip()`) de los strings y limpiar el sufijo `.0` de los números de teléfono que a veces añade Excel.
- **Flexibilidad del Mapeo de Columnas:** Si un nuevo archivo Excel tiene columnas con nombres diferentes, no es necesario modificar el código Python. Simplemente ajusta el archivo `config/mappings.yml` para que coincida con la nueva estructura.

---