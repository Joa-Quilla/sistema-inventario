"""
Conexión a la base de datos PostgreSQL usando patrón Singleton
"""
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import json

# Intentar cargar desde diferentes ubicaciones
def cargar_configuracion():
    """Carga la configuración desde múltiples ubicaciones posibles"""
    # 1. Intentar desde .env en el directorio actual
    load_dotenv()
    
    # 2. Si no hay contraseña, intentar desde AppData
    if not os.getenv('DB_PASSWORD'):
        appdata_path = os.path.join(os.getenv('APPDATA'), 'SistemaInventario', 'config.json')
        if os.path.exists(appdata_path):
            try:
                with open(appdata_path, 'r') as f:
                    config = json.load(f)
                    for key, value in config.items():
                        os.environ[key] = str(value)
            except:
                pass
    
    # 3. Si aún no hay contraseña, intentar leer del archivo de instalación
    if not os.getenv('DB_PASSWORD'):
        try:
            install_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
            if os.path.exists(install_path):
                from dotenv import dotenv_values
                config = dotenv_values(install_path)
                for key, value in config.items():
                    if not os.getenv(key):
                        os.environ[key] = value
        except:
            pass

cargar_configuracion()


class DatabaseConnection:
    """
    Clase Singleton para manejar la conexión a PostgreSQL
    Utiliza connection pooling para mejor rendimiento
    """
    _instance = None
    _connection_pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        """Inicializa el pool de conexiones"""
        try:
            self._connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'sistema_inventario'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', '')
            )
            print("[OK] Pool de conexiones creado exitosamente")
        except Exception as e:
            print(f"[ERROR] Error al crear pool de conexiones: {e}")
            raise

    def get_connection(self):
        """Obtiene una conexión del pool"""
        try:
            connection = self._connection_pool.getconn()
            return connection
        except Exception as e:
            print(f"[ERROR] Error al obtener conexion: {e}")
            raise

    def return_connection(self, connection):
        """Devuelve una conexión al pool"""
        try:
            self._connection_pool.putconn(connection)
        except Exception as e:
            print(f"[ERROR] Error al devolver conexion: {e}")

    def execute_query(self, query, params=None, fetch=True):
        """
        Ejecuta una consulta SQL
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            fetch: Si True o 'all', retorna todos los resultados (SELECT)
                   Si 'one', retorna solo el primer resultado
                   Si False, solo ejecuta sin retornar datos (INSERT/UPDATE/DELETE)
        
        Returns:
            Lista de diccionarios con los resultados (si fetch=True o 'all')
            Diccionario con el primer resultado (si fetch='one')
            Número de filas afectadas (si fetch=False)
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(query, params)
            
            if fetch == 'one':
                result = cursor.fetchone()
                connection.commit()  # Commit para RETURNING
                return dict(result) if result else None
            elif fetch == 'all' or fetch is True:
                results = cursor.fetchall()
                connection.commit()  # Commit por si acaso
                # Convertir RealDictRow a dict normal
                return [dict(row) for row in results]
            else:
                connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"[ERROR] Error ejecutando query: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.return_connection(connection)

    def execute_many(self, query, params_list):
        """
        Ejecuta múltiples inserts/updates en una sola transacción
        
        Args:
            query: Consulta SQL
            params_list: Lista de tuplas con parámetros
        
        Returns:
            Número total de filas afectadas
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.executemany(query, params_list)
            connection.commit()
            
            return cursor.rowcount
                
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"[ERROR] Error ejecutando query multiple: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.return_connection(connection)

    def test_connection(self):
        """Prueba la conexión a la base de datos"""
        try:
            result = self.execute_query("SELECT version();")
            print(f"[OK] Conexion exitosa a PostgreSQL")
            print(f"Version: {result[0]['version']}")
            return True
        except Exception as e:
            print(f"[ERROR] Error de conexion: {e}")
            return False

    def close_all_connections(self):
        """Cierra todas las conexiones del pool"""
        try:
            if self._connection_pool:
                self._connection_pool.closeall()
                print("[OK] Pool de conexiones cerrado")
        except Exception as e:
            print(f"[ERROR] Error al cerrar pool: {e}")


# Función helper para obtener la instancia
def get_db():
    """Retorna la instancia singleton de DatabaseConnection"""
    return DatabaseConnection()


# Función helper para obtener una conexión directa
def get_connection():
    """Obtiene una conexión del pool"""
    return get_db().get_connection()
