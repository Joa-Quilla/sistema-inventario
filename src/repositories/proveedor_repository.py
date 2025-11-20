"""
Repositorio para operaciones CRUD de Proveedores
"""
from typing import List, Optional, Dict, Any
from database.connection import DatabaseConnection
from models.proveedor import Proveedor


class ProveedorRepository:
    """Repositorio para gestión de proveedores"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def crear(self, proveedor: Proveedor) -> Dict[str, Any]:
        """Crea un nuevo proveedor"""
        try:
            es_valido, mensaje = proveedor.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            # Crear proveedor
            query_proveedor = """
                INSERT INTO proveedores 
                    (nombre_empresa, id_persona_contacto, telefono_empresa, email_empresa,
                     direccion_empresa, nit_empresa, sitio_web, tipo_proveedor, terminos_pago, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_proveedor
            """
            
            proveedor_result = self.db.execute_query(
                query_proveedor,
                (proveedor.nombre_empresa, proveedor.id_persona_contacto, 
                 proveedor.telefono_empresa, proveedor.email_empresa,
                 proveedor.direccion_empresa, proveedor.nit_empresa,
                 proveedor.sitio_web, proveedor.tipo_proveedor,
                 proveedor.terminos_pago, proveedor.estado),
                fetch='one'
            )
            
            if proveedor_result:
                return {
                    'success': True,
                    'message': 'Proveedor creado exitosamente',
                    'id_proveedor': proveedor_result['id_proveedor']
                }
            else:
                return {'success': False, 'message': 'Error al crear el proveedor'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def obtener_por_id(self, id_proveedor: int) -> Optional[Proveedor]:
        """Obtiene un proveedor por su ID"""
        query = """
            SELECT 
                pr.id_proveedor,
                pr.nombre_empresa,
                pr.id_persona_contacto,
                pr.telefono_empresa,
                pr.email_empresa,
                pr.direccion_empresa,
                pr.nit_empresa,
                pr.sitio_web,
                pr.tipo_proveedor,
                pr.terminos_pago,
                pr.estado,
                pr.fecha_registro,
                pr.created_at,
                pr.updated_at,
                p.nombre as contacto_nombre,
                p.apellido as contacto_apellido,
                p.telefono as contacto_telefono,
                p.email as contacto_email
            FROM proveedores pr
            LEFT JOIN personas p ON pr.id_persona_contacto = p.id_persona
            WHERE pr.id_proveedor = %s
        """
        
        result = self.db.execute_query(query, (id_proveedor,), fetch='one')
        
        if result:
            return Proveedor.from_dict(result)
        return None
    
    def listar(self, busqueda: Optional[str] = None) -> List[Proveedor]:
        """Lista proveedores activos con búsqueda opcional"""
        query = """
            SELECT 
                pr.id_proveedor,
                pr.nombre_empresa,
                pr.id_persona_contacto,
                pr.telefono_empresa,
                pr.email_empresa,
                pr.direccion_empresa,
                pr.nit_empresa,
                pr.sitio_web,
                pr.tipo_proveedor,
                pr.terminos_pago,
                pr.estado,
                pr.fecha_registro,
                pr.created_at,
                pr.updated_at,
                p.nombre as contacto_nombre,
                p.apellido as contacto_apellido,
                p.telefono as contacto_telefono,
                p.email as contacto_email
            FROM proveedores pr
            LEFT JOIN personas p ON pr.id_persona_contacto = p.id_persona
            WHERE pr.estado = true
        """
        params = []
        
        if busqueda:
            query += """ AND (
                LOWER(pr.nombre_empresa) LIKE LOWER(%s) OR
                LOWER(pr.nit_empresa) LIKE LOWER(%s)
            )"""
            params.extend([f'%{busqueda}%'] * 2)
        
        query += " ORDER BY pr.nombre_empresa ASC"
        
        result = self.db.execute_query(query, tuple(params) if params else None, fetch='all')
        
        if result:
            return [Proveedor.from_dict(row) for row in result]
        return []
    
    def listar_todos(self, busqueda: Optional[str] = None) -> List[Proveedor]:
        """Lista todos los proveedores (activos e inactivos) con búsqueda opcional"""
        query = """
            SELECT 
                pr.id_proveedor,
                pr.nombre_empresa,
                pr.id_persona_contacto,
                pr.telefono_empresa,
                pr.email_empresa,
                pr.direccion_empresa,
                pr.nit_empresa,
                pr.sitio_web,
                pr.tipo_proveedor,
                pr.terminos_pago,
                pr.estado,
                pr.fecha_registro,
                pr.created_at,
                pr.updated_at,
                p.nombre as contacto_nombre,
                p.apellido as contacto_apellido,
                p.telefono as contacto_telefono,
                p.email as contacto_email
            FROM proveedores pr
            LEFT JOIN personas p ON pr.id_persona_contacto = p.id_persona
            WHERE 1=1
        """
        params = []
        
        if busqueda:
            query += """ AND (
                LOWER(pr.nombre_empresa) LIKE LOWER(%s) OR
                LOWER(pr.nit_empresa) LIKE LOWER(%s)
            )"""
            params.extend([f'%{busqueda}%'] * 2)
        
        query += " ORDER BY pr.estado DESC, pr.nombre_empresa ASC"
        
        result = self.db.execute_query(query, tuple(params) if params else None, fetch='all')
        
        if result:
            return [Proveedor.from_dict(row) for row in result]
        return []
    
    def actualizar(self, proveedor: Proveedor) -> Dict[str, Any]:
        """Actualiza un proveedor existente"""
        try:
            es_valido, mensaje = proveedor.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            # Actualizar proveedor
            query_proveedor = """
                UPDATE proveedores
                SET nombre_empresa = %s, id_persona_contacto = %s, telefono_empresa = %s,
                    email_empresa = %s, direccion_empresa = %s, nit_empresa = %s,
                    sitio_web = %s, tipo_proveedor = %s, terminos_pago = %s,
                    estado = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id_proveedor = %s
            """
            
            self.db.execute_query(
                query_proveedor,
                (proveedor.nombre_empresa, proveedor.id_persona_contacto,
                 proveedor.telefono_empresa, proveedor.email_empresa,
                 proveedor.direccion_empresa, proveedor.nit_empresa,
                 proveedor.sitio_web, proveedor.tipo_proveedor,
                 proveedor.terminos_pago, proveedor.estado,
                 proveedor.id_proveedor),
                fetch=False
            )
            
            return {'success': True, 'message': 'Proveedor actualizado exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def eliminar(self, id_proveedor: int) -> Dict[str, Any]:
        """Elimina (desactiva) un proveedor"""
        try:
            # Verificar si tiene compras
            compras = self.db.execute_query(
                "SELECT COUNT(*) as total FROM compras WHERE id_proveedor = %s",
                (id_proveedor,),
                fetch='one'
            )
            
            if compras and compras['total'] > 0:
                query = """
                    UPDATE personas 
                    SET estado = 'inactivo' 
                    WHERE id_persona = (SELECT id_persona FROM proveedores WHERE id_proveedor = %s)
                """
                self.db.execute_query(query, (id_proveedor,))
                return {
                    'success': True,
                    'message': f'Proveedor desactivado (tiene {compras["total"]} compras asociadas)'
                }
            else:
                query_proveedor = "DELETE FROM proveedores WHERE id_proveedor = %s RETURNING id_persona"
                result = self.db.execute_query(query_proveedor, (id_proveedor,), fetch='one')
                
                if result:
                    self.db.execute_query("DELETE FROM personas WHERE id_persona = %s", (result['id_persona'],))
                
                return {'success': True, 'message': 'Proveedor eliminado exitosamente'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def contar_total(self) -> int:
        """Cuenta el total de proveedores activos"""
        query = """
            SELECT COUNT(*) as total 
            FROM proveedores pr
            INNER JOIN personas p ON pr.id_persona = p.id_persona
            WHERE p.estado = 'activo'
        """
        result = self.db.execute_query(query, fetch='one')
        return result['total'] if result else 0
