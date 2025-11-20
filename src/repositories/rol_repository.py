"""
Repositorio para operaciones de base de datos de Roles
"""
from typing import Dict, Any, List, Optional
from database.connection import DatabaseConnection


class RolRepository:
    """Repositorio para gestión de roles"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def crear(self, nombre: str, descripcion: str = None) -> Dict[str, Any]:
        """
        Crea un nuevo rol
        
        Args:
            nombre: Nombre del rol
            descripcion: Descripción del rol
            
        Returns:
            Dict con 'success', 'message', 'id_rol'
        """
        try:
            # Verificar que el nombre no exista
            query_check = "SELECT COUNT(*) as count FROM roles WHERE nombre = %s"
            result = self.db.execute_query(query_check, (nombre,), fetch='one')
            if result and result['count'] > 0:
                return {'success': False, 'message': f'El rol "{nombre}" ya existe'}
            
            # Crear rol
            query = """
                INSERT INTO roles (nombre, descripcion)
                VALUES (%s, %s)
                RETURNING id_rol
            """
            result = self.db.execute_query(query, (nombre, descripcion), fetch='one')
            
            if result:
                return {
                    'success': True,
                    'message': 'Rol creado exitosamente',
                    'id_rol': result['id_rol']
                }
            else:
                return {'success': False, 'message': 'Error al crear rol'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def listar(self) -> List[Dict[str, Any]]:
        """
        Lista todos los roles con conteo de empleados
        
        Returns:
            Lista de roles
        """
        try:
            query = """
                SELECT 
                    r.id_rol,
                    r.nombre,
                    r.descripcion,
                    COUNT(e.id_empleado) as total_empleados
                FROM roles r
                LEFT JOIN empleados e ON r.id_rol = e.id_rol
                GROUP BY r.id_rol, r.nombre, r.descripcion
                ORDER BY r.nombre
            """
            return self.db.execute_query(query, fetch='all') or []
            
        except Exception as e:
            print(f"Error al listar roles: {str(e)}")
            return []
    
    def obtener_por_id(self, id_rol: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un rol por su ID
        
        Args:
            id_rol: ID del rol
            
        Returns:
            Diccionario con datos del rol o None
        """
        try:
            query = """
                SELECT 
                    r.id_rol,
                    r.nombre,
                    r.descripcion,
                    COUNT(e.id_empleado) as total_empleados
                FROM roles r
                LEFT JOIN empleados e ON r.id_rol = e.id_rol
                WHERE r.id_rol = %s
                GROUP BY r.id_rol, r.nombre, r.descripcion
            """
            return self.db.execute_query(query, (id_rol,), fetch='one')
            
        except Exception as e:
            print(f"Error al obtener rol: {str(e)}")
            return None
    
    def actualizar(self, id_rol: int, nombre: str, descripcion: str = None) -> Dict[str, Any]:
        """
        Actualiza un rol existente
        
        Args:
            id_rol: ID del rol
            nombre: Nuevo nombre
            descripcion: Nueva descripción
            
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            # Verificar que el nombre no esté duplicado (excepto el mismo rol)
            query_check = """
                SELECT COUNT(*) as count FROM roles 
                WHERE nombre = %s AND id_rol != %s
            """
            result = self.db.execute_query(query_check, (nombre, id_rol), fetch='one')
            if result and result['count'] > 0:
                return {'success': False, 'message': f'El rol "{nombre}" ya existe'}
            
            # Actualizar rol
            query = """
                UPDATE roles SET
                    nombre = %s,
                    descripcion = %s
                WHERE id_rol = %s
            """
            self.db.execute_query(query, (nombre, descripcion, id_rol), fetch=False)
            
            return {'success': True, 'message': 'Rol actualizado exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def eliminar(self, id_rol: int) -> Dict[str, Any]:
        """
        Elimina un rol (si no tiene empleados asignados)
        
        Args:
            id_rol: ID del rol
            
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            # Verificar que no sea el rol Administrador
            query_check_admin = "SELECT nombre FROM roles WHERE id_rol = %s"
            result_admin = self.db.execute_query(query_check_admin, (id_rol,), fetch='one')
            if result_admin and result_admin['nombre'] == 'Administrador':
                return {'success': False, 'message': 'No se puede eliminar el rol Administrador'}
            
            # Verificar que no tenga empleados asignados
            query_check = "SELECT COUNT(*) as count FROM empleados WHERE id_rol = %s"
            result = self.db.execute_query(query_check, (id_rol,), fetch='one')
            if result and result['count'] > 0:
                return {
                    'success': False, 
                    'message': f'No se puede eliminar el rol porque tiene {result["count"]} empleado(s) asignado(s)'
                }
            
            # Eliminar permisos asociados
            query_permisos = "DELETE FROM roles_permisos WHERE id_rol = %s"
            self.db.execute_query(query_permisos, (id_rol,), fetch=False)
            
            # Eliminar rol
            query = "DELETE FROM roles WHERE id_rol = %s"
            self.db.execute_query(query, (id_rol,), fetch=False)
            
            return {'success': True, 'message': 'Rol eliminado exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def obtener_permisos_rol(self, id_rol: int) -> List[int]:
        """
        Obtiene los IDs de permisos asignados a un rol
        
        Args:
            id_rol: ID del rol
            
        Returns:
            Lista de IDs de permisos
        """
        try:
            query = """
                SELECT id_permiso 
                FROM roles_permisos 
                WHERE id_rol = %s
            """
            results = self.db.execute_query(query, (id_rol,), fetch='all')
            return [r['id_permiso'] for r in results] if results else []
            
        except Exception as e:
            print(f"Error al obtener permisos del rol: {str(e)}")
            return []
    
    def asignar_permisos(self, id_rol: int, permisos: List[int]) -> Dict[str, Any]:
        """
        Asigna permisos a un rol (reemplaza los existentes)
        
        Args:
            id_rol: ID del rol
            permisos: Lista de IDs de permisos
            
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            # Eliminar permisos actuales
            query_delete = "DELETE FROM roles_permisos WHERE id_rol = %s"
            self.db.execute_query(query_delete, (id_rol,), fetch=False)
            
            # Asignar nuevos permisos
            if permisos:
                query_insert = """
                    INSERT INTO roles_permisos (id_rol, id_permiso)
                    VALUES (%s, %s)
                """
                for id_permiso in permisos:
                    self.db.execute_query(query_insert, (id_rol, id_permiso), fetch=False)
            
            return {'success': True, 'message': 'Permisos asignados exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
