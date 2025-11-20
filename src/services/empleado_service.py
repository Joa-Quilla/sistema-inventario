"""
Servicio para lógica de negocio de Empleados
"""
from typing import Dict, Any, List, Optional
from repositories.empleado_repository import EmpleadoRepository
from models.empleado import Empleado
from models.persona import Persona
import re


class EmpleadoService:
    """Servicio para gestión de empleados"""
    
    def __init__(self):
        self.repository = EmpleadoRepository()
    
    def crear_empleado(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo empleado
        
        Args:
            datos: Diccionario con datos del empleado y persona
            
        Returns:
            Dict con 'success', 'message', 'id_empleado'
        """
        try:
            # Validar password
            password = datos.get('password', '')
            if not password or len(password) < 6:
                return {'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}
            
            # Validar email si existe
            email = datos.get('email', '')
            if email and not self._validar_email(email):
                return {'success': False, 'message': 'Email inválido'}
            
            # Crear instancia de Persona
            persona = Persona(
                nombre=datos.get('nombres', '').strip(),
                apellido=datos.get('apellidos', '').strip(),
                dpi_nit=datos.get('numero_documento', '').strip(),
                telefono=datos.get('telefono', '').strip(),
                email=email.strip() if email else None,
                direccion=datos.get('direccion', '').strip(),
                estado=True
            )
            
            # Crear instancia de Empleado
            empleado = Empleado(
                persona=persona,
                id_rol=datos.get('id_rol'),
                usuario=datos.get('usuario', '').strip(),
                fecha_contratacion=datos.get('fecha_contratacion'),
                salario=float(datos.get('salario', 0)),
                puesto=datos.get('puesto', '').strip() if datos.get('puesto') else None,
                estado=True
            )
            
            # Crear en repositorio
            return self.repository.crear(empleado, password)
            
        except Exception as e:
            return {'success': False, 'message': f'Error al crear empleado: {str(e)}'}
    
    def listar_empleados(self, pagina: int = 1, limite: int = 10, 
                        busqueda: str = "", filtro_estado: str = "",
                        filtro_rol: int = None) -> Dict[str, Any]:
        """
        Lista empleados con paginación y filtros
        
        Args:
            pagina: Número de página
            limite: Registros por página
            busqueda: Término de búsqueda
            filtro_estado: Filtrar por estado
            filtro_rol: Filtrar por rol
            
        Returns:
            Dict con 'empleados' (list), 'total' (int), 'paginas' (int)
        """
        resultado = self.repository.listar(pagina, limite, busqueda, filtro_estado, filtro_rol)
        
        # Calcular número de páginas
        total = resultado.get('total', 0)
        paginas = (total + limite - 1) // limite if total > 0 else 1
        
        return {
            'empleados': resultado.get('empleados', []),
            'total': total,
            'paginas': paginas
        }
    
    def obtener_empleado(self, id_empleado: int) -> Optional[Empleado]:
        """
        Obtiene un empleado por su ID
        
        Args:
            id_empleado: ID del empleado
            
        Returns:
            Instancia de Empleado o None
        """
        return self.repository.obtener_por_id(id_empleado)
    
    def actualizar_empleado(self, id_empleado: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un empleado existente
        
        Args:
            id_empleado: ID del empleado
            datos: Diccionario con datos actualizados
            
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            # Obtener empleado actual
            empleado = self.repository.obtener_por_id(id_empleado)
            if not empleado:
                return {'success': False, 'message': 'Empleado no encontrado'}
            
            # Validar email si existe
            email = datos.get('email', '')
            if email and not self._validar_email(email):
                return {'success': False, 'message': 'Email inválido'}
            
            # Actualizar datos de persona
            empleado.persona.nombre = datos.get('nombres', '').strip()
            empleado.persona.apellido = datos.get('apellidos', '').strip()
            empleado.persona.dpi_nit = datos.get('numero_documento', '').strip()
            empleado.persona.telefono = datos.get('telefono', '').strip()
            empleado.persona.email = email.strip() if email else None
            empleado.persona.direccion = datos.get('direccion', '').strip()
            
            # Actualizar datos de empleado
            empleado.id_rol = datos.get('id_rol')
            empleado.usuario = datos.get('usuario', '').strip()
            empleado.fecha_contratacion = datos.get('fecha_contratacion')
            empleado.salario = float(datos.get('salario', 0))
            empleado.puesto = datos.get('puesto', '').strip() if datos.get('puesto') else None
            empleado.estado = bool(datos.get('estado', True))
            
            # Actualizar en repositorio
            return self.repository.actualizar(empleado)
            
        except Exception as e:
            return {'success': False, 'message': f'Error al actualizar empleado: {str(e)}'}
    
    def cambiar_password(self, id_empleado: int, nueva_password: str) -> Dict[str, Any]:
        """
        Cambia la contraseña de un empleado
        
        Args:
            id_empleado: ID del empleado
            nueva_password: Nueva contraseña
            
        Returns:
            Dict con 'success' y 'message'
        """
        if not nueva_password or len(nueva_password) < 6:
            return {'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}
        
        return self.repository.cambiar_password(id_empleado, nueva_password)
    
    def cambiar_estado(self, id_empleado: int, nuevo_estado: bool) -> Dict[str, Any]:
        """
        Cambia el estado de un empleado
        
        Args:
            id_empleado: ID del empleado
            nuevo_estado: Nuevo estado (True=activo, False=inactivo)
            
        Returns:
            Dict con 'success' y 'message'
        """
        return self.repository.cambiar_estado(id_empleado, nuevo_estado)
    
    def eliminar_empleado(self, id_empleado: int) -> Dict[str, Any]:
        """
        Elimina un empleado (soft delete)
        
        Args:
            id_empleado: ID del empleado
            
        Returns:
            Dict con 'success' y 'message'
        """
        return self.repository.eliminar(id_empleado)
    
    def obtener_roles(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de roles disponibles
        
        Returns:
            Lista de diccionarios con id_rol y nombre
        """
        return self.repository.obtener_roles()
    
    def _validar_email(self, email: str) -> bool:
        """
        Valida formato de email
        
        Args:
            email: Email a validar
            
        Returns:
            True si es válido, False si no
        """
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(patron, email))
