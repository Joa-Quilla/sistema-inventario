"""
Repositorio para Empleados
"""
from typing import List, Dict, Optional, Any
from database.connection import DatabaseConnection
from models.empleado import Empleado
from models.persona import Persona
import hashlib


class EmpleadoRepository:
    """Repositorio para gestión de empleados"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def crear(self, empleado: Empleado, password: str) -> Dict[str, Any]:
        """
        Crea un nuevo empleado con su persona asociada
        
        Args:
            empleado: Instancia de Empleado con datos de persona
            password: Contraseña en texto plano
            
        Returns:
            Dict con 'success', 'message', 'id_empleado'
        """
        try:
            # Paso 1: Validar datos
            es_valido, mensaje = empleado.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            # Paso 2: Verificar que el usuario no exista
            query_usuario = "SELECT COUNT(*) as count FROM empleados WHERE usuario = %s"
            result = self.db.execute_query(query_usuario, (empleado.usuario,), fetch='one')
            if result and result['count'] > 0:
                return {'success': False, 'message': 'El usuario ya existe'}
            
            # Paso 3: Verificar que el documento no exista
            if empleado.persona and empleado.persona.dpi_nit:
                query_doc = """
                    SELECT COUNT(*) as count FROM personas 
                    WHERE dpi_nit = %s
                """
                result = self.db.execute_query(
                    query_doc, 
                    (empleado.persona.dpi_nit,),
                    fetch='one'
                )
                if result and result['count'] > 0:
                    return {'success': False, 'message': f'El DPI/NIT {empleado.persona.dpi_nit} ya está registrado'}
            
            # Verificar que el email no exista (si se proporciona)
            if empleado.persona and empleado.persona.email:
                query_email = """
                    SELECT COUNT(*) as count FROM personas 
                    WHERE email = %s
                """
                result = self.db.execute_query(
                    query_email, 
                    (empleado.persona.email,),
                    fetch='one'
                )
                if result and result['count'] > 0:
                    return {'success': False, 'message': f'El correo {empleado.persona.email} ya está registrado'}
            
            # Paso 4: Crear persona
            query_persona = """
                INSERT INTO personas 
                    (nombre, apellido, telefono, email, direccion, dpi_nit, estado)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_persona
            """
            persona = empleado.persona
            result_persona = self.db.execute_query(
                query_persona,
                (persona.nombre, persona.apellido, persona.telefono, 
                 persona.email, persona.direccion, persona.dpi_nit, persona.estado),
                fetch='one'
            )
            
            if not result_persona:
                return {'success': False, 'message': 'Error al crear persona'}
            
            id_persona = result_persona['id_persona']
            
            # Paso 5: Hash de contraseña usando SHA-256
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Paso 6: Crear empleado
            query_empleado = """
                INSERT INTO empleados 
                    (id_persona, id_rol, usuario, password, 
                     fecha_contratacion, salario, puesto, estado)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_empleado
            """
            result_empleado = self.db.execute_query(
                query_empleado,
                (id_persona, empleado.id_rol, empleado.usuario,
                 password_hash, empleado.fecha_contratacion, empleado.salario,
                 empleado.puesto, True),
                fetch='one'
            )
            
            if result_empleado:
                return {
                    'success': True,
                    'message': 'Empleado creado exitosamente',
                    'id_empleado': result_empleado['id_empleado']
                }
            else:
                return {'success': False, 'message': 'Error al crear empleado'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def listar(self, pagina: int = 1, limite: int = 10, busqueda: str = "", 
               filtro_estado: str = "", filtro_rol: int = None) -> Dict[str, Any]:
        """
        Lista empleados con paginación y filtros
        
        Args:
            pagina: Número de página
            limite: Registros por página
            busqueda: Término de búsqueda
            filtro_estado: Filtrar por estado
            filtro_rol: Filtrar por rol
            
        Returns:
            Dict con 'empleados' (list) y 'total' (int)
        """
        try:
            offset = (pagina - 1) * limite
            
            # Construir condiciones WHERE
            condiciones = []
            params = []
            
            if busqueda:
                condiciones.append("""
                    (p.nombre ILIKE %s OR p.apellido ILIKE %s OR 
                     e.usuario ILIKE %s OR p.dpi_nit ILIKE %s)
                """)
                busqueda_param = f'%{busqueda}%'
                params.extend([busqueda_param] * 4)
            
            if filtro_estado:
                # Convertir string a boolean
                estado_bool = True if filtro_estado == "activo" else False if filtro_estado == "inactivo" else None
                if estado_bool is not None:
                    condiciones.append("e.estado = %s")
                    params.append(estado_bool)
            
            if filtro_rol:
                condiciones.append("e.id_rol = %s")
                params.append(filtro_rol)
            
            where_clause = " AND " + " AND ".join(condiciones) if condiciones else ""
            
            # Query para contar total
            query_count = f"""
                SELECT COUNT(*) as total
                FROM empleados e
                INNER JOIN personas p ON e.id_persona = p.id_persona
                LEFT JOIN roles r ON e.id_rol = r.id_rol
                WHERE 1=1 {where_clause}
            """
            result_count = self.db.execute_query(query_count, tuple(params), fetch='one')
            total = result_count['total'] if result_count else 0
            
            # Query para obtener registros
            query = f"""
                SELECT 
                    e.id_empleado, e.id_persona, e.id_rol,
                    e.usuario, e.fecha_contratacion, e.salario, e.puesto, e.estado,
                    p.nombre, p.apellido, p.dpi_nit,
                    p.telefono, p.email, p.direccion, p.estado as estado_persona,
                    r.nombre as nombre_rol
                FROM empleados e
                INNER JOIN personas p ON e.id_persona = p.id_persona
                LEFT JOIN roles r ON e.id_rol = r.id_rol
                WHERE 1=1 {where_clause}
                ORDER BY e.fecha_contratacion DESC, p.apellido, p.nombre
                LIMIT %s OFFSET %s
            """
            params.extend([limite, offset])
            
            results = self.db.execute_query(query, tuple(params), fetch='all')
            empleados = [Empleado.from_dict(row) for row in results] if results else []
            
            return {'empleados': empleados, 'total': total}
            
        except Exception as e:
            print(f"Error al listar empleados: {e}")
            return {'empleados': [], 'total': 0}
    
    def obtener_por_id(self, id_empleado: int) -> Optional[Empleado]:
        """
        Obtiene un empleado por su ID
        
        Args:
            id_empleado: ID del empleado
            
        Returns:
            Instancia de Empleado o None
        """
        try:
            query = """
                SELECT 
                    e.id_empleado, e.id_persona, e.id_rol,
                    e.usuario, e.fecha_contratacion, e.salario, e.puesto, e.estado,
                    p.nombre, p.apellido, p.dpi_nit,
                    p.telefono, p.email, p.direccion, p.estado as estado_persona,
                    r.nombre as nombre_rol
                FROM empleados e
                INNER JOIN personas p ON e.id_persona = p.id_persona
                LEFT JOIN roles r ON e.id_rol = r.id_rol
                WHERE e.id_empleado = %s
            """
            result = self.db.execute_query(query, (id_empleado,), fetch='one')
            
            if result:
                return Empleado.from_dict(result)
            return None
            
        except Exception as e:
            print(f"Error al obtener empleado: {e}")
            return None
    
    def actualizar(self, empleado: Empleado) -> Dict[str, Any]:
        """
        Actualiza un empleado existente
        
        Args:
            empleado: Instancia de Empleado con datos actualizados
            
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            # Validar datos
            es_valido, mensaje = empleado.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            # Verificar que el usuario no esté duplicado (excepto el mismo empleado)
            query_usuario = """
                SELECT COUNT(*) as count FROM empleados 
                WHERE usuario = %s AND id_empleado != %s
            """
            result = self.db.execute_query(
                query_usuario, 
                (empleado.usuario, empleado.id_empleado),
                fetch='one'
            )
            if result and result['count'] > 0:
                return {'success': False, 'message': 'El usuario ya existe'}
            
            # Actualizar persona
            query_persona = """
                UPDATE personas SET
                    nombre = %s,
                    apellido = %s,
                    dpi_nit = %s,
                    telefono = %s,
                    email = %s,
                    direccion = %s,
                    estado = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_persona = %s
            """
            persona = empleado.persona
            self.db.execute_query(
                query_persona,
                (persona.nombre, persona.apellido, persona.dpi_nit,
                 persona.telefono, persona.email, persona.direccion,
                 persona.estado, empleado.id_persona),
                fetch=False
            )
            
            # Actualizar empleado
            query_empleado = """
                UPDATE empleados SET
                    id_rol = %s,
                    usuario = %s,
                    fecha_contratacion = %s,
                    salario = %s,
                    puesto = %s,
                    estado = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_empleado = %s
            """
            self.db.execute_query(
                query_empleado,
                (empleado.id_rol, empleado.usuario, empleado.fecha_contratacion,
                 empleado.salario, empleado.puesto, empleado.estado,
                 empleado.id_empleado),
                fetch=False
            )
            
            return {'success': True, 'message': 'Empleado actualizado exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cambiar_password(self, id_empleado: int, nueva_password: str) -> Dict[str, Any]:
        """
        Cambia la contraseña de un empleado
        
        Args:
            id_empleado: ID del empleado
            nueva_password: Nueva contraseña en texto plano
            
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            password_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
            
            query = """
                UPDATE empleados SET
                    password = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_empleado = %s
            """
            self.db.execute_query(query, (password_hash, id_empleado), fetch=False)
            
            return {'success': True, 'message': 'Contraseña actualizada exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cambiar_estado(self, id_empleado: int, nuevo_estado: bool) -> Dict[str, Any]:
        """
        Cambia el estado de un empleado
        
        Args:
            id_empleado: ID del empleado
            nuevo_estado: Nuevo estado (True=activo, False=inactivo)
            
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            # Si se intenta desactivar, verificar que no sea el único administrador activo
            if not nuevo_estado:
                # Obtener el rol del empleado
                query_rol = """
                    SELECT r.nombre as nombre_rol
                    FROM empleados e
                    INNER JOIN roles r ON e.id_rol = r.id_rol
                    WHERE e.id_empleado = %s
                """
                result_rol = self.db.execute_query(query_rol, (id_empleado,), fetch='one')
                
                # Si es administrador, verificar que no sea el único activo
                if result_rol and result_rol['nombre_rol'] == 'Administrador':
                    query_check = """
                        SELECT COUNT(*) as count FROM empleados e
                        INNER JOIN roles r ON e.id_rol = r.id_rol
                        WHERE r.nombre = 'Administrador' AND e.estado = true
                    """
                    result = self.db.execute_query(query_check, fetch='one')
                    
                    if result and result['count'] <= 1:
                        return {'success': False, 'message': 'No se puede desactivar el único administrador activo'}
            
            query = """
                UPDATE empleados SET
                    estado = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_empleado = %s
            """
            self.db.execute_query(query, (nuevo_estado, id_empleado), fetch=False)
            
            estado_texto = "activo" if nuevo_estado else "inactivo"
            return {'success': True, 'message': f'Estado cambiado a {estado_texto}'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def eliminar(self, id_empleado: int) -> Dict[str, Any]:
        """
        Elimina un empleado (soft delete - cambia estado a inactivo)
        
        Args:
            id_empleado: ID del empleado
            
        Returns:
            Dict con 'success' y 'message'
        """
        try:
            # Verificar que no sea el único administrador activo
            query_check = """
                SELECT COUNT(*) as count FROM empleados e
                INNER JOIN roles r ON e.id_rol = r.id_rol
                WHERE r.nombre = 'Administrador' AND e.estado = true
            """
            result = self.db.execute_query(query_check, fetch='one')
            
            if result and result['count'] <= 1:
                # Verificar si el empleado a eliminar es administrador
                query_es_admin = """
                    SELECT r.nombre FROM empleados e
                    INNER JOIN roles r ON e.id_rol = r.id_rol
                    WHERE e.id_empleado = %s
                """
                result_admin = self.db.execute_query(query_es_admin, (id_empleado,), fetch='one')
                
                if result_admin and result_admin['nombre'] == 'Administrador':
                    return {'success': False, 'message': 'No se puede eliminar el único administrador activo'}
            
            # Soft delete - cambiar estado a inactivo
            return self.cambiar_estado(id_empleado, False)
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def obtener_roles(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de roles disponibles
        
        Returns:
            Lista de diccionarios con id_rol y nombre
        """
        try:
            query = "SELECT id_rol, nombre, descripcion FROM roles ORDER BY nombre"
            results = self.db.execute_query(query, fetch='all')
            return results if results else []
        except Exception as e:
            print(f"Error al obtener roles: {e}")
            return []
    
    def obtener_roles(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de roles disponibles
        
        Returns:
            Lista de diccionarios con id_rol y nombre
        """
        try:
            query = "SELECT id_rol, nombre, descripcion FROM roles ORDER BY nombre"
            results = self.db.execute_query(query, fetch='all')
            return results if results else []
        except Exception as e:
            print(f"Error al obtener roles: {e}")
            return []
