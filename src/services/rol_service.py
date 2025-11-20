"""
Servicio para lógica de negocio de Roles
"""
from typing import Dict, Any, List, Optional
from repositories.rol_repository import RolRepository
from repositories.permiso_repository import PermisoRepository


class RolService:
    """Servicio para gestión de roles y permisos"""
    
    def __init__(self):
        self.rol_repository = RolRepository()
        self.permiso_repository = PermisoRepository()
    
    def crear_rol(self, nombre: str, descripcion: str = None) -> Dict[str, Any]:
        """
        Crea un nuevo rol
        
        Args:
            nombre: Nombre del rol
            descripcion: Descripción del rol
            
        Returns:
            Dict con 'success', 'message', 'id_rol'
        """
        # Validar nombre
        if not nombre or not nombre.strip():
            return {'success': False, 'message': 'El nombre del rol es obligatorio'}
        
        if len(nombre.strip()) < 3:
            return {'success': False, 'message': 'El nombre debe tener al menos 3 caracteres'}
        
        return self.rol_repository.crear(nombre.strip(), descripcion)
    
    def listar_roles(self) -> List[Dict[str, Any]]:
        """
        Lista todos los roles
        
        Returns:
            Lista de roles
        """
        return self.rol_repository.listar()
    
    def obtener_rol(self, id_rol: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un rol por su ID
        
        Args:
            id_rol: ID del rol
            
        Returns:
            Diccionario con datos del rol o None
        """
        return self.rol_repository.obtener_por_id(id_rol)
    
    def actualizar_rol(self, id_rol: int, nombre: str, descripcion: str = None) -> Dict[str, Any]:
        """
        Actualiza un rol existente
        
        Args:
            id_rol: ID del rol
            nombre: Nuevo nombre
            descripcion: Nueva descripción
            
        Returns:
            Dict con 'success' y 'message'
        """
        # Validar nombre
        if not nombre or not nombre.strip():
            return {'success': False, 'message': 'El nombre del rol es obligatorio'}
        
        if len(nombre.strip()) < 3:
            return {'success': False, 'message': 'El nombre debe tener al menos 3 caracteres'}
        
        # No permitir cambiar el nombre del rol Administrador
        rol_actual = self.rol_repository.obtener_por_id(id_rol)
        if rol_actual and rol_actual['nombre'] == 'Administrador' and nombre.strip() != 'Administrador':
            return {'success': False, 'message': 'No se puede cambiar el nombre del rol Administrador'}
        
        return self.rol_repository.actualizar(id_rol, nombre.strip(), descripcion)
    
    def eliminar_rol(self, id_rol: int) -> Dict[str, Any]:
        """
        Elimina un rol
        
        Args:
            id_rol: ID del rol
            
        Returns:
            Dict con 'success' y 'message'
        """
        return self.rol_repository.eliminar(id_rol)
    
    def obtener_permisos_rol(self, id_rol: int) -> List[int]:
        """
        Obtiene los IDs de permisos asignados a un rol
        
        Args:
            id_rol: ID del rol
            
        Returns:
            Lista de IDs de permisos
        """
        return self.rol_repository.obtener_permisos_rol(id_rol)
    
    def asignar_permisos(self, id_rol: int, permisos: List[int]) -> Dict[str, Any]:
        """
        Asigna permisos a un rol
        
        Args:
            id_rol: ID del rol
            permisos: Lista de IDs de permisos
            
        Returns:
            Dict con 'success' y 'message'
        """
        return self.rol_repository.asignar_permisos(id_rol, permisos)
    
    def listar_permisos(self) -> List[Dict[str, Any]]:
        """
        Lista todos los permisos disponibles
        
        Returns:
            Lista de permisos
        """
        return self.permiso_repository.listar_todos()
    
    def listar_permisos_por_modulo(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Lista permisos agrupados por módulo
        
        Returns:
            Dict con módulos como keys y listas de permisos como values
        """
        return self.permiso_repository.listar_por_modulo()
    
    def inicializar_permisos(self) -> Dict[str, Any]:
        """
        Inicializa los permisos base del sistema
        
        Returns:
            Dict con 'success' y 'message'
        """
        # Crear permisos base
        resultado = self.permiso_repository.crear_permisos_base()
        
        if resultado['success']:
            # Asignar todos los permisos al Administrador
            resultado_admin = self.permiso_repository.asignar_todos_permisos_admin()
            if not resultado_admin['success']:
                return resultado_admin
        
        return resultado
