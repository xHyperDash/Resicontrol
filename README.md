# ResiControl

![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Version](https://img.shields.io/badge/Version-2.3.0-orange)

**ResiControl** es una solución de escritorio para la gestión integral de seguridad en conjuntos residenciales pequeños. La aplicación permite registrar visitantes y residentes, controlar accesos y salidas, administrar parqueaderos, mantener un historial completo de movimientos, registrar incidentes, generar reportes en PDF y CSV, y escanear códigos QR de placas de vehículos.

---

## Descripción general

ResiControl está diseñado para simplificar la operación diaria de seguridad en residencias con una interfaz moderna y un flujo de trabajo claro. El sistema combina una base de datos local, autenticación segura y módulos especializados para cubrir el ciclo completo de gestión de acceso.

### Funcionalidades principales

- Gestión de residentes y visitantes.
- Control de acceso y salida con trazabilidad.
- Gestión visual de parqueaderos.
- Historial de eventos con filtros y exportación.
- Registro de incidentes y alertas.
- Generación de reportes PDF y CSV.
- Escaneo de códigos QR para identificación rápida.
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
├── main.py                       Punto de entrada
├── resicontrol.py                Aplicación principal (CustomTkinter)
├── config.py                     Definición centralizada de temas y estilos
├── icons.py                      Generación de iconos vectoriales
├── logger.py                     Registro de eventos con rotación
├── auth.py                       Autenticación, bloqueo y validación de credenciales
├── validators.py                 Validación de campos de entrada
├── database.py                   Inicialización, esquema y seed de la base de datos
├── models.py                     Capa de datos y operaciones CRUD
├── backup.py                     Backups diarios y manuales
├── qr_manager.py                 Generación y lectura de códigos QR
├── report_generator.py           Generación de reportes PDF y CSV
│
├── views/                        Módulos de interfaz gráfica
│   ├── base.py                    Componentes reutilizables
│   ├── navigation.py              Navegación lateral
│   ├── dashboard.py               Métricas y accesos rápidos
│   ├── residents.py               Gestión de residentes
│   ├── visitors.py                Registro de visitantes
│   ├── parking.py                 Gestión de parqueaderos
│   ├── history.py                 Historial de accesos
│   ├── incidents.py               Registro de incidentes
│   ├── reports.py                 Reportes PDF
│   ├── backup.py                  Respaldos
│   ├── users.py                   Administración de usuarios
│   ├── qr_scanner.py              Escaneo QR
│   ├── table.py                   Tabla reutilizable
│   └── toast.py                   Notificaciones no bloqueantes
│
├── tests/                        Pruebas automatizadas
├── backups/                      Respaldos generados
├── qrs/                          Códigos QR generados
├── reportes/                     Reportes CSV y PDF generados
├── logs/                         Archivos de log
├── resicontrol.db                Base de datos SQLite
├── requirements.txt              Dependencias del proyecto
├── mypy.ini                      Configuración de type checking
├── ResiControl.spec              Configuración de PyInstaller
└── README.md                     Documentación del proyecto
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

- Python 3.10 o superior
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

4. Ejecuta la aplicación:

```bash
python main.py
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
4. El sistema identifica el residente y muestra la información asociada.

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

---

## Empaquetado

Para generar el ejecutable de Windows:

```bash
pip install pyinstaller
pyinstaller ResiControl.spec
```

El ejecutable se generará en `dist/ResiControl.exe`.

> Las carpetas `backups/`, `qrs/` y `logs/` se crean automáticamente cuando la aplicación se ejecuta por primera vez.

---

## Testing

### Ejecutar todos los tests

```bash
pytest tests/ -v
```

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
| `report_generator.py` | Generación de CSV y PDF |

---

## Type checking

El proyecto utiliza **mypy** para la verificación estática de tipos.

### Verificación

```bash
mypy .
```

### Configuración relevante

- **Python:** 3.11
- **Advertencias sobre return types faltantes:** activadas
- **Funciones sin tipado:** permitidas por compatibilidad retroactiva

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
- Vistas con scroll en formularios largos (visitantes, residentes, usuarios).
- Sidebar sin frames envolventes (espaciado compacto y preciso).
- Exportación CSV fiable con filtros y rutas absolutas.
- Backups automáticos diarios.
- Índices en la base de datos.
- Validación de formularios.
- Tests automatizados.
- Logging y auditoría.

### Próximas mejoras

- Migración a PostgreSQL.
- Exportación a Excel.
- Login persistente.
- Modo claro/oscuro.
- Persistencia de bloqueo de usuarios en base de datos.

---

## Licencia

Este proyecto se distribuye bajo la licencia **MIT**.

---

## Créditos

Desarrollado como proyecto de aprendizaje para la gestión de seguridad residencial con Python y CustomTkinter.
