# Sistema de Inventario

Sistema completo de gestión de inventario, ventas y compras desarrollado con Python y Flet.

## Características

- ✅ Gestión de clientes, empleados y proveedores
- ✅ Control de productos y categorías
- ✅ Registro de compras y ventas
- ✅ Sistema de cajas (apertura/cierre)
- ✅ Generación de reportes (PDF/Excel)
- ✅ Sistema de roles y permisos
- ✅ Interfaz moderna con Flet

## Requisitos

- Python 3.10 o superior
- PostgreSQL 12 o superior

## Instalación

1. Clonar el repositorio
2. Crear entorno virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar base de datos:
   - Crear base de datos `sistema_inventario` en PostgreSQL
   - Ejecutar el script SQL proporcionado
   - Copiar `.env.example` a `.env` y configurar credenciales

5. Ejecutar la aplicación:
   ```bash
   python src/main.py
   ```

## Credenciales por defecto

- **Usuario:** admin
- **Contraseña:** admin123

## Estructura del Proyecto

```
sistema_inventario/
├── src/
│   ├── models/          # Modelos de datos
│   ├── views/           # Interfaces Flet
│   ├── controllers/     # Lógica de negocio
│   ├── repositories/    # Acceso a datos
│   ├── services/        # Servicios (reportes, auth)
│   ├── database/        # Conexión BD
│   ├── utils/           # Utilidades
│   └── main.py          # Punto de entrada
├── tests/               # Pruebas
└── requirements.txt     # Dependencias
```

## Tecnologías

- **Frontend:** Flet
- **Backend:** Python
- **Base de Datos:** PostgreSQL
- **Reportes:** ReportLab, OpenPyXL
