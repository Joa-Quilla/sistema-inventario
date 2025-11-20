"""
Repositorio para operaciones de base de datos de Permisos
"""
from typing import Dict, Any, List
from database.connection import DatabaseConnection


class PermisoRepository:
    """Repositorio para gestión de permisos"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def listar_todos(self) -> List[Dict[str, Any]]:
        """
        Lista todos los permisos
        
        Returns:
            Lista de permisos
        """
        try:
            query = """
                SELECT 
                    id_permiso,
                    modulo,
                    accion,
                    descripcion
                FROM permisos
                ORDER BY modulo, accion
            """
            return self.db.execute_query(query, fetch='all') or []
            
        except Exception as e:
            print(f"Error al listar permisos: {str(e)}")
            return []
    
    def listar_por_modulo(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Lista permisos agrupados por módulo
        
        Returns:
            Dict con módulos como keys y listas de permisos como values
        """
        try:
            permisos = self.listar_todos()
            agrupados = {}
            
            for permiso in permisos:
                modulo = permiso['modulo']
                if modulo not in agrupados:
                    agrupados[modulo] = []
                agrupados[modulo].append(permiso)
            
            return agrupados
            
        except Exception as e:
            print(f"Error al agrupar permisos: {str(e)}")
            return {}
    
    def crear_permisos_base(self) -> Dict[str, Any]:
        """
        Crea los permisos base del sistema si no existen
        
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            modulos = [
                'productos', 'clientes', 'proveedores', 'compras', 
                'ventas', 'cajas', 'empleados', 'reportes', 'roles'
            ]
            acciones = ['leer', 'crear', 'actualizar', 'eliminar']
            
            descripciones = {
                'leer': 'Ver y consultar información',
                'crear': 'Crear nuevos registros',
                'actualizar': 'Editar registros existentes',
                'eliminar': 'Eliminar o desactivar registros'
            }
            
            count = 0
            for modulo in modulos:
                for accion in acciones:
                    # Verificar si ya existe
                    query_check = """
                        SELECT COUNT(*) as count 
                        FROM permisos 
                        WHERE modulo = %s AND accion = %s
                    """
                    result = self.db.execute_query(query_check, (modulo, accion), fetch='one')
                    
                    if result and result['count'] == 0:
                        # Crear permiso
                        query_insert = """
                            INSERT INTO permisos (modulo, accion, descripcion)
                            VALUES (%s, %s, %s)
                        """
                        descripcion = f"{descripciones[accion]} de {modulo}"
                        self.db.execute_query(
                            query_insert, 
                            (modulo, accion, descripcion), 
                            fetch=False
                        )
                        count += 1
            
            if count > 0:
                return {
                    'success': True, 
                    'message': f'Se crearon {count} permisos base'
                }
            else:
                return {
                    'success': True, 
                    'message': 'Los permisos base ya existen'
                }
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def asignar_todos_permisos_admin(self) -> Dict[str, Any]:
        """
        Asigna todos los permisos al rol Administrador
        
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            # Obtener ID del rol Administrador
            query_rol = "SELECT id_rol FROM roles WHERE nombre = 'Administrador'"
            result_rol = self.db.execute_query(query_rol, fetch='one')
            
            if not result_rol:
                return {'success': False, 'message': 'Rol Administrador no encontrado'}
            
            id_rol = result_rol['id_rol']
            
            # Obtener todos los permisos
            query_permisos = "SELECT id_permiso FROM permisos"
            permisos = self.db.execute_query(query_permisos, fetch='all')
            
            if not permisos:
                return {'success': False, 'message': 'No hay permisos para asignar'}
            
            # Eliminar permisos actuales
            query_delete = "DELETE FROM roles_permisos WHERE id_rol = %s"
            self.db.execute_query(query_delete, (id_rol,), fetch=False)
            
            # Asignar todos los permisos
            query_insert = """
                INSERT INTO roles_permisos (id_rol, id_permiso)
                VALUES (%s, %s)
                ON CONFLICT (id_rol, id_permiso) DO NOTHING
            """
            for permiso in permisos:
                self.db.execute_query(
                    query_insert, 
                    (id_rol, permiso['id_permiso']), 
                    fetch=False
                )
            
            return {
                'success': True, 
                'message': f'Se asignaron {len(permisos)} permisos al Administrador'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
