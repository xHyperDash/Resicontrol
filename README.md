# 🏢 ResiControl — Gestión de Seguridad Residencial

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Version](https://img.shields.io/badge/Version-2.0.0-orange)

**ResiControl** es una aplicación de escritorio para la gestión integral de seguridad en conjuntos residenciales pequeños. Permite registrar visitantes y residentes, controlar accesos y salidas, gestionar parqueaderos, llevar un historial completo de movimientos, registrar incidentes, generar reportes en PDF y CSV, y escanear códigos QR de placas de vehículos.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Base de Datos](#-base-de-datos)
- [Dependencias](#-dependencias)
- [Empaquetado](#-empaquetado)
- [Tests](#-tests)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## ⚡ Características

| Módulo | Descripción |
|--------|-------------|
| **🔐 Login seguro** | Autenticación con contraseñas hasheadas en bcrypt, bloqueo tras 5 intentos fallidos (5 min) |
| **📊 Dashboard** | Métricas en tiempo real: entradas del día, residentes activos, parqueaderos ocupados, personas dentro |
| **🚪 Visitantes** | Registro de entrada/salida con consentimiento de datos (Ley 1581), tabla con visitantes activos y edición |
| **👤 Residentes** | Alta, baja (soft-delete), edición, búsqueda, generación de QR y visualización por tablas |
| **🚗 Parqueaderos** | Vista visual de 20 parqueaderos (10 residentes + 10 visitantes), asignación manual a visitantes |
| **📜 Historial** | Historial completo de accesos con filtros por fecha, tipo y búsqueda; exportación a CSV |
| **⚠️ Incidentes** | Registro de incidentes con niveles de alerta (bajo, medio, alto) |
| **🔍 Escaneo QR** | Cámara en tiempo real con decodificación de QR para identificar residentes |
| **📄 Reportes PDF** | Generación de reportes con tablas formateadas por rango de fechas y tipo |
| **💾 Backups** | Backups automáticos diarios a las 00:00, retención de 30 días, restauración desde UI |
| **🔑 Gestión de Usuarios** | Solo admin: crear/eliminar usuarios con roles (admin, operador, residente) |

---

## 🏗️ Arquitectura

El proyecto sigue una **arquitectura modular** con separación de responsabilidades:

```
ResiControl/
│
├── main.py                    # Punto de entrada
├── resicontrol.py             # Interfaz gráfica (CustomTkinter) - capa Vista
├── config.py                  # Constantes, rutas y colores
├── logger.py                  # Logging con rotación de archivos
├── auth.py                    # Autenticación: bcrypt, bloqueo, validación de contraseñas
├── validators.py              # Validación de campos de formulario
├── database.py                # Inicialización de BD, tablas, índices, seed
├── models.py                  # Capa de datos: todas las operaciones CRUD
├── backup.py                  # Backup automático diario y manual
├── qr_manager.py              # Generación y escaneo de códigos QR
├── report_generator.py         # Generación de reportes PDF y CSV
│
├── tests/
│   └── test_resicontrol.py    # Tests unitarios (pytest)
│
├── backups/                   # Carpeta de backups generados (gitignored)
├── qrs/                       # Carpeta de QR generados (gitignored)
├── logs/                      # Carpeta de logs (gitignored)
│
├── resicontrol.db             # Base de datos SQLite
├── requirements.txt           # Dependencias
├── ResiControl.spec           # Configuración de PyInstaller
└── README.md                  # Este archivo
```

### Flujo de Datos

```
Usuario → [resicontrol.py - Vista] → [models.py - Datos] → [resicontrol.db - SQLite]
                                              ↑
[config.py - Rutas] ← [backup.py - Respaldos automáticos]
[auth.py - Seguridad] ← [validators.py - Validaciones]
[qr_manager.py - QR] ← [report_generator.py - Reportes]
```

---

## 🚀 Instalación

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

**4. Ejecutar la aplicación:**
```bash
python main.py
```

### Credenciales por defecto

| Usuario  | Contraseña | Rol       |
|----------|------------|-----------|
| `admin`  | `admin123` | Admin     |
| `portero`| `1234`     | Operador  |

> ⚠️ **Importante:** Cambia las contraseñas por defecto antes de poner en producción.

---

## 🖥️ Uso

### Interfaz de Usuario

La aplicación utiliza **CustomTkinter** para una interfaz moderna con tema oscuro.

- **Sidebar izquierdo:** Navegación entre módulos con íconos
- **Área central:** Contenido del módulo seleccionado
- **Dashboard:** Métricas actualizadas automáticamente cada 10 segundos

### Flujo Típico de Operación

1. **Login** → Iniciar sesión con usuario y contraseña
2. **Dashboard** → Revisar métricas del día
3. **Visitantes** → Registrar entrada (nombre, cédula, placa, unidad) → Marcar salida al irse
4. **Residentes** → Agregar/editar residentes, generar QR de placas
5. **Parqueaderos** → Visualizar estado, asignar a visitantes
6. **Historial** → Consultar registros, filtrar, exportar CSV
7. **Incidentes** → Registrar eventos de seguridad
8. **Reportes** → Generar PDF de accesos por fecha
9. **Respaldos** → Crear o restaurar backups

### Registro de Visitantes con Cámara QR

1. Ir al módulo "Escaneo QR"
2. Presionar "Iniciar escaneo"
3. Mostrar el QR de la placa del vehículo frente a la cámara
4. El sistema identifica al residente y muestra su información

---

## 📦 Dependencias

Las dependencias están listadas en `requirements.txt`:

| Paquete | Versión | Uso |
|---------|---------|-----|
| `customtkinter` | >=5.2.0 | Interfaz gráfica moderna |
| `CTkMessagebox` | >=1.0 | Diálogos de notificación |
| `bcrypt` | >=4.0 | Hashing seguro de contraseñas |
| `reportlab` | >=4.0 | Generación de PDFs |
| `schedule` | >=1.2 | Programación de backups automáticos |
| `opencv-python` | >=4.8 | Captura de video para QR |
| `Pillow` | >=10.0 | Procesamiento de imágenes |
| `pyzbar` | >=0.1.9 | Decodificación de códigos QR |
| `qrcode` | >=7.4 | Generación de códigos QR |
| `pytest` | >=7.0 | Framework de tests |
| `pytest-cov` | >=4.0 | Cobertura de tests |

---

## 🔧 Empaquetado (.exe)

Para empaquetar la aplicación como ejecutable de Windows:

```bash
pip install pyinstaller
pyinstaller ResiControl.spec
```

El ejecutable se generará en `dist/ResiControl.exe`.

> **Nota:** Los archivos de la carpeta `backups/`, `qrs/` y `logs/` se crean automáticamente junto al `.exe` al ejecutarse por primera vez.

---

## 🧪 Tests

### Ejecutar todos los tests:
```bash
pytest tests/ -v
```

### Ejecutar con cobertura:
```bash
pytest tests/ -v --cov=models --cov=auth --cov=validators --cov=backup --cov=report_generator --cov=qr_manager
```

### Tests disponibles:

| Módulo | Tests | Cobertura |
|--------|-------|-----------|
| `auth.py` | Hash, verificación, bloqueo, fortaleza | 100% |
| `validators.py` | Email, cédula, placa, teléfono, unidad | 100% |
| `database.py` | Creación de tablas, índices, seed, usuarios | Completo |
| `models.py` | CRUD de usuarios, residentes, visitantes, accesos, incidentes, parqueaderos, métricas | Completo |
| `qr_manager.py` | Ruta de QR, escaneo | Parcial |
| `backup.py` | Creación, listado de backups | Parcial |
| `report_generator.py` | Generación de CSV y PDF | Parcial |

---

## 🤝 Contribución

Si deseas contribuir:

1. Haz un fork del proyecto
2. Crea una rama descriptiva: `git checkout -b feature/nueva-funcionalidad`
3. Haz commit de tus cambios: `git commit -m "Agregada: descripción del cambio"`
4. Haz push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

### Próximas mejoras planificadas:
- [x] Seguridad: migración a bcrypt con bloqueo por intentos
- [x] Edición de residentes y visitantes
- [x] Backups automáticos diarios
- [x] Índices en base de datos
- [x] Validación de campos de formulario
- [x] Tests unitarios
- [x] Logging y auditoría
- [ ] Migración a PostgreSQL para escalabilidad
- [ ] Exportación a Excel
- [ ] Sistema de login persistente
- [ ] Modo claro/oscuro

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver el archivo `LICENSE` para más detalles.

---

## 🙏 Créditos

Desarrollado como proyecto de aprendizaje para la gestión de seguridad residencial con Python y CustomTkinter.