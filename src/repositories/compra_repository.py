"""
Repository para gestión de compras
"""
from typing import List, Optional, Dict, Any
from database.connection import DatabaseConnection
from models.compra import Compra, DetalleCompra


class CompraRepository:
    """Repository para operaciones CRUD de compras"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def crear(self, compra: Compra) -> Dict[str, Any]:
        """
        Crea una nueva compra con sus detalles
        IMPORTANTE: También actualiza el stock y precios de los productos
        """
        try:
            # Validar compra
            es_valido, mensaje = compra.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            # Iniciar transacción
            # 1. Insertar compra
            query_compra = """
                INSERT INTO compras (
                    numero_factura, id_proveedor, id_empleado,
                    fecha_compra, total, estado, observaciones
                )
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s)
                RETURNING id_compra, fecha_compra
            """
            
            result = self.db.execute_query(
                query_compra,
                (compra.numero_factura, compra.id_proveedor, compra.id_empleado,
                 compra.total, compra.estado, compra.observaciones),
                fetch='one'
            )
            
            if not result:
                return {'success': False, 'message': 'Error al crear la compra'}
            
            id_compra = result['id_compra']
            
            # 2. Insertar detalles de compra y actualizar productos
            query_detalle = """
                INSERT INTO detalle_compras (
                    id_compra, id_producto, cantidad,
                    precio_unitario, subtotal
                )
                VALUES (%s, %s, %s, %s, %s)
            """
            
            for detalle in compra.detalles:
                # Insertar detalle
                self.db.execute_query(
                    query_detalle,
                    (id_compra, detalle.id_producto, detalle.cantidad,
                     detalle.precio_unitario, detalle.subtotal),
                    fetch=False
                )
                
                # 3. Actualizar stock del producto (SUMAR)
                query_stock = """
                    UPDATE productos
                    SET stock_actual = stock_actual + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id_producto = %s
                """
                
                self.db.execute_query(
                    query_stock,
                    (detalle.cantidad, detalle.id_producto),
                    fetch=False
                )
                
                # 4. Actualizar precio de costo del producto
                # El precio de venta se calcula automáticamente por el trigger de margen
                query_precio = """
                    UPDATE productos
                    SET precio_costo = %s,
                        precio_venta = %s * (1 + (margen_ganancia / 100)),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id_producto = %s
                """
                
                self.db.execute_query(
                    query_precio,
                    (detalle.precio_unitario, detalle.precio_unitario, detalle.id_producto),
                    fetch=False
                )
            
            return {
                'success': True,
                'message': 'Compra registrada exitosamente',
                'id_compra': id_compra
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def obtener_por_id(self, id_compra: int) -> Optional[Compra]:
        """Obtiene una compra por su ID con sus detalles"""
        # Query principal para la compra
        query = """
            SELECT 
                c.id_compra, c.numero_factura, c.id_proveedor,
                c.id_empleado, c.fecha_compra, c.total,
                c.estado, c.observaciones,
                c.created_at, c.updated_at,
                prov.nombre_empresa as nombre_proveedor,
                CONCAT(pe.nombre, ' ', pe.apellido) as nombre_empleado
            FROM compras c
            LEFT JOIN proveedores prov ON c.id_proveedor = prov.id_proveedor
            LEFT JOIN empleados e ON c.id_empleado = e.id_empleado
            LEFT JOIN personas pe ON e.id_persona = pe.id_persona
            WHERE c.id_compra = %s
        """
        
        result = self.db.execute_query(query, (id_compra,), fetch='one')
        
        if not result:
            return None
        
        # Query para los detalles
        query_detalles = """
            SELECT 
                dc.id_detalle_compra, dc.id_compra, dc.id_producto,
                dc.cantidad, dc.precio_unitario, dc.subtotal,
                dc.created_at,
                p.codigo as codigo_producto,
                p.nombre as nombre_producto
            FROM detalle_compras dc
            INNER JOIN productos p ON dc.id_producto = p.id_producto
            WHERE dc.id_compra = %s
            ORDER BY dc.id_detalle_compra
        """
        
        detalles_data = self.db.execute_query(query_detalles, (id_compra,), fetch='all')
        
        # Crear modelo Compra
        compra_dict = dict(result)
        compra_dict['detalles'] = detalles_data or []
        
        return Compra.from_dict(compra_dict)
    
    def listar(
        self,
        id_proveedor: Optional[int] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        estado: Optional[str] = None
    ) -> List[Compra]:
        """
        Lista compras con filtros opcionales
        
        Args:
            id_proveedor: Filtrar por proveedor
            fecha_desde: Fecha inicio (formato: YYYY-MM-DD)
            fecha_hasta: Fecha fin (formato: YYYY-MM-DD)
            estado: Filtrar por estado (completada, pendiente, cancelada)
        """
        query = """
            SELECT 
                c.id_compra, c.numero_factura, c.id_proveedor,
                c.id_empleado, c.fecha_compra, c.total,
                c.estado, c.observaciones,
                c.created_at, c.updated_at,
                prov.nombre_empresa as nombre_proveedor,
                CONCAT(pe.nombre, ' ', pe.apellido) as nombre_empleado
            FROM compras c
            LEFT JOIN proveedores prov ON c.id_proveedor = prov.id_proveedor
            LEFT JOIN empleados e ON c.id_empleado = e.id_empleado
            LEFT JOIN personas pe ON e.id_persona = pe.id_persona
            WHERE 1=1
        """
        params = []
        
        if id_proveedor:
            query += " AND c.id_proveedor = %s"
            params.append(id_proveedor)
        
        if fecha_desde:
            query += " AND DATE(c.fecha_compra) >= %s"
            params.append(fecha_desde)
        
        if fecha_hasta:
            query += " AND DATE(c.fecha_compra) <= %s"
            params.append(fecha_hasta)
        
        if estado:
            query += " AND c.estado = %s"
            params.append(estado)
        
        query += " ORDER BY c.fecha_compra DESC, c.id_compra DESC"
        
        results = self.db.execute_query(query, tuple(params) if params else None, fetch='all')
        
        if not results:
            return []
        
        # No cargar detalles aquí para optimizar el listado
        return [Compra.from_dict(dict(row)) for row in results]
    
    def anular(self, id_compra: int) -> Dict[str, Any]:
        """
        Anula una compra (marca como cancelada)
        IMPORTANTE: También revierte el stock de los productos
        """
        try:
            # Obtener detalles de la compra para revertir stock
            compra = self.obtener_por_id(id_compra)
            
            if not compra:
                return {'success': False, 'message': 'Compra no encontrada'}
            
            if compra.estado == 'cancelada':
                return {'success': False, 'message': 'La compra ya está cancelada'}
            
            # Revertir stock de cada producto
            for detalle in compra.detalles:
                query_stock = """
                    UPDATE productos
                    SET stock_actual = stock_actual - %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id_producto = %s
                """
                
                self.db.execute_query(
                    query_stock,
                    (detalle.cantidad, detalle.id_producto),
                    fetch=False
                )
            
            # Marcar compra como cancelada
            query = """
                UPDATE compras
                SET estado = 'cancelada',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_compra = %s
            """
            
            self.db.execute_query(query, (id_compra,), fetch=False)
            
            return {'success': True, 'message': 'Compra anulada exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def contar_total(self, estado: Optional[str] = None) -> int:
        """Cuenta el total de compras"""
        query = "SELECT COUNT(*) as total FROM compras WHERE 1=1"
        params = []
        
        if estado:
            query += " AND estado = %s"
            params.append(estado)
        
        result = self.db.execute_query(query, tuple(params) if params else None, fetch='one')
        return result['total'] if result else 0
