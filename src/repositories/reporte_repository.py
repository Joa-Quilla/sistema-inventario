"""
Repositorio para Reportes
Maneja todas las consultas SQL para generación de reportes
"""
from typing import List, Dict, Any
from datetime import datetime, date
from database.connection import DatabaseConnection


class ReporteRepository:
    """Repositorio para generación de reportes del sistema"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def cierre_caja_diario(self, fecha: date) -> Dict[str, Any]:
        """
        Genera reporte de cierre de caja para un día específico
        
        Args:
            fecha: Fecha del reporte
            
        Returns:
            Dict con ventas, ingresos, egresos y totales del día
        """
        try:
            # Ventas del día
            query_ventas = """
                SELECT 
                    v.id_venta,
                    v.numero_factura,
                    v.fecha_venta,
                    v.total,
                    v.metodo_pago,
                    c.nombre || ' ' || c.apellido as cliente,
                    e.nombre || ' ' || e.apellido as empleado
                FROM ventas v
                JOIN clientes cl ON v.id_cliente = cl.id_cliente
                JOIN personas c ON cl.id_persona = c.id_persona
                JOIN empleados emp ON v.id_empleado = emp.id_empleado
                JOIN personas e ON emp.id_persona = e.id_persona
                WHERE DATE(v.fecha_venta) = %s
                ORDER BY v.fecha_venta DESC
            """
            
            ventas = self.db.execute_query(query_ventas, (fecha,))
            
            # Resumen del día
            query_resumen = """
                SELECT 
                    COUNT(*) as total_ventas,
                    COALESCE(SUM(total), 0) as total_ingresos,
                    COALESCE(SUM(CASE WHEN metodo_pago = 'efectivo' THEN total ELSE 0 END), 0) as efectivo,
                    COALESCE(SUM(CASE WHEN metodo_pago = 'tarjeta' THEN total ELSE 0 END), 0) as tarjeta,
                    COALESCE(SUM(CASE WHEN metodo_pago = 'transferencia' THEN total ELSE 0 END), 0) as transferencia
                FROM ventas
                WHERE DATE(fecha_venta) = %s
            """
            
            resumen = self.db.execute_query(query_resumen, (fecha,), fetch='one')
            
            return {
                'success': True,
                'fecha': fecha,
                'ventas': ventas or [],
                'resumen': resumen or {}
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cierre_caja_mensual(self, año: int, mes: int) -> Dict[str, Any]:
        """
        Genera reporte de cierre de caja mensual
        
        Args:
            año: Año del reporte
            mes: Mes del reporte (1-12)
            
        Returns:
            Dict con resumen de ventas por día del mes
        """
        try:
            query = """
                SELECT 
                    DATE(fecha_venta) as fecha,
                    COUNT(*) as total_ventas,
                    COALESCE(SUM(total), 0) as total_ingresos,
                    COALESCE(SUM(CASE WHEN metodo_pago = 'efectivo' THEN total ELSE 0 END), 0) as efectivo,
                    COALESCE(SUM(CASE WHEN metodo_pago = 'tarjeta' THEN total ELSE 0 END), 0) as tarjeta,
                    COALESCE(SUM(CASE WHEN metodo_pago = 'transferencia' THEN total ELSE 0 END), 0) as transferencia
                FROM ventas
                WHERE EXTRACT(YEAR FROM fecha_venta) = %s
                AND EXTRACT(MONTH FROM fecha_venta) = %s
                GROUP BY DATE(fecha_venta)
                ORDER BY fecha DESC
            """
            
            datos_diarios = self.db.execute_query(query, (año, mes))
            
            # Resumen total del mes
            query_resumen = """
                SELECT 
                    COUNT(*) as total_ventas,
                    COALESCE(SUM(total), 0) as total_ingresos,
                    COALESCE(AVG(total), 0) as promedio_venta
                FROM ventas
                WHERE EXTRACT(YEAR FROM fecha_venta) = %s
                AND EXTRACT(MONTH FROM fecha_venta) = %s
            """
            
            resumen = self.db.execute_query(query_resumen, (año, mes), fetch='one')
            
            return {
                'success': True,
                'año': año,
                'mes': mes,
                'datos_diarios': datos_diarios or [],
                'resumen': resumen or {}
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def compras_por_periodo(self, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
        """
        Genera reporte de compras en un periodo de tiempo
        
        Args:
            fecha_inicio: Fecha inicial del periodo
            fecha_fin: Fecha final del periodo
            
        Returns:
            Dict con listado de compras y resumen
        """
        try:
            query_compras = """
                SELECT 
                    c.id_compra,
                    c.numero_factura,
                    c.fecha_compra,
                    c.total,
                    prov.nombre_empresa as proveedor,
                    e.nombre || ' ' || e.apellido as empleado,
                    COUNT(dc.id_detalle_compra) as total_productos
                FROM compras c
                JOIN proveedores prov ON c.id_proveedor = prov.id_proveedor
                JOIN empleados emp ON c.id_empleado = emp.id_empleado
                JOIN personas e ON emp.id_persona = e.id_persona
                LEFT JOIN detalle_compras dc ON c.id_compra = dc.id_compra
                WHERE DATE(c.fecha_compra) BETWEEN %s AND %s
                GROUP BY c.id_compra, c.numero_factura, c.fecha_compra, c.total, 
                         prov.nombre_empresa, e.nombre, e.apellido
                ORDER BY c.fecha_compra DESC
            """
            
            compras = self.db.execute_query(query_compras, (fecha_inicio, fecha_fin))
            
            # Resumen del periodo
            query_resumen = """
                SELECT 
                    COUNT(*) as total_compras,
                    COALESCE(SUM(total), 0) as total_gastado,
                    COALESCE(AVG(total), 0) as promedio_compra
                FROM compras
                WHERE DATE(fecha_compra) BETWEEN %s AND %s
            """
            
            resumen = self.db.execute_query(query_resumen, (fecha_inicio, fecha_fin), fetch='one')
            
            return {
                'success': True,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'compras': compras or [],
                'resumen': resumen or {}
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def productos_y_existencias(self) -> Dict[str, Any]:
        """
        Genera reporte de productos con sus existencias actuales
        
        Returns:
            Dict con listado de productos, stock y alertas
        """
        try:
            query = """
                SELECT 
                    p.id_producto,
                    p.codigo,
                    p.nombre,
                    p.descripcion,
                    c.nombre as categoria,
                    p.stock_actual,
                    p.stock_minimo,
                    p.precio_venta,
                    p.precio_costo,
                    p.estado,
                    CASE 
                        WHEN p.stock_actual = 0 THEN 'SIN_STOCK'
                        WHEN p.stock_actual <= p.stock_minimo THEN 'BAJO_STOCK'
                        ELSE 'NORMAL'
                    END as nivel_stock
                FROM productos p
                LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
                ORDER BY 
                    CASE 
                        WHEN p.stock_actual = 0 THEN 1
                        WHEN p.stock_actual <= p.stock_minimo THEN 2
                        ELSE 3
                    END,
                    p.nombre
            """
            
            productos = self.db.execute_query(query)
            
            # Estadísticas de inventario
            query_stats = """
                SELECT 
                    COUNT(*) as total_productos,
                    COUNT(CASE WHEN stock_actual = 0 THEN 1 END) as sin_stock,
                    COUNT(CASE WHEN stock_actual <= stock_minimo AND stock_actual > 0 THEN 1 END) as bajo_stock,
                    COALESCE(SUM(stock_actual), 0) as total_unidades,
                    COALESCE(SUM(stock_actual * precio_venta), 0) as valor_inventario
                FROM productos
                WHERE estado = true
            """
            
            stats = self.db.execute_query(query_stats, fetch='one')
            
            return {
                'success': True,
                'productos': productos or [],
                'estadisticas': stats or {}
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cartera_clientes(self) -> Dict[str, Any]:
        """
        Genera reporte de cartera de clientes con historial de compras
        
        Returns:
            Dict con listado de clientes y sus estadísticas
        """
        try:
            query = """
                SELECT 
                    c.id_cliente,
                    p.nombre,
                    p.apellido,
                    p.email,
                    p.telefono,
                    p.dpi_nit,
                    p.direccion,
                    COUNT(v.id_venta) as total_compras,
                    COALESCE(SUM(v.total), 0) as total_gastado,
                    COALESCE(MAX(v.fecha_venta), NULL) as ultima_compra
                FROM clientes c
                JOIN personas p ON c.id_persona = p.id_persona
                LEFT JOIN ventas v ON c.id_cliente = v.id_cliente
                WHERE p.estado = true
                GROUP BY c.id_cliente, p.nombre, p.apellido, p.email, 
                         p.telefono, p.dpi_nit, p.direccion
                ORDER BY total_gastado DESC
            """
            
            clientes = self.db.execute_query(query)
            
            # Estadísticas generales
            query_stats = """
                SELECT 
                    COUNT(DISTINCT c.id_cliente) as total_clientes,
                    COUNT(v.id_venta) as total_ventas,
                    COALESCE(AVG(v.total), 0) as ticket_promedio
                FROM clientes c
                JOIN personas p ON c.id_persona = p.id_persona
                LEFT JOIN ventas v ON c.id_cliente = v.id_cliente
                WHERE p.estado = true
            """
            
            stats = self.db.execute_query(query_stats, fetch='one')
            
            return {
                'success': True,
                'clientes': clientes or [],
                'estadisticas': stats or {}
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cartera_proveedores(self) -> Dict[str, Any]:
        """
        Genera reporte de cartera de proveedores con historial
        
        Returns:
            Dict con listado de proveedores y sus estadísticas
        """
        try:
            query = """
                SELECT 
                    prov.id_proveedor,
                    prov.nombre_empresa,
                    p.nombre || ' ' || p.apellido as nombre_contacto,
                    prov.email_empresa as email,
                    prov.telefono_empresa as telefono,
                    prov.direccion_empresa as direccion,
                    COUNT(c.id_compra) as total_compras,
                    COALESCE(SUM(c.total), 0) as total_comprado,
                    COALESCE(MAX(c.fecha_compra), NULL) as ultima_compra
                FROM proveedores prov
                LEFT JOIN personas p ON prov.id_persona_contacto = p.id_persona
                LEFT JOIN compras c ON prov.id_proveedor = c.id_proveedor
                WHERE prov.estado = true
                GROUP BY prov.id_proveedor, prov.nombre_empresa, p.nombre, p.apellido,
                         prov.email_empresa, prov.telefono_empresa, prov.direccion_empresa
                ORDER BY total_comprado DESC
            """
            
            proveedores = self.db.execute_query(query)
            
            # Estadísticas generales
            query_stats = """
                SELECT 
                    COUNT(DISTINCT prov.id_proveedor) as total_proveedores,
                    COUNT(c.id_compra) as total_compras,
                    COALESCE(AVG(c.total), 0) as compra_promedio
                FROM proveedores prov
                LEFT JOIN compras c ON prov.id_proveedor = c.id_proveedor
                WHERE prov.estado = true
            """
            
            stats = self.db.execute_query(query_stats, fetch='one')
            
            return {
                'success': True,
                'proveedores': proveedores or [],
                'estadisticas': stats or {}
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cartera_empleados(self) -> Dict[str, Any]:
        """
        Genera reporte de cartera de empleados con información laboral
        
        Returns:
            Dict con listado de empleados y sus datos
        """
        try:
            query = """
                SELECT 
                    e.id_empleado,
                    p.nombre,
                    p.apellido,
                    p.email,
                    p.telefono,
                    p.dpi_nit,
                    e.puesto,
                    r.nombre as rol,
                    e.fecha_contratacion,
                    e.salario,
                    e.estado,
                    COUNT(DISTINCT v.id_venta) as total_ventas_realizadas,
                    COALESCE(SUM(v.total), 0) as monto_total_ventas
                FROM empleados e
                JOIN personas p ON e.id_persona = p.id_persona
                JOIN roles r ON e.id_rol = r.id_rol
                LEFT JOIN ventas v ON e.id_empleado = v.id_empleado
                GROUP BY e.id_empleado, p.nombre, p.apellido, p.email, p.telefono,
                         p.dpi_nit, e.puesto, r.nombre, e.fecha_contratacion, 
                         e.salario, e.estado
                ORDER BY e.estado DESC, p.apellido, p.nombre
            """
            
            empleados = self.db.execute_query(query)
            
            # Estadísticas generales
            query_stats = """
                SELECT 
                    COUNT(CASE WHEN e.estado = true THEN 1 END) as empleados_activos,
                    COUNT(CASE WHEN e.estado = false THEN 1 END) as empleados_inactivos,
                    COUNT(*) as total_empleados,
                    COALESCE(AVG(CASE WHEN e.estado = true THEN e.salario END), 0) as salario_promedio
                FROM empleados e
                JOIN personas p ON e.id_persona = p.id_persona
            """
            
            stats = self.db.execute_query(query_stats, fetch='one')
            
            return {
                'success': True,
                'empleados': empleados or [],
                'estadisticas': stats or {}
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
