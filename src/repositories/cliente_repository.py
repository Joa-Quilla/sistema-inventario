"""
Repositorio para operaciones CRUD de Clientes
"""
from typing import List, Optional, Dict, Any
from database.connection import DatabaseConnection
from models.cliente import Cliente
from models.persona import Persona


class ClienteRepository:
    """Repositorio para gestión de clientes"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def crear(self, cliente: Cliente) -> Dict[str, Any]:
        """
        Crea un nuevo cliente (con persona)
        
        Args:
            cliente: Objeto Cliente a crear
            
        Returns:
            Dict con 'success' (bool), 'message' (str), 'id_cliente' (int si success=True)
        """
        try:
            # Validar
            es_valido, mensaje = cliente.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            # Primero crear la persona
            query_persona = """
                INSERT INTO personas 
                    (nombre, apellido, telefono, email, direccion, dpi_nit, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_persona, created_at
            """
            
            persona_result = self.db.execute_query(
                query_persona,
                (cliente.persona.nombre, cliente.persona.apellido,
                 cliente.persona.telefono, cliente.persona.email, 
                 cliente.persona.direccion, cliente.persona.dpi_nit,
                 cliente.persona.estado),
                fetch='one'
            )
            
            if not persona_result:
                return {'success': False, 'message': 'Error al crear los datos de persona'}
            
            id_persona = persona_result['id_persona']
            
            # Luego crear el cliente
            query_cliente = """
                INSERT INTO clientes 
                    (id_persona, tipo_cliente, limite_credito, descuento_habitual, estado)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_cliente, created_at
            """
            
            cliente_result = self.db.execute_query(
                query_cliente,
                (id_persona, cliente.tipo_cliente, cliente.limite_credito, 
                 cliente.descuento_habitual, cliente.estado),
                fetch='one'
            )
            
            if cliente_result:
                return {
                    'success': True,
                    'message': 'Cliente creado exitosamente',
                    'id_cliente': cliente_result['id_cliente'],
                    'id_persona': id_persona
                }
            else:
                return {'success': False, 'message': 'Error al crear el cliente'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def obtener_por_id(self, id_cliente: int) -> Optional[Cliente]:
        """Obtiene un cliente por su ID con datos de persona"""
        query = """
            SELECT 
                c.id_cliente,
                c.id_persona,
                c.tipo_cliente,
                c.limite_credito,
                c.descuento_habitual,
                c.fecha_primera_compra,
                c.total_compras,
                c.estado,
                c.created_at,
                c.updated_at,
                p.nombre,
                p.apellido,
                p.telefono,
                p.email,
                p.direccion,
                p.dpi_nit,
                p.fecha_registro,
                p.estado as persona_estado
            FROM clientes c
            INNER JOIN personas p ON c.id_persona = p.id_persona
            WHERE c.id_cliente = %s
        """
        
        result = self.db.execute_query(query, (id_cliente,), fetch='one')
        
        if result:
            return Cliente.from_dict(result)
        return None
    
    def obtener_por_nit(self, nit: str) -> Optional[Cliente]:
        """Obtiene un cliente por su NIT (dpi_nit)"""
        query = """
            SELECT 
                c.id_cliente, c.id_persona, c.tipo_cliente,
                c.limite_credito, c.descuento_habitual,
                c.fecha_primera_compra, c.total_compras,
                c.estado, c.created_at, c.updated_at,
                p.nombre, p.apellido, p.telefono, p.email,
                p.direccion, p.dpi_nit, p.fecha_registro, p.estado as persona_estado
            FROM clientes c
            INNER JOIN personas p ON c.id_persona = p.id_persona
            WHERE p.dpi_nit = %s
        """
        
        result = self.db.execute_query(query, (nit,), fetch='one')
        
        if result:
            return Cliente.from_dict(result)
        return None
    
    def listar(
        self,
        solo_activos: bool = True,
        tipo_cliente: Optional[str] = None,
        busqueda: Optional[str] = None
    ) -> List[Cliente]:
        """
        Lista clientes con filtros opcionales
        
        Args:
            solo_activos: Si True, solo retorna clientes activos
            tipo_cliente: Filtrar por tipo (minorista, mayorista)
            busqueda: Término de búsqueda (nombre, apellido, NIT, teléfono)
        """
        query = """
            SELECT 
                c.id_cliente, c.id_persona, c.tipo_cliente,
                c.limite_credito, c.descuento_habitual,
                c.fecha_primera_compra, c.total_compras,
                c.estado, c.created_at, c.updated_at,
                p.nombre, p.apellido, p.telefono, p.email,
                p.direccion, p.dpi_nit, p.fecha_registro, p.estado as persona_estado
            FROM clientes c
            INNER JOIN personas p ON c.id_persona = p.id_persona
            WHERE 1=1
        """
        params = []
        
        if solo_activos:
            query += " AND c.estado = TRUE"
        
        if tipo_cliente:
            query += " AND c.tipo_cliente = %s"
            params.append(tipo_cliente)
        
        if busqueda:
            query += """ AND (
                LOWER(p.nombre) LIKE LOWER(%s) OR 
                LOWER(p.apellido) LIKE LOWER(%s) OR
                LOWER(p.dpi_nit) LIKE LOWER(%s) OR
                LOWER(p.telefono) LIKE LOWER(%s)
            )"""
            params.extend([f'%{busqueda}%'] * 4)
        
        query += " ORDER BY p.nombre, p.apellido ASC"
        
        result = self.db.execute_query(query, tuple(params) if params else None, fetch='all')
        
        if result:
            return [Cliente.from_dict(row) for row in result]
        return []
    
    def listar_todos(self) -> List[Cliente]:
        """
        Obtiene todos los clientes activos sin paginación
        
        Returns:
            Lista de todos los clientes activos
        """
        return self.listar(solo_activos=True)
    
    def actualizar(self, cliente: Cliente) -> Dict[str, Any]:
        """
        Actualiza un cliente existente (persona + cliente)
        
        Args:
            cliente: Objeto Cliente con datos actualizados
            
        Returns:
            Dict con 'success' (bool) y 'message' (str)
        """
        try:
            # Validar
            es_valido, mensaje = cliente.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            if not cliente.id_cliente or not cliente.persona.id_persona:
                return {'success': False, 'message': 'ID de cliente no especificado'}
            
            # Actualizar persona
            query_persona = """
                UPDATE personas
                SET nombre = %s,
                    apellido = %s,
                    telefono = %s,
                    email = %s,
                    direccion = %s,
                    dpi_nit = %s
                WHERE id_persona = %s
            """
            
            self.db.execute_query(
                query_persona,
                (cliente.persona.nombre, cliente.persona.apellido,
                 cliente.persona.telefono, cliente.persona.email,
                 cliente.persona.direccion, cliente.persona.dpi_nit,
                 cliente.persona.id_persona),
                fetch=False
            )
            
            # Actualizar cliente
            query_cliente = """
                UPDATE clientes
                SET tipo_cliente = %s,
                    limite_credito = %s,
                    descuento_habitual = %s,
                    estado = %s
                WHERE id_cliente = %s
            """
            
            self.db.execute_query(
                query_cliente,
                (cliente.tipo_cliente, cliente.limite_credito,
                 cliente.descuento_habitual, cliente.estado,
                 cliente.id_cliente),
                fetch=False
            )
            
            return {'success': True, 'message': 'Cliente actualizado exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def eliminar(self, id_cliente: int) -> Dict[str, Any]:
        """
        Elimina (desactiva) un cliente
        
        Args:
            id_cliente: ID del cliente a eliminar
            
        Returns:
            Dict con 'success' (bool) y 'message' (str)
        """
        try:
            # Verificar si tiene ventas
            ventas = self.db.execute_query(
                "SELECT COUNT(*) as total FROM ventas WHERE id_cliente = %s",
                (id_cliente,),
                fetch='one'
            )
            
            if ventas and ventas['total'] > 0:
                # Solo desactivar el cliente (tiene historial de ventas)
                query = "UPDATE clientes SET estado = FALSE WHERE id_cliente = %s"
                self.db.execute_query(query, (id_cliente,), fetch=False)
                return {
                    'success': True,
                    'message': f'Cliente desactivado (tiene {ventas["total"]} ventas asociadas)'
                }
            else:
                # Desactivar cliente sin ventas
                query = "UPDATE clientes SET estado = FALSE WHERE id_cliente = %s"
                self.db.execute_query(query, (id_cliente,), fetch=False)
                return {'success': True, 'message': 'Cliente desactivado exitosamente'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def contar_total(self, solo_activos: bool = True) -> int:
        """Cuenta el total de clientes"""
        query = """
            SELECT COUNT(*) as total 
            FROM clientes c
            INNER JOIN personas p ON c.id_persona = p.id_persona
        """
        if solo_activos:
            query += " WHERE c.estado = TRUE"
        
        result = self.db.execute_query(query, fetch='one')
        return result['total'] if result else 0
