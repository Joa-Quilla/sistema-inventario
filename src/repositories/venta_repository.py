"""
Repository para gestión de Ventas.
Maneja operaciones CRUD y lógica de negocio relacionada con ventas.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from database.connection import DatabaseConnection
from models.venta import Venta, DetalleVenta


class VentaRepository:
    """Repository para operaciones de ventas"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def crear(self, venta: Venta, id_caja_actual: int) -> Dict[str, Any]:
        """
        Crea una nueva venta con sus detalles.
        
        Proceso:
        1. Validar stock disponible para todos los productos
        2. Insertar venta en tabla ventas
        3. Insertar detalles en tabla detalle_ventas
        4. RESTAR stock de cada producto (stock_actual - cantidad)
        5. Registrar movimiento de caja (ingreso)
        
        Args:
            venta: Objeto Venta con detalles
            id_caja_actual: ID de la caja abierta actual
        
        Returns:
            Dict con success y id_venta o mensaje de error
        """
        connection = None
        cursor = None
        
        try:
            # Validar venta
            es_valido, mensaje = venta.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # Paso 1: Validar stock disponible para todos los productos
            for detalle in venta.detalles:
                cursor.execute("""
                    SELECT stock_actual, nombre 
                    FROM productos 
                    WHERE id_producto = %s AND estado = true
                """, (detalle.id_producto,))
                
                producto_data = cursor.fetchone()
                if not producto_data:
                    return {
                        'success': False, 
                        'message': f'El producto con ID {detalle.id_producto} no existe o está inactivo'
                    }
                
                stock_actual = producto_data[0]
                nombre_producto = producto_data[1]
                
                if stock_actual < detalle.cantidad:
                    return {
                        'success': False,
                        'message': f'Stock insuficiente para {nombre_producto}. Disponible: {stock_actual}, Solicitado: {detalle.cantidad}'
                    }
            
            # Paso 2: Insertar venta
            cursor.execute("""
                INSERT INTO ventas (
                    numero_factura, id_cliente, id_empleado, id_caja,
                    fecha_venta, subtotal, descuento, total,
                    metodo_pago, estado, observaciones
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_venta
            """, (
                venta.numero_factura,
                venta.id_cliente,
                venta.id_empleado,
                id_caja_actual,
                venta.fecha_venta or datetime.now(),
                venta.subtotal,
                venta.descuento,
                venta.total,
                venta.metodo_pago,
                venta.estado,
                venta.observaciones
            ))
            
            id_venta = cursor.fetchone()[0]
            
            # Paso 3: Insertar detalles y actualizar stock
            for detalle in venta.detalles:
                # Insertar detalle
                cursor.execute("""
                    INSERT INTO detalle_ventas (
                        id_venta, id_producto, cantidad, 
                        precio_unitario, subtotal
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    id_venta,
                    detalle.id_producto,
                    detalle.cantidad,
                    detalle.precio_unitario,
                    detalle.subtotal
                ))
                
                # Paso 4: RESTAR stock (VENTAS DISMINUYEN EL STOCK)
                cursor.execute("""
                    UPDATE productos 
                    SET stock_actual = stock_actual - %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id_producto = %s
                """, (detalle.cantidad, detalle.id_producto))
            
            # Paso 5: Registrar movimiento de caja (INGRESO)
            cursor.execute("""
                INSERT INTO movimientos_caja (
                    id_caja, tipo, concepto, monto, 
                    fecha_movimiento, id_empleado, observaciones
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_caja_actual,
                'ingreso',
                f'Venta - Factura {venta.numero_factura}',
                venta.total,
                datetime.now(),
                venta.id_empleado,
                f'Método de pago: {venta.metodo_pago}'
            ))
            
            # Actualizar totales de caja
            cursor.execute("""
                UPDATE cajas 
                SET total_ventas = total_ventas + %s,
                    total_ingresos = total_ingresos + %s
                WHERE id_caja = %s
            """, (venta.total, venta.total, id_caja_actual))
            
            # Paso 6: Actualizar datos del cliente (si hay cliente)
            if venta.id_cliente:
                # Verificar si es la primera compra
                cursor.execute("""
                    SELECT fecha_primera_compra
                    FROM clientes
                    WHERE id_cliente = %s
                """, (venta.id_cliente,))
                
                cliente_data = cursor.fetchone()
                if cliente_data:
                    fecha_primera = cliente_data[0]
                    
                    if fecha_primera is None:
                        # Es la primera compra, actualizar fecha y total
                        cursor.execute("""
                            UPDATE clientes
                            SET fecha_primera_compra = CURRENT_DATE,
                                total_compras = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id_cliente = %s
                        """, (venta.total, venta.id_cliente))
                    else:
                        # Ya tiene compras, solo sumar al total
                        cursor.execute("""
                            UPDATE clientes
                            SET total_compras = total_compras + %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id_cliente = %s
                        """, (venta.total, venta.id_cliente))
            
            connection.commit()
            
            return {
                'success': True,
                'id_venta': id_venta,
                'message': 'Venta registrada exitosamente'
            }
            
        except Exception as e:
            if connection:
                connection.rollback()
            
            error_msg = str(e).lower()
            
            # Manejo de errores específicos
            if 'duplicate' in error_msg or 'unique' in error_msg:
                if 'numero_factura' in error_msg:
                    return {
                        'success': False,
                        'message': 'El número de factura ya existe. Por favor ingrese un número diferente.'
                    }
            
            return {
                'success': False,
                'message': f'Error al crear venta: {str(e)}'
            }
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.db.return_connection(connection)
    
    def anular(self, id_venta: int, id_empleado: int) -> Dict[str, Any]:
        """
        Anula una venta y revierte el stock.
        
        Proceso:
        1. Obtener detalles de la venta
        2. SUMAR el stock de vuelta (revertir la resta)
        3. Marcar venta como anulada
        4. Registrar movimiento de caja (egreso negativo)
        
        Args:
            id_venta: ID de la venta a anular
            id_empleado: ID del empleado que anula
        
        Returns:
            Dict con success y mensaje
        """
        connection = None
        cursor = None
        
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # Verificar que la venta existe y no está ya anulada
            cursor.execute("""
                SELECT estado, total, id_caja, numero_factura, id_cliente
                FROM ventas 
                WHERE id_venta = %s
            """, (id_venta,))
            
            venta_data = cursor.fetchone()
            if not venta_data:
                return {'success': False, 'message': 'Venta no encontrada'}
            
            estado_actual, total, id_caja, numero_factura, id_cliente = venta_data
            
            if estado_actual == 'anulada':
                return {'success': False, 'message': 'La venta ya está anulada'}
            
            # Obtener detalles de la venta
            cursor.execute("""
                SELECT id_producto, cantidad
                FROM detalle_ventas
                WHERE id_venta = %s
            """, (id_venta,))
            
            detalles = cursor.fetchall()
            
            # Revertir stock (SUMAR de vuelta)
            for id_producto, cantidad in detalles:
                cursor.execute("""
                    UPDATE productos
                    SET stock_actual = stock_actual + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id_producto = %s
                """, (cantidad, id_producto))
            
            # Marcar venta como anulada
            cursor.execute("""
                UPDATE ventas
                SET estado = 'anulada',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_venta = %s
            """, (id_venta,))
            
            # Registrar movimiento de caja (EGRESO por devolución)
            cursor.execute("""
                INSERT INTO movimientos_caja (
                    id_caja, tipo, concepto, monto,
                    fecha_movimiento, id_empleado, observaciones
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_caja,
                'egreso',
                f'Anulación de venta - Factura {numero_factura}',
                total,
                datetime.now(),
                id_empleado,
                f'Venta anulada, se revirtió el stock'
            ))
            
            # Actualizar totales de caja (restar de ventas, sumar a egresos)
            cursor.execute("""
                UPDATE cajas
                SET total_ventas = total_ventas - %s,
                    total_egresos = total_egresos + %s
                WHERE id_caja = %s
            """, (total, total, id_caja))
            
            # Actualizar total_compras del cliente (si tiene cliente)
            if id_cliente:
                cursor.execute("""
                    UPDATE clientes
                    SET total_compras = GREATEST(total_compras - %s, 0),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id_cliente = %s
                """, (total, id_cliente))
            
            connection.commit()
            
            return {
                'success': True,
                'message': 'Venta anulada exitosamente. Stock revertido.'
            }
            
        except Exception as e:
            if connection:
                connection.rollback()
            return {
                'success': False,
                'message': f'Error al anular venta: {str(e)}'
            }
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.db.return_connection(connection)
    
    def obtener_por_id(self, id_venta: int) -> Optional[Venta]:
        """
        Obtiene una venta por su ID con sus detalles.
        
        Args:
            id_venta: ID de la venta
        
        Returns:
            Objeto Venta con detalles o None
        """
        connection = None
        cursor = None
        
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # Obtener venta con datos relacionados
            cursor.execute("""
                SELECT 
                    v.id_venta, v.numero_factura, v.id_cliente, v.id_empleado,
                    v.id_caja, v.fecha_venta, v.subtotal, v.descuento,
                    v.total, v.metodo_pago, v.estado, v.observaciones,
                    v.created_at, v.updated_at,
                    COALESCE(CONCAT(pc.nombre, ' ', pc.apellido), 'Sin cliente') as cliente_nombre,
                    CONCAT(pe.nombre, ' ', pe.apellido) as empleado_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN personas pc ON c.id_persona = pc.id_persona
                LEFT JOIN empleados e ON v.id_empleado = e.id_empleado
                LEFT JOIN personas pe ON e.id_persona = pe.id_persona
                WHERE v.id_venta = %s
            """, (id_venta,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Crear objeto venta
            venta = Venta(
                id_venta=row[0],
                numero_factura=row[1],
                id_cliente=row[2],
                id_empleado=row[3],
                id_caja=row[4],
                fecha_venta=row[5],
                subtotal=float(row[6]),
                descuento=float(row[7]),
                total=float(row[8]),
                metodo_pago=row[9],
                estado=row[10],
                observaciones=row[11],
                created_at=row[12],
                updated_at=row[13],
                cliente_nombre=row[14],
                empleado_nombre=row[15]
            )
            
            # Obtener detalles
            cursor.execute("""
                SELECT 
                    dv.id_detalle_venta, dv.id_venta, dv.id_producto,
                    dv.cantidad, dv.precio_unitario, dv.subtotal,
                    dv.created_at,
                    p.codigo as producto_codigo,
                    p.nombre as producto_nombre
                FROM detalle_ventas dv
                JOIN productos p ON dv.id_producto = p.id_producto
                WHERE dv.id_venta = %s
                ORDER BY dv.id_detalle_venta
            """, (id_venta,))
            
            detalles_rows = cursor.fetchall()
            for detalle_row in detalles_rows:
                detalle = DetalleVenta(
                    id_detalle_venta=detalle_row[0],
                    id_venta=detalle_row[1],
                    id_producto=detalle_row[2],
                    cantidad=detalle_row[3],
                    precio_unitario=float(detalle_row[4]),
                    subtotal=float(detalle_row[5]),
                    created_at=detalle_row[6],
                    producto_codigo=detalle_row[7],
                    producto_nombre=detalle_row[8]
                )
                venta.detalles.append(detalle)
            
            return venta
            
        except Exception as e:
            print(f"Error al obtener venta: {e}")
            return None
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.db.return_connection(connection)
    
    def obtener_ultima_factura(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último número de factura registrado.
        
        Returns:
            Dict con numero_factura o None si no hay ventas
        """
        connection = None
        cursor = None
        
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT numero_factura
                FROM ventas
                ORDER BY id_venta DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return {'numero_factura': row[0]}
            return None
            
        except Exception as e:
            print(f"Error al obtener última factura: {e}")
            return None
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.db.return_connection(connection)
    
    def listar(
        self, 
        limit: int = 10,
        offset: int = 0,
        busqueda: Optional[str] = None,
        estado: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_cliente: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista ventas con filtros y paginación.
        
        Args:
            limit: Registros por página
            offset: Offset para paginación
            busqueda: Buscar por número de factura o nombre de cliente
            estado: Filtrar por estado (completada, anulada)
            fecha_inicio: Filtrar desde fecha
            fecha_fin: Filtrar hasta fecha
            id_cliente: Filtrar por cliente
        
        Returns:
            Dict con 'ventas' (lista) y 'total' (int)
        """
        connection = None
        cursor = None
        
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # Construir WHERE dinámico
            condiciones = ["1=1"]
            parametros = []
            
            if busqueda:
                condiciones.append("""(
                    v.numero_factura ILIKE %s OR
                    CONCAT(pc.nombre, ' ', pc.apellido) ILIKE %s
                )""")
                parametros.extend([f'%{busqueda}%', f'%{busqueda}%'])
            
            if estado:
                condiciones.append("v.estado = %s")
                parametros.append(estado)
            
            if fecha_inicio:
                condiciones.append("DATE(v.fecha_venta) >= %s")
                parametros.append(fecha_inicio)
            
            if fecha_fin:
                condiciones.append("DATE(v.fecha_venta) <= %s")
                parametros.append(fecha_fin)
            
            if id_cliente:
                condiciones.append("v.id_cliente = %s")
                parametros.append(id_cliente)
            
            where_clause = " AND ".join(condiciones)
            
            # Contar total
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM ventas v
                LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN personas pc ON c.id_persona = pc.id_persona
                WHERE {where_clause}
            """, parametros)
            
            total = cursor.fetchone()[0]
            
            # Obtener registros de la página
            parametros.extend([limit, offset])
            
            cursor.execute(f"""
                SELECT 
                    v.id_venta, v.numero_factura, v.id_cliente, v.id_empleado,
                    v.id_caja, v.fecha_venta, v.subtotal, v.descuento,
                    v.total, v.metodo_pago, v.estado, v.observaciones,
                    v.created_at, v.updated_at,
                    COALESCE(CONCAT(pc.nombre, ' ', pc.apellido), 'Sin cliente') as cliente_nombre,
                    CONCAT(pe.nombre, ' ', pe.apellido) as empleado_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN personas pc ON c.id_persona = pc.id_persona
                LEFT JOIN empleados e ON v.id_empleado = e.id_empleado
                LEFT JOIN personas pe ON e.id_persona = pe.id_persona
                WHERE {where_clause}
                ORDER BY v.fecha_venta DESC, v.id_venta DESC
                LIMIT %s OFFSET %s
            """, parametros)
            
            ventas = []
            for row in cursor.fetchall():
                venta = Venta(
                    id_venta=row[0],
                    numero_factura=row[1],
                    id_cliente=row[2],
                    id_empleado=row[3],
                    id_caja=row[4],
                    fecha_venta=row[5],
                    subtotal=float(row[6]),
                    descuento=float(row[7]),
                    total=float(row[8]),
                    metodo_pago=row[9],
                    estado=row[10],
                    observaciones=row[11],
                    created_at=row[12],
                    updated_at=row[13],
                    cliente_nombre=row[14],
                    empleado_nombre=row[15]
                )
                ventas.append(venta)
            
            return {
                'ventas': ventas,
                'total': total
            }
            
        except Exception as e:
            print(f"Error al listar ventas: {e}")
            return {
                'ventas': [],
                'total': 0
            }
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.db.return_connection(connection)
