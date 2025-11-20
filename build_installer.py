"""
Script para generar el instalador del Sistema de Inventario
Utiliza PyInstaller para crear el ejecutable
"""
import os
import sys
import subprocess
import shutil

def limpiar_directorios():
    """Limpia directorios de builds anteriores"""
    directorios = ['build', 'dist', '__pycache__']
    for dir in directorios:
        if os.path.exists(dir):
            print(f"🗑️  Eliminando {dir}...")
            shutil.rmtree(dir)

def crear_ejecutable():
    """Crea el ejecutable con PyInstaller"""
    print("📦 Creando ejecutable con PyInstaller...")
    
    # Verificar si existe el ícono
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    icon_param = ['--icon=' + icon_path] if os.path.exists(icon_path) else []
    
    # Usar python -m PyInstaller en lugar de pyinstaller directamente
    comando = [
        sys.executable, '-m', 'PyInstaller',
        '--name=Sistema_Inventario',
        '--onefile',
        '--windowed',
        '--hidden-import=psycopg2',
        '--hidden-import=flet',
        '--collect-all=flet',
        '--noconfirm',
        'src/main.py'
    ] + icon_param
    
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✅ Ejecutable creado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear el ejecutable: {e}")
        if e.stderr:
            print(e.stderr)
        return False
    except FileNotFoundError:
        print("❌ PyInstaller no encontrado. Instalando...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
            print("✅ PyInstaller instalado. Reintentando...")
            resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
            print("✅ Ejecutable creado correctamente")
            return True
        except Exception as install_error:
            print(f"❌ Error al instalar PyInstaller: {install_error}")
            return False

def crear_carpeta_distribucion():
    """Crea la carpeta final de distribución"""
    print("📁 Creando carpeta de distribución...")
    
    dist_folder = "Sistema_Inventario_v1.0"
    
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    
    os.makedirs(dist_folder)
    
    # Copiar ejecutable
    shutil.copy('dist/Sistema_Inventario.exe', dist_folder)
    
    # Copiar script de configuración de BD
    shutil.copy('setup_database.py', dist_folder)
    
    # Copiar script SQL
    shutil.copy('Sistema_inventario.sql', dist_folder)
    
    # Copiar README
    shutil.copy('MANUAL_INSTALACION.md', dist_folder)
    
    # Copiar requirements
    shutil.copy('requirements.txt', dist_folder)
    
    print(f"✅ Carpeta de distribución creada: {dist_folder}")
    return dist_folder

def crear_manual_instalacion():
    """Crea el manual de instalación"""
    manual = """# MANUAL DE INSTALACIÓN - SISTEMA DE INVENTARIO

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
"""
    
    with open('MANUAL_INSTALACION.md', 'w', encoding='utf-8') as f:
        f.write(manual)
    
    print("✅ Manual de instalación creado")

def main():
    print("=" * 60)
    print("GENERADOR DE INSTALADOR - SISTEMA DE INVENTARIO")
    print("=" * 60)
    print()
    
    # Verificar que PyInstaller esté instalado
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller no está instalado")
        print("   Instale con: pip install pyinstaller")
        sys.exit(1)
    
    # Limpiar builds anteriores
    limpiar_directorios()
    
    # Crear manual de instalación
    crear_manual_instalacion()
    
    # Crear ejecutable
    if not crear_ejecutable():
        print("❌ Error al crear el ejecutable")
        sys.exit(1)
    
    # Crear carpeta de distribución
    carpeta_dist = crear_carpeta_distribucion()
    
    print()
    print("=" * 60)
    print("✅ INSTALADOR CREADO CORRECTAMENTE")
    print("=" * 60)
    print()
    print(f"📁 Carpeta de distribución: {carpeta_dist}")
    print()
    print("Contenido:")
    print("  - Sistema_Inventario.exe (aplicación)")
    print("  - setup_database.py (configurador de BD)")
    print("  - Sistema_inventario.sql (script de BD)")
    print("  - MANUAL_INSTALACION.md (instrucciones)")
    print("  - requirements.txt (dependencias)")
    print()
    print("📝 Próximos pasos:")
    print("  1. Comprima la carpeta en un archivo .zip")
    print("  2. Comparta el .zip con el cliente")
    print("  3. El cliente debe seguir el MANUAL_INSTALACION.md")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Proceso cancelado")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
