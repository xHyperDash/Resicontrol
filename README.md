# ResiControl

![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Version](https://img.shields.io/badge/Version-2.3.0-orange)

**ResiControl** es una solución de escritorio para la gestión integral de seguridad en conjuntos residenciales pequeños. La aplicación permite registrar visitantes y residentes, controlar accesos y salidas, administrar parqueaderos, mantener un historial completo de movimientos, registrar incidentes, generar reportes en PDF y CSV, y escanear códigos QR de placas de vehículos.

---

## Descripción general

ResiControl está diseñado para simplificar la operación diaria de seguridad en residencias con una interfaz moderna y un flujo de trabajo claro. El sistema combina una base de datos local, autenticación segura y módulos especializados para cubrir el ciclo completo de gestión de acceso.

### Funcionalidades principales

- Gestión de residentes y visitantes con entrada/salida.
- Control de acceso con trazabilidad y detección de duplicados.
- Gestión visual de parqueaderos con modo edición (agregar/quitar en lote).
- Historial de eventos con filtros y exportación CSV/XLSX.
- Registro de incidentes y alertas.
- Generación de reportes PDF, CSV y XLSX.
- Escaneo de códigos QR con registro automático de entrada.
- Dashboard con gráficos en tiempo real (matplotlib).
- Backups automáticos y restauración desde la interfaz.
- Gestión de usuarios con roles administrativos.

---

## Tabla de contenidos

- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Uso](#uso)
- [Dependencias](#dependencias)
- [Empaquetado](#empaquetado)
- [Testing](#testing)
- [Type checking](#type-checking)
- [Contribución](#contribución)
- [Licencia](#licencia)

---

## Arquitectura

El proyecto sigue una arquitectura modular, con separación clara de responsabilidades y un enfoque consistente en la mantenibilidad:

```text
ResiControl/
│
├── resicontrol.py                Punto de entrada
├── config.py                     Configuración y constantes
├── database.py                   Inicialización y esquema de BD
├── models.py                     Capa de datos y operaciones CRUD
├── auth.py                       Autenticación y validación
├── validators.py                 Validación de campos
├── icons.py                      Generación de iconos vectoriales
├── logger.py                     Registro de eventos
├── backup.py                     Backups automáticos
├── qr_manager.py                 Generación y lectura de QR
├── report_generator.py           Reportes PDF, CSV y XLSX
│
├── views/                        Módulos de interfaz gráfica
│   ├── base.py                   Componentes base reutilizables
│   ├── navigation.py             Navegación lateral
│   ├── dashboard.py              Dashboard con gráficos
│   ├── residents.py              Gestión de residentes
│   ├── visitors.py               Registro de visitantes
│   ├── parking.py                Gestión de parqueaderos
│   ├── history.py                Historial de accesos
│   ├── incidents.py              Incidentes
│   ├── reports.py                Reportes
│   ├── backup.py                 Respaldos
│   ├── users.py                  Administración de usuarios
│   ├── qr_scanner.py             Escaneo QR
│   ├── table.py                  Tabla reutilizable
│   └── toast.py                  Notificaciones toast
│
├── tests/                        Pruebas automatizadas
├── seed_test_data.py             Datos de prueba idempotentes
├── er_diagram.png                Diagrama entidad-relación
├── ResiControl_ER.gv             Fuente del diagrama ER
├── requirements.txt              Dependencias del proyecto
├── mypy.ini                      Configuración de mypy
├── ResiControl.spec              Configuración de PyInstaller
├── setup.iss                     Script de Inno Setup
└── README.md                     Documentación
```

### Flujo de datos

```text
Usuario → Vista → models.py → SQLite
```

### Flujo de navegación

La navegación entre vistas se concentra en un único punto de entrada para evitar inconsistencias y duplicación de estado:

```text
Sidebar / accesos rápidos → _cambiar_pagina() → reemplazo de la vista actual
```

---

## Instalación

### Requisitos previos

- Python 3.11 o superior
- `pip`

### Pasos

1. Clona el repositorio y accede al directorio del proyecto:

```bash
git clone <url-del-repositorio>
cd ResiControl
```

2. Crea y activa un entorno virtual:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. (Opcional) Puebla la base de datos con datos de demostración:

```bash
python seed_test_data.py
```

5. Ejecuta la aplicación:

```bash
python resicontrol.py
```

### Credenciales por defecto

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `admin` | `admin123` | Administrador |
| `portero` | `1234` | Operador |

> Se recomienda cambiar estas credenciales antes de utilizar el sistema en entornos reales.

---

## Uso

### Flujo operativo recomendado

1. Inicia sesión con el usuario autorizado.
2. Revisa el dashboard para ver las métricas del día.
3. Registra visitantes y residentes según sea necesario.
4. Asigna o consulta espacios de parqueadero.
5. Revise el historial y exporte información cuando corresponda.
6. Registre incidentes y genere reportes.

### Escaneo QR

1. Accede al módulo **Escaneo QR**.
2. Presiona **Iniciar escaneo**.
3. Coloca el código QR frente a la cámara.
4. El sistema identifica al residente y registra automáticamente la entrada (o muestra advertencia si ya está dentro).

### Parqueaderos — Modo edición

1. Presiona **Editar** para activar el modo edición.
2. Selecciona espacios libres (resaltados en verde claro) para agregar/quitar.
3. Usa el panel de agregado masivo para crear varios espacios de golpe.
4. Presiona **Guardar cambios de edición** para confirmar.

---

## Dependencias

Las dependencias principales del proyecto son:

| Paquete | Versión | Uso |
| --- | --- | --- |
| `customtkinter` | `>=5.2.0` | Interfaz gráfica moderna |
| `CTkMessagebox` | `>=1.0` | Diálogos de notificación |
| `bcrypt` | `>=4.0` | Hash seguro de contraseñas |
| `reportlab` | `>=4.0` | Generación de PDFs |
| `schedule` | `>=1.2` | Programación de backups |
| `opencv-python` | `>=4.8` | Captura de video para QR |
| `Pillow` | `>=10.0` | Procesamiento de imágenes |
| `pyzbar` | `>=0.1.9` | Decodificación de QR |
| `qrcode` | `>=7.4` | Generación de QR |
| `pytest` | `>=7.0` | Pruebas automatizadas |
| `pytest-cov` | `>=4.0` | Cobertura de pruebas |
| `mypy` | `>=1.0` | Verificación estática de tipos |
| `matplotlib` | `>=3.7` | Gráficos en el dashboard |
| `openpyxl` | `>=3.1` | Exportación a Excel XLSX |
| `graphviz` | `>=0.20` | Diagrama entidad-relación |

---

## Empaquetado

### Ejecutable portátil (PyInstaller)

```bash
pip install pyinstaller
pyinstaller ResiControl.spec
```

El ejecutable se generará en `dist/ResiControl/ResiControl.exe`.

### Instalador de Windows (Inno Setup)

Requiere [Inno Setup 6+](https://jrsoftware.org/isdl.php).

```bash
iscc setup.iss
```

El instalador se genera en `installer/ResiControl_v2.3.0_Setup.exe`.

### Modo empaquetado

Cuando se ejecuta desde el instalador, la aplicación almacena automáticamente los datos en `%APPDATA%\ResiControl\` (backups, QR, reportes, logs). En modo fuente, los datos se guardan junto al proyecto.

> Las carpetas `backups/`, `qrs/`, `logs/`, `reportes/` se crean automáticamente al iniciar la aplicación por primera vez.

---

## Testing

### Ejecutar todos los tests

```bash
pytest tests/ -v
```

> **52 tests** — todos pasando.

### Ejecutar con cobertura

```bash
pytest tests/ -v --cov=models --cov=auth --cov=validators --cov=backup --cov=report_generator --cov=qr_manager --cov=views
```

### Cobertura actual

| Módulo | Estado |
| --- | --- |
| `auth.py` | Validación de hash, verificación, bloqueo y fortaleza |
| `validators.py` | Validación de email, cédula, placa, teléfono y unidad |
| `database.py` | Creación de tablas, índices, seed y usuarios |
| `models.py` | CRUD de usuarios, residentes, visitantes, accesos, incidentes, parqueaderos y métricas |
| `qr_manager.py` | Generación y escaneo de QR |
| `backup.py` | Creación y listado de backups |
| `report_generator.py` | Generación de CSV, PDF y XLSX |

---

## Type checking

El proyecto utiliza **mypy** para la verificación estática de tipos.

```bash
mypy .
```

> **Estado actual:** `Success: no issues found in 28 source files` — 0 errores, 0 advertencias.

---

## Contribución

Si deseas colaborar en el proyecto:

1. Haz un fork del repositorio.
2. Crea una rama con un nombre descriptivo.
3. Realiza tus cambios y confirma el commit.
4. Sube la rama y abre un Pull Request.

### Mejoras implementadas

- Temas centralizados en `config.py`.
- Iconos vectoriales basados en glifos del sistema en `icons.py`.
- Componente reutilizable `TableView` en `views/table.py`.
- Navegación unificada mediante `_cambiar_pagina`.
- Notificaciones toast no bloqueantes.
- Gráficos interactivos en el dashboard (matplotlib).
- Tablas con columnas de ancho fijo para alineación perfecta.
- Generación de QR desde el diálogo de edición de residentes.
- Vistas con scroll en formularios largos.
- Sidebar sin frames envolventes (espaciado compacto y preciso).
- Exportación CSV, PDF y XLSX con filtros y rutas absolutas.
- Backups automáticos diarios.
- Índices en la base de datos.
- Validación de formularios.
- Tests automatizados (52 tests, 0 mypy errores).
- Logging y auditoría.
- Dashboard con 3 gráficos en tiempo real (entradas por hora, incidentes, dentro ahora).
- Escaneo QR con registro automático de entrada.
- Modo edición de parqueaderos (agregar/quitar en lote).
- Calendario para selección de fechas en reportes.
- Confirmación antes de cerrar sesión.
- Empaquetado con PyInstaller + Inno Setup.
- Almacenamiento en `%APPDATA%` en modo instalado.
- Entrada rápida para residentes desde el mismo módulo.
- Prevención de entradas duplicadas.
- Diagrama entidad-relación generado con Graphviz.
- Datos de prueba idempotentes (`seed_test_data.py`).

### Próximas mejoras

- Migración a PostgreSQL.
- Login persistente.
- Modo claro/oscuro.
- Persistencia de bloqueo de usuarios en base de datos.
- Notificaciones en tiempo real.

---

## Licencia

Este proyecto se distribuye bajo la licencia **MIT**.

---

## Créditos

Desarrollado como proyecto de aprendizaje para la gestión de seguridad residencial con Python y CustomTkinter.
