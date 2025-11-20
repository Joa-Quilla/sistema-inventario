"""
Repositorio para operaciones CRUD de Productos
"""
from typing import List, Optional, Dict, Any
from database.connection import DatabaseConnection
from models.producto import Producto


class ProductoRepository:
    """Repositorio para gestión de productos"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def crear(self, producto: Producto) -> Dict[str, Any]:
        """
        Crea un nuevo producto
        
        Args:
            producto: Objeto Producto a crear
            
        Returns:
            Dict con 'success' (bool), 'message' (str), 'id_producto' (int si success=True)
        """
        try:
            # Validar
            es_valido, mensaje = producto.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            # Verificar que no exista un producto con el mismo código
            existe = self.obtener_por_codigo(producto.codigo)
            if existe:
                return {'success': False, 'message': f'Ya existe un producto con el código "{producto.codigo}"'}
            
            query = """
                INSERT INTO productos 
                    (id_categoria, codigo, nombre, descripcion, unidad_medida,
                     precio_costo, precio_venta,
                     stock_actual, stock_minimo,
                     lote, fecha_vencimiento, ubicacion, estado)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_producto, created_at as fecha_creacion
            """
            
            estado_bool = producto.estado == 'activo'
            result = self.db.execute_query(
                query,
                (producto.id_categoria, producto.codigo, producto.nombre, producto.descripcion,
                 producto.unidad_medida, producto.precio_compra, producto.precio_venta,
                 producto.stock_actual, producto.stock_minimo,
                 producto.lote, producto.fecha_vencimiento, producto.ubicacion, estado_bool),
                fetch='one'
            )
            
            if result:
                return {
                    'success': True,
                    'message': 'Producto creado exitosamente',
                    'id_producto': result['id_producto'],
                    'fecha_creacion': result['fecha_creacion']
                }
            else:
                return {'success': False, 'message': 'Error al crear el producto'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def obtener_por_id(self, id_producto: int) -> Optional[Producto]:
        """Obtiene un producto por su ID con información de categoría"""
        query = """
            SELECT 
                p.id_producto,
                p.codigo,
                p.nombre,
                p.descripcion,
                p.id_categoria,
                p.precio_costo as precio_compra,
                p.precio_venta,
                p.stock_actual,
                p.stock_minimo,
                p.unidad_medida,
                p.lote,
                p.fecha_vencimiento,
                p.ubicacion,
                CASE WHEN p.estado THEN 'activo' ELSE 'inactivo' END as estado,
                p.created_at as fecha_creacion,
                p.updated_at as fecha_actualizacion,
                c.nombre as nombre_categoria
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE p.id_producto = %s
        """
        
        result = self.db.execute_query(query, (id_producto,), fetch='one')
        
        if result:
            return Producto.from_dict(result)
        return None
    
    def obtener_por_codigo(self, codigo: str) -> Optional[Producto]:
        """Obtiene un producto por su código"""
        query = """
            SELECT 
                p.id_producto,
                p.codigo,
                p.nombre,
                p.descripcion,
                p.id_categoria,
                p.precio_costo as precio_compra,
                p.precio_venta,
                p.stock_actual,
                p.stock_minimo,
                p.unidad_medida,
                p.lote,
                p.fecha_vencimiento,
                p.ubicacion,
                CASE WHEN p.estado THEN 'activo' ELSE 'inactivo' END as estado,
                p.created_at as fecha_creacion,
                c.nombre as nombre_categoria
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE LOWER(p.codigo) = LOWER(%s)
        """
        
        result = self.db.execute_query(query, (codigo,), fetch='one')
        
        if result:
            return Producto.from_dict(result)
        return None
    
    def listar(
        self, 
        solo_activos: bool = True,
        id_categoria: Optional[int] = None,
        busqueda: Optional[str] = None,
        solo_bajo_stock: bool = False
    ) -> List[Producto]:
        """
        Lista productos con filtros opcionales
        
        Args:
            solo_activos: Si True, solo retorna productos activos
            id_categoria: Filtrar por categoría específica
            busqueda: Término de búsqueda (busca en código, nombre, descripción)
            solo_bajo_stock: Si True, solo retorna productos con stock bajo
        """
        query = """
            SELECT 
                p.id_producto,
                p.codigo,
                p.nombre,
                p.descripcion,
                p.id_categoria,
                p.precio_costo as precio_compra,
                p.precio_venta,
                p.stock_actual,
                p.stock_minimo,
                p.unidad_medida,
                p.lote,
                p.fecha_vencimiento,
                p.ubicacion,
                CASE WHEN p.estado THEN 'activo' ELSE 'inactivo' END as estado,
                p.created_at as fecha_creacion,
                p.updated_at as fecha_actualizacion,
                c.nombre as nombre_categoria
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE 1=1
        """
        params = []
        
        if solo_activos:
            query += " AND p.estado = TRUE"
        
        if id_categoria:
            query += " AND p.id_categoria = %s"
            params.append(id_categoria)
        
        if busqueda:
            query += " AND (LOWER(p.codigo) LIKE LOWER(%s) OR LOWER(p.nombre) LIKE LOWER(%s) OR LOWER(p.descripcion) LIKE LOWER(%s))"
            params.extend([f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'])
        
        if solo_bajo_stock:
            query += " AND p.stock_actual <= p.stock_minimo"
        
        query += " ORDER BY p.nombre ASC"
        
        result = self.db.execute_query(query, tuple(params) if params else None, fetch='all')
        
        if result:
            return [Producto.from_dict(row) for row in result]
        return []
    
    def actualizar(self, producto: Producto) -> Dict[str, Any]:
        """
        Actualiza un producto existente (NO actualiza precios ni stock)
        Los precios se actualizan en Compras, el stock en Compras/Ventas
        
        Args:
            producto: Objeto Producto con datos actualizados
            
        Returns:
            Dict con 'success' (bool) y 'message' (str)
        """
        try:
            # Validar
            es_valido, mensaje = producto.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            if not producto.id_producto:
                return {'success': False, 'message': 'ID de producto no especificado'}
            
            # Verificar código duplicado
            existe = self.db.execute_query(
                "SELECT id_producto FROM productos WHERE LOWER(codigo) = LOWER(%s) AND id_producto != %s",
                (producto.codigo, producto.id_producto),
                fetch='one'
            )
            if existe:
                return {'success': False, 'message': f'Ya existe otro producto con el código "{producto.codigo}"'}
            
            # Solo actualizar información básica, NO precios ni stock
            query = """
                UPDATE productos
                SET id_categoria = %s,
                    codigo = %s,
                    nombre = %s,
                    descripcion = %s,
                    unidad_medida = %s,
                    stock_minimo = %s,
                    fecha_vencimiento = %s,
                    ubicacion = %s,
                    estado = %s
                WHERE id_producto = %s
            """
            
            estado_bool = producto.estado == 'activo'
            self.db.execute_query(
                query,
                (producto.id_categoria, producto.codigo, producto.nombre, producto.descripcion,
                 producto.unidad_medida, producto.stock_minimo,
                 producto.fecha_vencimiento, producto.ubicacion,
                 estado_bool, producto.id_producto),
                fetch=False
            )
            
            return {'success': True, 'message': 'Producto actualizado exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def actualizar_stock(self, id_producto: int, cantidad: int, operacion: str = 'sumar') -> Dict[str, Any]:
        """
        Actualiza el stock de un producto
        
        Args:
            id_producto: ID del producto
            cantidad: Cantidad a sumar o restar
            operacion: 'sumar' o 'restar'
            
        Returns:
            Dict con 'success' (bool), 'message' (str), 'stock_nuevo' (int si success=True)
        """
        try:
            if operacion == 'sumar':
                query = """
                    UPDATE productos
                    SET stock_actual = stock_actual + %s,
                        fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE id_producto = %s
                    RETURNING stock_actual
                """
            else:  # restar
                query = """
                    UPDATE productos
                    SET stock_actual = stock_actual - %s,
                        fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE id_producto = %s AND stock_actual >= %s
                    RETURNING stock_actual
                """
                
            params = (cantidad, id_producto, cantidad) if operacion == 'restar' else (cantidad, id_producto)
            result = self.db.execute_query(query, params, fetch='one')
            
            if result:
                return {
                    'success': True,
                    'message': 'Stock actualizado exitosamente',
                    'stock_nuevo': result['stock_actual']
                }
            else:
                return {'success': False, 'message': 'Stock insuficiente o producto no encontrado'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def eliminar(self, id_producto: int) -> Dict[str, Any]:
        """
        Elimina (desactiva) un producto
        
        Args:
            id_producto: ID del producto a eliminar
            
        Returns:
            Dict con 'success' (bool) y 'message' (str)
        """
        try:
            # Verificar si tiene ventas o compras asociadas
            ventas = self.db.execute_query(
                "SELECT COUNT(*) as total FROM detalle_ventas WHERE id_producto = %s",
                (id_producto,),
                fetch='one'
            )
            
            if ventas and ventas['total'] > 0:
                # No eliminar, solo desactivar
                query = "UPDATE productos SET estado = FALSE WHERE id_producto = %s"
                self.db.execute_query(query, (id_producto,), fetch=False)
                return {
                    'success': True,
                    'message': 'Producto desactivado (tiene historial de ventas)'
                }
            else:
                # Eliminar físicamente
                query = "DELETE FROM productos WHERE id_producto = %s"
                self.db.execute_query(query, (id_producto,), fetch=False)
                return {'success': True, 'message': 'Producto eliminado exitosamente'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def obtener_productos_bajo_stock(self) -> List[Producto]:
        """Obtiene productos con stock igual o menor al mínimo"""
        return self.listar(solo_bajo_stock=True)
    
    def listar_activos_para_ventas(self, busqueda: Optional[str] = None) -> List[Producto]:
        """
        Lista solo productos activos disponibles para ventas (con stock > 0)
        
        Args:
            busqueda: Término de búsqueda opcional
            
        Returns:
            Lista de productos activos con stock disponible
        """
        query = """
            SELECT 
                p.id_producto,
                p.codigo,
                p.nombre,
                p.descripcion,
                p.id_categoria,
                p.precio_costo as precio_compra,
                p.precio_venta,
                p.stock_actual,
                p.stock_minimo,
                p.unidad_medida,
                p.lote,
                p.fecha_vencimiento,
                p.ubicacion,
                'activo' as estado,
                p.created_at as fecha_creacion,
                c.nombre as nombre_categoria
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE p.estado = TRUE 
              AND p.stock_actual > 0
              AND c.estado = TRUE
        """
        
        params = []
        if busqueda:
            query += " AND (LOWER(p.codigo) LIKE LOWER(%s) OR LOWER(p.nombre) LIKE LOWER(%s))"
            params.extend([f'%{busqueda}%', f'%{busqueda}%'])
        
        query += " ORDER BY p.nombre ASC"
        
        result = self.db.execute_query(query, tuple(params) if params else None, fetch='all')
        
        if result:
            return [Producto.from_dict(row) for row in result]
        return []
    
    def contar_total(self, solo_activos: bool = True) -> int:
        """Cuenta el total de productos"""
        query = "SELECT COUNT(*) as total FROM productos"
        if solo_activos:
            query += " WHERE estado = TRUE"
        
        result = self.db.execute_query(query, fetch='one')
        return result['total'] if result else 0
