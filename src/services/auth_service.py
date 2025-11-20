"""
Servicio de Autenticación y Autorización
Maneja login, verificación de permisos y sesiones
"""
import hashlib
from datetime import datetime
from typing import Optional, Dict, List


class AuthService:
    """Servicio para manejar autenticación y permisos"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.sesion_actual = None  # Almacena datos del usuario logueado

    @staticmethod
    def hash_password(password: str) -> str:
        """Encripta una contraseña usando SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, usuario: str, password: str) -> Dict:
        """
        Autentica un usuario
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'empleado': dict (si success=True)
            }
        """
        try:
            password_hash = self.hash_password(password)
            
            query = """
                SELECT 
                    e.id_empleado,
                    e.usuario,
                    e.id_rol,
                    r.nombre as nombre_rol,
                    e.puesto,
                    e.estado as empleado_activo,
                    p.id_persona,
                    p.nombre,
                    p.apellido,
                    p.email,
                    p.telefono
                FROM empleados e
                JOIN personas p ON e.id_persona = p.id_persona
                JOIN roles r ON e.id_rol = r.id_rol
                WHERE e.usuario = %s 
                AND e.password = %s
                AND e.estado = true
                AND p.estado = true
            """
            
            resultado = self.db.execute_query(query, (usuario, password_hash))
            
            if not resultado:
                return {
                    'success': False,
                    'message': 'Usuario o contraseña incorrectos'
                }
            
            empleado = resultado[0]
            
            # Actualizar último login
            self.db.execute_query(
                "UPDATE empleados SET ultimo_login = %s WHERE id_empleado = %s",
                (datetime.now(), empleado['id_empleado']),
                fetch=False
            )
            
            # Guardar sesión
            self.sesion_actual = empleado
            
            # Registrar en logs
            self._registrar_log(empleado['id_empleado'], 'login', None, None, 'Login exitoso')
            
            return {
                'success': True,
                'message': f"Bienvenido {empleado['nombre']} {empleado['apellido']}",
                'empleado': empleado
            }
            
        except Exception as e:
            print(f"❌ Error en login: {e}")
            return {
                'success': False,
                'message': f'Error al iniciar sesión: {str(e)}'
            }

    def logout(self):
        """Cierra la sesión actual"""
        if self.sesion_actual:
            self._registrar_log(
                self.sesion_actual['id_empleado'],
                'logout',
                None,
                None,
                'Logout'
            )
            self.sesion_actual = None

    def verificar_permiso(self, modulo: str, accion: str) -> bool:
        """
        Verifica si el usuario actual tiene permiso para realizar una acción
        
        Args:
            modulo: Nombre del módulo (clientes, productos, ventas, etc.)
            accion: Acción a realizar (crear, leer, actualizar, eliminar)
        
        Returns:
            bool: True si tiene permiso, False si no
        """
        if not self.sesion_actual:
            return False
        
        try:
            query = """
                SELECT COUNT(*) as tiene_permiso
                FROM empleados e
                JOIN roles_permisos rp ON e.id_rol = rp.id_rol
                JOIN permisos p ON rp.id_permiso = p.id_permiso
                WHERE e.id_empleado = %s 
                AND p.modulo = %s 
                AND p.accion = %s
                AND e.estado = true
            """
            
            resultado = self.db.execute_query(
                query,
                (self.sesion_actual['id_empleado'], modulo, accion)
            )
            
            return resultado[0]['tiene_permiso'] > 0
            
        except Exception as e:
            print(f"❌ Error verificando permiso: {e}")
            return False

    def obtener_permisos_usuario(self) -> List[Dict]:
        """
        Obtiene todos los permisos del usuario actual
        
        Returns:
            Lista de permisos: [{'modulo': 'clientes', 'accion': 'crear'}, ...]
        """
        if not self.sesion_actual:
            return []
        
        try:
            query = """
                SELECT DISTINCT
                    p.modulo,
                    p.accion,
                    p.descripcion
                FROM empleados e
                JOIN roles_permisos rp ON e.id_rol = rp.id_rol
                JOIN permisos p ON rp.id_permiso = p.id_permiso
                WHERE e.id_empleado = %s 
                AND e.estado = true
                ORDER BY p.modulo, p.accion
            """
            
            return self.db.execute_query(query, (self.sesion_actual['id_empleado'],))
            
        except Exception as e:
            print(f"❌ Error obteniendo permisos: {e}")
            return []

    def es_admin(self) -> bool:
        """Verifica si el usuario actual es administrador"""
        if not self.sesion_actual:
            return False
        return self.sesion_actual['nombre_rol'].lower() == 'administrador'

    def get_usuario_actual(self) -> Optional[Dict]:
        """Retorna los datos del usuario actual"""
        return self.sesion_actual

    def cambiar_password(self, id_empleado: int, password_actual: str, password_nuevo: str) -> Dict:
        """
        Cambia la contraseña de un empleado
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Verificar contraseña actual
            password_actual_hash = self.hash_password(password_actual)
            
            query = "SELECT id_empleado FROM empleados WHERE id_empleado = %s AND password = %s"
            resultado = self.db.execute_query(query, (id_empleado, password_actual_hash))
            
            if not resultado:
                return {
                    'success': False,
                    'message': 'Contraseña actual incorrecta'
                }
            
            # Cambiar contraseña
            password_nuevo_hash = self.hash_password(password_nuevo)
            
            self.db.execute_query(
                "UPDATE empleados SET password = %s, updated_at = %s WHERE id_empleado = %s",
                (password_nuevo_hash, datetime.now(), id_empleado),
                fetch=False
            )
            
            # Registrar en logs
            self._registrar_log(id_empleado, 'cambio_password', 'empleados', id_empleado, 'Cambio de contraseña')
            
            return {
                'success': True,
                'message': 'Contraseña actualizada exitosamente'
            }
            
        except Exception as e:
            print(f"❌ Error cambiando contraseña: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    def _registrar_log(self, id_empleado: int, accion: str, tabla_afectada: Optional[str],
                       id_registro: Optional[int], descripcion: str):
        """Registra una acción en la tabla de logs"""
        try:
            query = """
                INSERT INTO logs_sistema (id_empleado, accion, tabla_afectada, id_registro, descripcion)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(
                query,
                (id_empleado, accion, tabla_afectada, id_registro, descripcion),
                fetch=False
            )
        except Exception as e:
            print(f"⚠️ Error registrando log: {e}")
