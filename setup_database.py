"""
Script de configuración de la base de datos
Ejecuta el script SQL para crear la base de datos completa
"""
import psycopg2
import sys
import os

def leer_script_sql():
    """Lee el script SQL del archivo"""
    script_path = os.path.join(os.path.dirname(__file__), 'Sistema_inventario.sql')
    try:
        with open(script_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {script_path}")
        return None
    except Exception as e:
        print(f"❌ Error al leer el archivo SQL: {e}")
        return None

def verificar_postgres_instalado():
    """Verifica si PostgreSQL está instalado"""
    try:
        import psycopg2
        return True
    except ImportError:
        print("❌ PostgreSQL (psycopg2) no está instalado")
        print("   Instala con: pip install psycopg2-binary")
        return False

def conectar_postgres(host, port, user, password):
    """Intenta conectar a PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Base de datos por defecto
        )
        conn.autocommit = True
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Error al conectar a PostgreSQL: {e}")
        return None

def crear_base_datos(conn):
    """Crea la base de datos si no existe"""
    try:
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'sistema_inventario'")
        existe = cursor.fetchone()
        
        if existe:
            print("ℹ️  La base de datos 'sistema_inventario' ya existe")
        else:
            print("📦 Creando base de datos 'sistema_inventario'...")
            cursor.execute("CREATE DATABASE sistema_inventario")
            print("✅ Base de datos creada correctamente")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al crear la base de datos: {e}")
        return False

def ejecutar_script_sql(host, port, user, password, sql_script):
    """Ejecuta el script SQL en la base de datos sistema_inventario"""
    try:
        # Conectar a la base de datos específica
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='sistema_inventario'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Ejecutar el script completo
        print("📝 Ejecutando script SQL...")
        cursor.execute(sql_script)
        
        print("✅ Script ejecutado correctamente")
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al ejecutar el script SQL: {e}")
        return False

def configurar_base_datos():
    """Proceso principal de configuración"""
    print("=" * 60)
    print("CONFIGURACIÓN DE BASE DE DATOS - SISTEMA DE INVENTARIO")
    print("=" * 60)
    print()
    
    # Verificar psycopg2
    if not verificar_postgres_instalado():
        return False
    
    # Solicitar credenciales
    print("Ingrese las credenciales de PostgreSQL:")
    host = input("Host [localhost]: ").strip() or "localhost"
    port = input("Puerto [5432]: ").strip() or "5432"
    user = input("Usuario [postgres]: ").strip() or "postgres"
    password = input("Contraseña: ").strip()
    
    if not password:
        print("❌ La contraseña es obligatoria")
        return False
    
    print()
    print("🔌 Conectando a PostgreSQL...")
    
    # Conectar a PostgreSQL
    conn = conectar_postgres(host, port, user, password)
    if not conn:
        return False
    
    print("✅ Conexión establecida")
    print()
    
    # Crear base de datos si no existe
    if not crear_base_datos(conn):
        conn.close()
        return False
    
    conn.close()
    print()
    
    # Leer script SQL
    sql_script = leer_script_sql()
    if not sql_script:
        return False
    
    # Ejecutar script en la base de datos sistema_inventario
    if ejecutar_script_sql(host, port, user, password, sql_script):
        print()
        print("=" * 60)
        print("✅ BASE DE DATOS CONFIGURADA CORRECTAMENTE")
        print("=" * 60)
        print()
        print("Detalles de conexión:")
        print(f"  - Host: {host}")
        print(f"  - Puerto: {port}")
        print(f"  - Base de datos: sistema_inventario")
        print(f"  - Usuario: {user}")
        print()
        print("Usuario administrador creado:")
        print("  - Usuario: admin")
        print("  - Contraseña: admin123")
        print()
        print("⚠️  IMPORTANTE: Cambie la contraseña del administrador después del primer login")
        print()
        
        # Guardar configuración
        guardar_configuracion(host, port, user, password)
        
        return True
    else:
        return False

def guardar_configuracion(host, port, user, password):
    """Guarda la configuración en múltiples ubicaciones"""
    import json
    
    # 1. Intentar guardar en el directorio actual
    try:
        config_path = os.path.join(os.path.dirname(__file__), '.env')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(f"DB_HOST={host}\n")
            f.write(f"DB_PORT={port}\n")
            f.write(f"DB_NAME=sistema_inventario\n")
            f.write(f"DB_USER={user}\n")
            f.write(f"DB_PASSWORD={password}\n")
        print(f"💾 Configuración guardada en {config_path}")
    except Exception as e:
        print(f"⚠️  No se pudo guardar en directorio local: {e}")
    
    # 2. Guardar en AppData (siempre funciona)
    try:
        appdata_dir = os.path.join(os.getenv('APPDATA'), 'SistemaInventario')
        os.makedirs(appdata_dir, exist_ok=True)
        config_file = os.path.join(appdata_dir, 'config.json')
        
        config = {
            'DB_HOST': host,
            'DB_PORT': port,
            'DB_NAME': 'sistema_inventario',
            'DB_USER': user,
            'DB_PASSWORD': password
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        
        print(f"💾 Configuración guardada en {config_file}")
    except Exception as e:
        print(f"⚠️  No se pudo guardar en AppData: {e}")

if __name__ == "__main__":
    try:
        exito = configurar_base_datos()
        if exito:
            input("\nPresione Enter para continuar...")
            sys.exit(0)
        else:
            input("\nPresione Enter para salir...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Configuración cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        input("\nPresione Enter para salir...")
        sys.exit(1)
