# ResiControl - Gestion de Seguridad Residencial

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Version](https://img.shields.io/badge/Version-2.1.0-orange)

**ResiControl** es una aplicacion de escritorio para la gestion integral de seguridad en conjuntos residenciales pequenos. Permite registrar visitantes y residentes, controlar accesos y salidas, gestionar parqueaderos, llevar un historial completo de movimientos, registrar incidentes, generar reportes en PDF y CSV, y escanear codigos QR de placas de vehiculos.

---

## Tabla de Contenidos

- [Caracteristicas](#caracteristicas)
- [Arquitectura](#arquitectura)
- [Instalacion](#instalacion)
- [Uso](#uso)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Type Checking](#type-checking)
- [Base de Datos](#base-de-datos)
- [Dependencias](#dependencias)
- [Empaquetado](#empaquetado)
- [Tests](#tests)
- [Contribucion](#contribucion)
- [Licencia](#licencia)

---

## Caracteristicas

| Modulo | Descripcion |
|--------|-------------|
| **Login seguro** | Autenticacion con contrasenas hasheadas en bcrypt, bloqueo tras 5 intentos fallidos (5 min) |
| **Dashboard** | Metricas en tiempo real: entradas del dia, residentes activos, parqueaderos ocupados, personas dentro |
| **Visitantes** | Registro de entrada/salida con consentimiento de datos (Ley 1581), tabla con visitantes activos y edicion |
| **Residentes** | Alta, baja (soft-delete), edicion, busqueda, generacion de QR y visualizacion por tablas |
| **Parqueaderos** | Vista visual de 20 parqueaderos (10 residentes + 10 visitantes), asignacion manual a visitantes |
| **Historial** | Historial completo de accesos con filtros por fecha, tipo y busqueda; exportacion a CSV |
| **Incidentes** | Registro de incidentes con niveles de alerta (bajo, medio, alto) |
| **Escaneo QR** | Camara en tiempo real con decodificacion de QR para identificar residentes |
| **Reportes PDF** | Generacion de reportes con tablas formateadas por rango de fechas y tipo |
| **Backups** | Backups automaticos diarios a las 00:00, retencion de 30 dias, restauracion desde UI |
| **Gestion de Usuarios** | Solo admin: crear/eliminar usuarios con roles (admin, operador, residente) |

---

## Arquitectura

El proyecto sigue una **arquitectura modular** con separation de responsabilidades y tipo hints para mejor mantenimiento:

```
ResiControl/
|
├── main.py                       # Punto de entrada
├── resicontrol.py                # Aplicacion principal (CustomTkinter)
├── config.py                     # Constantes, rutas y colores
├── logger.py                    # Logging con rotacion de archivos
├── auth.py                      # Autenticacion: bcrypt, bloqueo, validacion de contrasenas
├── validators.py                # Validacion de campos de formulario
├── database.py                  # Inicializacion de BD, tablas, indices, seed
├── models.py                    # Capa de datos: todas las operaciones CRUD
├── backup.py                    # Backup automatico diario y manual
├── qr_manager.py               # Generacion y escaneo de codigos QR
├── report_generator.py          # Generacion de reportes PDF y CSV
│
├── views/                       # Modulos de interfaz grafica (refactorizado)
│   ├── __init__.py
│   ├── base.py                 # Componentes compartidos de CTk
│   ├── navigation.py          # Menu lateral y navegacion
│   ├── dashboard.py           # Vista de metricas
│   ├── residents.py           # Gestion de residentes
│   ├── visitors.py            # Registro de visitantes
│   ├── parking.py             # Gestion de parqueaderos
│   ├── history.py             # Historial de accesos
│   ├── incidents.py           # Registro de incidentes
│   ├── reports.py             # Generacion de reportes PDF
│   ├── backup.py              # Gestion de respaldos
│   ├── users.py               # Gestion de usuarios (admin)
│   └── qr_scanner.py          # Escaneo de codigos QR
│
├── tests/
│   └── test_resicontrol.py   # Tests unitarios (pytest)
│
├── backups/                    # Carpeta de backups generados (gitignored)
├── qrs/                       # Carpeta de QR generados (gitignored)
├── logs/                      # Carpeta de logs (gitignored)
│
├── resicontrol.db             # Base de datos SQLite
├── requirements.txt           # Dependencias
├── mypy.ini                   # Configuracion de type checking
├── ResiControl.spec           # Configuracion de PyInstaller
└── README.md                  # Este archivo
```

### Flujo de Datos

```
Usuario → [views/* - Vista] → [models.py - Datos] → [resicontrol.db - SQLite]
                                    ↑
[config.py - Rutas] ← [backup.py - Respaldos automaticos]
[auth.py - Seguridad] ← [validators.py - Validaciones]
[qr_manager.py - QR] ← [report_generator.py - Reportes]
```

---

## Instalacion

### Requisitos Previos

- **Python 3.10 o superior**
- **pip** (gestor de paquetes de Python)

### Pasos

**1. Clonar o descargar el repositorio:**
```bash
git clone <url-del-repositorio>
cd ResiControl
```

**2. Crear entorno virtual (recomendado):**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

**3. Instalar dependencias:**
```bash
pip install -r requirements.txt
```

**4. Ejecutar la aplicacion:**
```bash
python main.py
```

### Credenciales por defecto

| Usuario  | Contrasena | Rol       |
|----------|------------|-----------|
| `admin`  | `admin123` | Admin     |
| `portero`| `1234`     | Operador  |

> **Importante:** Cambia las contrasenas por defecto antes de poner en produccion.

---

## Uso

### Interfaz de Usuario

La aplicacion utiliza **CustomTkinter** para una interfaz moderna con tema oscuro.

- **Sidebar izquierdo:** Navegacion entre modulos
- **Area central:** Contenido del modulo seleccionado
- **Dashboard:** Metricas actualizadas automaticamente cada 10 segundos

### Flujo Tipico de Operacion

1. **Login** -> Iniciar sesion con usuario y contrasena
2. **Dashboard** -> Revisar metricas del dia
3. **Visitantes** -> Registrar entrada (nombre, cedula, placa, unidad) -> Marcar salida al irse
4. **Residentes** -> Agregar/editar residentes, generar QR de placas
5. **Parqueaderos** -> Visualizar estado, asignar a visitantes
6. **Historial** -> Consultar registros, filtrar, exportar CSV
7. **Incidentes** -> Registrar eventos de seguridad
8. **Reportes** -> Generar PDF de accesos por fecha
9. **Respaldos** -> Crear o restaurar backups

### Registro de Visitantes con Camara QR

1. Ir al modulo "Escaneo QR"
2. Presionar "Iniciar escaneo"
3. Mostrar el QR de la placa del vehiculo frente a la camara
4. El sistema identifica al residente y muestra su informacion

---

## Type Checking

El proyecto utiliza **mypy** para verificacion de tipos estaticos.

### Verificar tipos:
```bash
mypy .
```

### Configuracion

El archivo `mypy.ini` contiene la configuracion para el type checking:

- Python version: 3.10
- Warn on missing return types
- Allow untyped function definitions for backward compatibility

### Beneficios del Type Hints

- Mejor IDE support (autocomplete, refactoring)
- Errores detectados en tiempo de desarrollo
- Documentacion implicita en el codigo
- Mas facil de mantener y evolucionar

---

## Dependencias

Las dependencias estan listadas en `requirements.txt`:

| Paquete | Version | Uso |
|---------|---------|-----|
| `customtkinter` | >=5.2.0 | Interfaz grafica moderna |
| `CTkMessagebox` | >=1.0 | Dialogos de notificacion |
| `bcrypt` | >=4.0 | Hashing seguro de contrasenas |
| `reportlab` | >=4.0 | Generacion de PDFs |
| `schedule` | >=1.2 | Programacion de backups automaticos |
| `opencv-python` | >=4.8 | Captura de video para QR |
| `Pillow` | >=10.0 | Procesamiento de imagenes |
| `pyzbar` | >=0.1.9 | Decodificacion de codigos QR |
| `qrcode` | >=7.4 | Generacion de codigos QR |
| `pytest` | >=7.0 | Framework de tests |
| `pytest-cov` | >=4.0 | Cobertura de tests |
| `mypy` | >=1.0 | Type checking |

---

## Empaquetado (.exe)

Para empaquetar la aplicacion como ejecutable de Windows:

```bash
pip install pyinstaller
pyinstaller ResiControl.spec
```

El ejecutable se generara en `dist/ResiControl.exe`.

> **Nota:** Los archivos de la carpeta `backups/`, `qrs/` y `logs/` se crean automaticamente junto al `.exe` al ejecutarse por primera vez.

---

## Tests

### Ejecutar todos los tests:
```bash
pytest tests/ -v
```

### Ejecutar con cobertura:
```bash
pytest tests/ -v --cov=models --cov=auth --cov=validators --cov=backup --cov=report_generator --cov=qr_manager --cov=views
```

### Tests disponibles:

| Modulo | Tests | Cobertura |
|--------|-------|-----------|
| `auth.py` | Hash, verificacion, bloqueo, fortaleza | 100% |
| `validators.py` | Email, cedula, placa, telefono, unidad | 100% |
| `database.py` | Creacion de tablas, indices, seed, usuarios | Completo |
| `models.py` | CRUD de usuarios, residentes, visitantes, accesos, incidentes, parqueaderos, metricas | Completo |
| `qr_manager.py` | Ruta de QR, escaneo | Parcial |
| `backup.py` | Creacion, listado de backups | Parcial |
| `report_generator.py` | Generacion de CSV y PDF | Parcial |

---

## Contribucion

Si deseas contribuir:

1. Haz un fork del proyecto
2. Crea una rama descriptiva: `git checkout -b feature/nueva-funcionalidad`
3. Haz commit de tus cambios: `git commit -m "Agregada: descripcion del cambio"`
4. Haz push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

### Mejoras implementadas (v2.1.0):
- [x] Refactorizacion de interfaz grafica en modulo views/
- [x] Type hints en todos los modulos principales
- [x] Integracion de mypy para verificacion de tipos
- [x] Separacion de responsabilidades en vistas modulares
- [x] Seguridad: migracion a bcrypt con bloqueo por intentos
- [x] Edicion de residentes y visitantes
- [x] Backups automaticos diarios
- [x] Indices en base de datos
- [x] Validacion de campos de formulario
- [x] Tests unitarios
- [x] Logging y auditoria

### Proximas mejoras planificadas:
- [ ] Migracion a PostgreSQL para escalabilidad
- [ ] Exportacion a Excel
- [ ] Sistema de login persistente
- [ ] Modo claro/oscuro
- [ ] Persistencia de bloqueo de usuarios en base de datos

---

## Licencia

Este proyecto esta bajo la licencia **MIT**. Ver el archivo `LICENSE` para mas detalles.

---

## Creditos

Desarrollado como proyecto de aprendizaje para la gestion de seguridad residencial con Python y CustomTkinter.