"""
Servicio para gestión de cajas (apertura, cierre, movimientos)
"""
from datetime import datetime
from typing import Optional, Dict, List, Any
from database.connection import DatabaseConnection


class CajaService:
    """Servicio para operaciones relacionadas con cajas"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def obtener_caja_actual(self, id_empleado: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la caja actualmente abierta para un empleado
        
        Args:
            id_empleado: ID del empleado
            
        Returns:
            Dict con información de la caja abierta o None si no hay caja abierta
        """
        query = """
            SELECT 
                c.id_caja,
                c.id_empleado,
                c.fecha_apertura,
                c.monto_inicial,
                c.estado,
                p.nombre || ' ' || p.apellido as nombre_empleado
            FROM cajas c
            INNER JOIN empleados emp ON c.id_empleado = emp.id_empleado
            INNER JOIN personas p ON emp.id_persona = p.id_persona
            WHERE c.id_empleado = %s 
              AND c.estado = 'abierta'
              AND c.fecha_cierre IS NULL
            ORDER BY c.fecha_apertura DESC
            LIMIT 1
        """
        
        result = self.db.execute_query(query, (id_empleado,), fetch='one')
        return result
    
    def verificar_caja_abierta(self, id_empleado: int) -> Dict[str, Any]:
        """
        Verifica si hay una caja abierta para el empleado
        
        Args:
            id_empleado: ID del empleado
            
        Returns:
            Dict con 'success' (bool), 'message' (str), 'caja' (dict si success=True)
        """
        caja = self.obtener_caja_actual(id_empleado)
        if caja:
            return {
                'success': True,
                'message': 'Caja abierta encontrada',
                'caja': caja
            }
        else:
            return {
                'success': False,
                'message': 'No hay caja abierta. Debe abrir una caja antes de realizar ventas.'
            }
    
    def abrir_caja(self, id_empleado: int, monto_inicial: float, observaciones: str = "") -> Dict[str, Any]:
        """
        Abre una nueva caja para el empleado
        
        Args:
            id_empleado: ID del empleado que abre la caja
            monto_inicial: Monto inicial con el que se abre la caja
            observaciones: Observaciones opcionales
            
        Returns:
            Dict con 'success' (bool), 'message' (str), 'id_caja' (int si success=True)
        """
        try:
            # Verificar que no haya una caja abierta
            resultado = self.verificar_caja_abierta(id_empleado)
            if resultado['success']:
                return {
                    'success': False,
                    'message': 'Ya existe una caja abierta para este empleado'
                }
            
            # Insertar nueva caja
            query = """
                INSERT INTO cajas 
                    (id_empleado, fecha_apertura, monto_inicial, estado, observaciones)
                VALUES 
                    (%s, CURRENT_TIMESTAMP, %s, 'abierta', %s)
                RETURNING id_caja, fecha_apertura
            """
            
            result = self.db.execute_query(
                query, 
                (id_empleado, monto_inicial, observaciones),
                fetch='one'
            )
            
            if result:
                # Registrar el movimiento inicial
                self.registrar_movimiento(
                    id_caja=result['id_caja'],
                    tipo='ingreso',
                    monto=monto_inicial,
                    concepto='Apertura de caja - Monto inicial',
                    id_empleado=id_empleado
                )
                
                return {
                    'success': True,
                    'message': 'Caja abierta exitosamente',
                    'id_caja': result['id_caja'],
                    'fecha_apertura': result['fecha_apertura']
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al abrir la caja'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al abrir caja: {str(e)}'
            }
    
    def cerrar_caja(self, id_caja: int, monto_final: float, observaciones: str = "") -> Dict[str, Any]:
        """
        Cierra una caja existente
        
        Args:
            id_caja: ID de la caja a cerrar
            monto_final: Monto final contado en caja
            observaciones: Observaciones del cierre
            
        Returns:
            Dict con 'success' (bool), 'message' (str), 'diferencia' (float si success=True)
        """
        try:
            # Obtener información de la caja
            caja_info = self.obtener_resumen_caja(id_caja)
            
            if not caja_info:
                return {
                    'success': False,
                    'message': 'Caja no encontrada'
                }
            
            if caja_info['estado'] == 'cerrada':
                return {
                    'success': False,
                    'message': 'La caja ya está cerrada'
                }
            
            # Calcular diferencia
            monto_esperado = float(caja_info['total_calculado'])
            diferencia = float(monto_final) - monto_esperado
            
            # Actualizar caja
            query = """
                UPDATE cajas 
                SET 
                    fecha_cierre = CURRENT_TIMESTAMP,
                    monto_final = %s,
                    diferencia = %s,
                    estado = 'cerrada',
                    observaciones = CASE 
                        WHEN observaciones IS NULL OR observaciones = '' THEN %s
                        ELSE observaciones || ' | CIERRE: ' || %s
                    END
                WHERE id_caja = %s
                RETURNING fecha_cierre
            """
            
            result = self.db.execute_query(
                query,
                (monto_final, diferencia, observaciones, observaciones, id_caja),
                fetch='one'
            )
            
            if result:
                return {
                    'success': True,
                    'message': 'Caja cerrada exitosamente',
                    'diferencia': diferencia,
                    'monto_esperado': monto_esperado,
                    'monto_final': monto_final,
                    'fecha_cierre': result['fecha_cierre']
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al cerrar la caja'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al cerrar caja: {str(e)}'
            }
    
    def obtener_resumen_caja(self, id_caja: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el resumen completo de una caja (ingresos, egresos, total)
        
        Args:
            id_caja: ID de la caja
            
        Returns:
            Dict con resumen de la caja
        """
        query = """
            SELECT 
                c.id_caja,
                c.id_empleado,
                c.fecha_apertura,
                c.fecha_cierre,
                c.monto_inicial,
                c.monto_final,
                c.diferencia,
                c.estado,
                c.observaciones,
                p.nombre || ' ' || p.apellido as nombre_empleado,
                COALESCE(SUM(CASE WHEN m.tipo = 'ingreso' THEN m.monto ELSE 0 END), 0) as total_ingresos,
                COALESCE(SUM(CASE WHEN m.tipo = 'egreso' THEN m.monto ELSE 0 END), 0) as total_egresos,
                COALESCE(SUM(CASE WHEN m.tipo = 'ingreso' THEN m.monto ELSE -m.monto END), 0) as total_calculado,
                COUNT(m.id_movimiento) as total_movimientos
            FROM cajas c
            INNER JOIN empleados emp ON c.id_empleado = emp.id_empleado
            INNER JOIN personas p ON emp.id_persona = p.id_persona
            LEFT JOIN movimientos_caja m ON c.id_caja = m.id_caja
            WHERE c.id_caja = %s
            GROUP BY 
                c.id_caja, c.id_empleado, c.fecha_apertura, c.fecha_cierre,
                c.monto_inicial, c.monto_final, c.diferencia, c.estado,
                c.observaciones, p.nombre, p.apellido
        """
        
        result = self.db.execute_query(query, (id_caja,), fetch='one')
        return result
    
    def registrar_movimiento(
        self, 
        id_caja: int, 
        tipo: str, 
        monto: float, 
        concepto: str,
        id_empleado: int
    ) -> Dict[str, Any]:
        """
        Registra un movimiento de caja (ingreso o egreso)
        
        Args:
            id_caja: ID de la caja
            tipo: 'ingreso' o 'egreso'
            monto: Monto del movimiento
            concepto: Concepto del movimiento
            id_empleado: ID del empleado que realiza el movimiento
            
        Returns:
            Dict con 'success' (bool), 'message' (str), 'id_movimiento' (int si success=True)
        """
        try:
            query = """
                INSERT INTO movimientos_caja 
                    (id_caja, tipo, monto, concepto, id_empleado)
                VALUES 
                    (%s, %s, %s, %s, %s)
                RETURNING id_movimiento, fecha_movimiento
            """
            
            result = self.db.execute_query(
                query,
                (id_caja, tipo, monto, concepto, id_empleado),
                fetch='one'
            )
            
            if result:
                return {
                    'success': True,
                    'message': 'Movimiento registrado exitosamente',
                    'id_movimiento': result['id_movimiento'],
                    'fecha_movimiento': result['fecha_movimiento']
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al registrar el movimiento'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al registrar movimiento: {str(e)}'
            }
    
    def obtener_movimientos_caja(self, id_caja: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los movimientos de una caja
        
        Args:
            id_caja: ID de la caja
            
        Returns:
            Lista de movimientos
        """
        query = """
            SELECT 
                m.id_movimiento,
                m.tipo,
                m.monto,
                m.descripcion,
                m.fecha_movimiento,
                m.id_venta,
                m.id_compra,
                p.nombre || ' ' || p.apellido as empleado
            FROM movimientos_caja m
            INNER JOIN empleados emp ON m.id_empleado = emp.id_empleado
            INNER JOIN personas p ON emp.id_persona = p.id_persona
            WHERE m.id_caja = %s
            ORDER BY m.fecha_movimiento ASC
        """
        
        result = self.db.execute_query(query, (id_caja,), fetch='all')
        return result if result else []
    
    def obtener_historial_cajas(self, id_empleado: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de cajas
        
        Args:
            id_empleado: Filtrar por empleado (opcional)
            limit: Cantidad máxima de resultados
            
        Returns:
            Lista de cajas
        """
        if id_empleado:
            query = """
                SELECT 
                    c.id_caja,
                    c.fecha_apertura,
                    c.fecha_cierre,
                    c.monto_inicial,
                    c.monto_final,
                    c.diferencia,
                    c.estado,
                    p.nombre || ' ' || p.apellido as nombre_empleado
                FROM cajas c
                INNER JOIN empleados emp ON c.id_empleado = emp.id_empleado
                INNER JOIN personas p ON emp.id_persona = p.id_persona
                WHERE c.id_empleado = %s
                ORDER BY c.fecha_apertura DESC
                LIMIT %s
            """
            params = (id_empleado, limit)
        else:
            query = """
                SELECT 
                    c.id_caja,
                    c.fecha_apertura,
                    c.fecha_cierre,
                    c.monto_inicial,
                    c.monto_final,
                    c.diferencia,
                    c.estado,
                    p.nombre || ' ' || p.apellido as nombre_empleado
                FROM cajas c
                INNER JOIN empleados emp ON c.id_empleado = emp.id_empleado
                INNER JOIN personas p ON emp.id_persona = p.id_persona
                ORDER BY c.fecha_apertura DESC
                LIMIT %s
            """
            params = (limit,)
        
        result = self.db.execute_query(query, params, fetch='all')
        return result if result else []
