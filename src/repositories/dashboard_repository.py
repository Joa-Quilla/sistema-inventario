"""
Repositorio para estadísticas del Dashboard
"""
from database.connection import get_connection
from typing import Dict, Any
from datetime import datetime, date


class DashboardRepository:
    """Repositorio para obtener estadísticas del dashboard"""
    
    @staticmethod
    def obtener_estadisticas_ventas_hoy() -> Dict[str, Any]:
        """Obtiene estadísticas de ventas del día actual"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            hoy = date.today()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_ventas,
                    COALESCE(SUM(total), 0) as ingresos_totales,
                    COALESCE(AVG(total), 0) as ticket_promedio
                FROM ventas
                WHERE DATE(fecha_venta) = %s
            """, (hoy,))
            
            row = cursor.fetchone()
            cursor.close()
            
            return {
                'success': True,
                'total_ventas': int(row[0]),
                'ingresos_totales': float(row[1]),
                'ticket_promedio': float(row[2])
            }
            
        except Exception as e:
            print(f"[ERROR] Error en obtener_estadisticas_ventas_hoy: {e}")
            return {
                'success': False,
                'message': f'Error al obtener estadísticas: {str(e)}',
                'total_ventas': 0,
                'ingresos_totales': 0,
                'ticket_promedio': 0
            }
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def obtener_estadisticas_mes() -> Dict[str, Any]:
        """Obtiene estadísticas del mes actual"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            hoy = date.today()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_ventas,
                    COALESCE(SUM(total), 0) as ingresos_totales
                FROM ventas
                WHERE EXTRACT(MONTH FROM fecha_venta) = %s
                AND EXTRACT(YEAR FROM fecha_venta) = %s
            """, (hoy.month, hoy.year))
            
            row = cursor.fetchone()
            cursor.close()
            
            return {
                'success': True,
                'total_ventas_mes': int(row[0]),
                'ingresos_mes': float(row[1])
            }
            
        except Exception as e:
            print(f"[ERROR] Error en obtener_estadisticas_mes: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'total_ventas_mes': 0,
                'ingresos_mes': 0
            }
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def obtener_productos_bajo_stock() -> Dict[str, Any]:
        """Obtiene productos con bajo stock"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*)
                FROM productos
                WHERE stock <= stock_minimo
                AND activo = true
            """)
            
            count = cursor.fetchone()[0]
            
            # Obtener los productos
            cursor.execute("""
                SELECT 
                    p.nombre,
                    p.codigo,
                    p.stock,
                    p.stock_minimo,
                    c.nombre as categoria
                FROM productos p
                LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
                WHERE p.stock <= p.stock_minimo
                AND p.activo = true
                ORDER BY p.stock ASC
                LIMIT 5
            """)
            
            productos = []
            for row in cursor.fetchall():
                productos.append({
                    'nombre': row[0],
                    'codigo': row[1],
                    'stock': row[2],
                    'stock_minimo': row[3],
                    'categoria': row[4]
                })
            
            cursor.close()
            
            return {
                'success': True,
                'total_bajo_stock': count,
                'productos': productos
            }
            
        except Exception as e:
            print(f"[ERROR] Error en obtener_productos_bajo_stock: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'total_bajo_stock': 0,
                'productos': []
            }
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def obtener_productos_mas_vendidos() -> Dict[str, Any]:
        """Obtiene los productos más vendidos del mes"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            hoy = date.today()
            
            # Verificar si existe la tabla detalle_ventas
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'detalle_ventas'
                )
            """)
            
            if not cursor.fetchone()[0]:
                cursor.close()
                return {'success': True, 'productos': []}
            
            cursor.execute("""
                SELECT 
                    p.nombre,
                    p.codigo,
                    COALESCE(SUM(dv.cantidad), 0) as total_vendido,
                    COALESCE(SUM(dv.subtotal), 0) as ingresos
                FROM detalle_ventas dv
                JOIN productos p ON dv.id_producto = p.id_producto
                JOIN ventas v ON dv.id_venta = v.id_venta
                WHERE EXTRACT(MONTH FROM v.fecha_venta) = %s
                AND EXTRACT(YEAR FROM v.fecha_venta) = %s
                GROUP BY p.id_producto, p.nombre, p.codigo
                ORDER BY total_vendido DESC
                LIMIT 5
            """, (hoy.month, hoy.year))
            
            productos = []
            for row in cursor.fetchall():
                productos.append({
                    'nombre': row[0],
                    'codigo': row[1],
                    'cantidad': int(row[2]),
                    'ingresos': float(row[3])
                })
            
            cursor.close()
            
            return {
                'success': True,
                'productos': productos
            }
            
        except Exception as e:
            print(f"[ERROR] Error en obtener_productos_mas_vendidos: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'productos': []
            }
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def obtener_ultimas_ventas() -> Dict[str, Any]:
        """Obtiene las últimas 5 ventas realizadas"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    v.numero_factura,
                    v.fecha_venta,
                    v.total,
                    v.metodo_pago,
                    CONCAT(p.nombre, ' ', p.apellido) as cliente
                FROM ventas v
                LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN personas p ON c.id_persona = p.id_persona
                ORDER BY v.fecha_venta DESC
                LIMIT 5
            """)
            
            ventas = []
            for row in cursor.fetchall():
                ventas.append({
                    'numero_factura': row[0],
                    'fecha': row[1],
                    'total': float(row[2]),
                    'metodo_pago': row[3],
                    'cliente': row[4] if row[4] else 'Cliente General'
                })
            
            cursor.close()
            
            return {
                'success': True,
                'ventas': ventas
            }
            
        except Exception as e:
            print(f"[ERROR] Error en obtener_ultimas_ventas: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'ventas': []
            }
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def obtener_totales_generales() -> Dict[str, Any]:
        """Obtiene totales generales del sistema"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Total productos activos
            cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = true")
            total_productos = cursor.fetchone()[0]
            
            # Total clientes activos
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE activo = true")
            total_clientes = cursor.fetchone()[0]
            
            # Total proveedores activos
            cursor.execute("SELECT COUNT(*) FROM proveedores WHERE activo = true")
            total_proveedores = cursor.fetchone()[0]
            
            # Valor total del inventario
            cursor.execute("""
                SELECT COALESCE(SUM(stock * precio_venta), 0)
                FROM productos
                WHERE activo = true
            """)
            valor_inventario = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                'success': True,
                'total_productos': int(total_productos),
                'total_clientes': int(total_clientes),
                'total_proveedores': int(total_proveedores),
                'valor_inventario': float(valor_inventario)
            }
            
        except Exception as e:
            print(f"[ERROR] Error en obtener_totales_generales: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'total_productos': 0,
                'total_clientes': 0,
                'total_proveedores': 0,
                'valor_inventario': 0
            }
        finally:
            if conn:
                conn.close()
