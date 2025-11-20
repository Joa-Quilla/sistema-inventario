# MANUAL DE INSTALACIÓN - SISTEMA DE INVENTARIO

## Requisitos Previos

1. **PostgreSQL 12 o superior** instalado en el sistema
   - Descargar desde: https://www.postgresql.org/download/
   - Durante la instalación, recordar la contraseña del usuario `postgres`

2. **Python 3.8 o superior** (solo si se va a configurar manualmente)
   - Descargar desde: https://www.python.org/downloads/

## Instalación Rápida

### Paso 1: Instalar PostgreSQL
Si no tiene PostgreSQL instalado:
1. Descargue PostgreSQL desde el enlace anterior
2. Ejecute el instalador
3. Anote la contraseña que configure para el usuario `postgres`
4. Deje el puerto por defecto: 5432

### Paso 2: Configurar la Base de Datos
1. Abra una terminal/PowerShell en esta carpeta
2. Ejecute el script de configuración:
   ```
   python setup_database.py
   ```
3. Ingrese las credenciales de PostgreSQL cuando se le soliciten:
   - Host: localhost (presione Enter para usar el valor por defecto)
   - Puerto: 5432 (presione Enter para usar el valor por defecto)
   - Usuario: postgres (presione Enter para usar el valor por defecto)
   - Contraseña: [la contraseña que configuró en PostgreSQL]

4. El script creará automáticamente:
   - La base de datos `inventario_db`
   - Todas las tablas necesarias
   - Datos iniciales (roles, permisos, usuario admin)

### Paso 3: Ejecutar la Aplicación
1. Ejecute el archivo `Sistema_Inventario.exe`
2. Use las credenciales del administrador para el primer login:
   - Usuario: `admin`
   - Contraseña: `admin123`
3. **IMPORTANTE:** Cambie la contraseña del administrador después del primer acceso

## Instalación Manual (Desarrolladores)

Si desea ejecutar desde el código fuente:

1. Instale las dependencias:
   ```
   pip install -r requirements.txt
   ```

2. Configure la base de datos:
   ```
   python setup_database.py
   ```

3. Ejecute la aplicación:
   ```
   python src/main.py
   ```

## Solución de Problemas

### Error: "No se puede conectar a PostgreSQL"
- Verifique que PostgreSQL esté ejecutándose
- Compruebe que las credenciales sean correctas
- Asegúrese de que el puerto 5432 no esté bloqueado por el firewall

### Error: "Módulo no encontrado"
- Si ejecuta desde código fuente, instale las dependencias:
  ```
  pip install -r requirements.txt
  ```

### La aplicación no inicia
- Verifique que la base de datos esté configurada correctamente
- Revise el archivo `.env` para confirmar las credenciales

## Soporte

Para reportar problemas o solicitar ayuda, contacte al equipo de desarrollo.

## Licencia

Sistema de Inventario - Proyecto Universitario
Ingeniería de Software II - 2025
