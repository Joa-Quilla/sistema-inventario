"""
Modelo de Caja para el sistema de inventario.
Representa las cajas (turnos) con sus movimientos de ingreso/egreso.
"""
from datetime import datetime
from typing import Optional, Dict, Any


class Caja:
    """
    Modelo de Caja.
    
    Attributes:
        id_caja: Identificador único de la caja
        id_empleado: ID del empleado responsable
        fecha_apertura: Fecha y hora de apertura
        fecha_cierre: Fecha y hora de cierre (None si está abierta)
        monto_inicial: Monto con el que se abre la caja
        monto_final: Monto al cerrar (calculado)
        total_ventas: Total de ventas realizadas
        total_ingresos: Total de ingresos adicionales
        total_egresos: Total de egresos
        diferencia: Diferencia entre esperado y real
        estado: Estado de la caja (abierta, cerrada)
        observaciones: Observaciones generales
        created_at: Fecha de creación del registro
    """
    
    def __init__(
        self,
        id_empleado: int,
        monto_inicial: float,
        id_caja: Optional[int] = None,
        fecha_apertura: Optional[datetime] = None,
        fecha_cierre: Optional[datetime] = None,
        monto_final: Optional[float] = None,
        total_ventas: float = 0.0,
        total_ingresos: float = 0.0,
        total_egresos: float = 0.0,
        diferencia: Optional[float] = None,
        estado: str = "abierta",
        observaciones: Optional[str] = None,
        created_at: Optional[datetime] = None,
        # Campos denormalizados para display
        nombre_empleado: Optional[str] = None
    ):
        self.id_caja = id_caja
        self.id_empleado = id_empleado
        self.fecha_apertura = fecha_apertura or datetime.now()
        self.fecha_cierre = fecha_cierre
        self.monto_inicial = monto_inicial
        self.monto_final = monto_final
        self.total_ventas = total_ventas
        self.total_ingresos = total_ingresos
        self.total_egresos = total_egresos
        self.diferencia = diferencia
        self.estado = estado
        self.observaciones = observaciones
        self.created_at = created_at or datetime.now()
        
        # Campos para visualización
        self.nombre_empleado = nombre_empleado
    
    def calcular_monto_esperado(self) -> float:
        """Calcula el monto esperado al cierre"""
        return self.monto_inicial + self.total_ventas + self.total_ingresos - self.total_egresos
    
    def calcular_diferencia(self, monto_real: float) -> float:
        """Calcula la diferencia entre monto real y esperado"""
        monto_esperado = self.calcular_monto_esperado()
        return monto_real - monto_esperado
    
    def validar(self) -> tuple[bool, str]:
        """Valida los datos de la caja."""
        if not self.id_empleado:
            return False, "El empleado es requerido"
        
        if self.monto_inicial < 0:
            return False, "El monto inicial no puede ser negativo"
        
        if self.estado not in ["abierta", "cerrada"]:
            return False, "Estado inválido"
        
        return True, "OK"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario."""
        return {
            "id_caja": self.id_caja,
            "id_empleado": self.id_empleado,
            "fecha_apertura": self.fecha_apertura.isoformat() if isinstance(self.fecha_apertura, datetime) else self.fecha_apertura,
            "fecha_cierre": self.fecha_cierre.isoformat() if isinstance(self.fecha_cierre, datetime) else self.fecha_cierre,
            "monto_inicial": float(self.monto_inicial),
            "monto_final": float(self.monto_final) if self.monto_final is not None else None,
            "total_ventas": float(self.total_ventas),
            "total_ingresos": float(self.total_ingresos),
            "total_egresos": float(self.total_egresos),
            "diferencia": float(self.diferencia) if self.diferencia is not None else None,
            "estado": self.estado,
            "observaciones": self.observaciones,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "nombre_empleado": self.nombre_empleado
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Caja':
        """Crea una instancia desde un diccionario."""
        # Convertir strings a datetime si es necesario
        fecha_apertura = data.get('fecha_apertura')
        if isinstance(fecha_apertura, str):
            fecha_apertura = datetime.fromisoformat(fecha_apertura.replace('Z', '+00:00'))
        
        fecha_cierre = data.get('fecha_cierre')
        if isinstance(fecha_cierre, str):
            fecha_cierre = datetime.fromisoformat(fecha_cierre.replace('Z', '+00:00'))
        
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return Caja(
            id_caja=data.get('id_caja'),
            id_empleado=data['id_empleado'],
            fecha_apertura=fecha_apertura,
            fecha_cierre=fecha_cierre,
            monto_inicial=float(data['monto_inicial']),
            monto_final=float(data['monto_final']) if data.get('monto_final') is not None else None,
            total_ventas=float(data.get('total_ventas', 0)),
            total_ingresos=float(data.get('total_ingresos', 0)),
            total_egresos=float(data.get('total_egresos', 0)),
            diferencia=float(data['diferencia']) if data.get('diferencia') is not None else None,
            estado=data.get('estado', 'abierta'),
            observaciones=data.get('observaciones'),
            created_at=created_at,
            nombre_empleado=data.get('nombre_empleado')
        )
    
    def __repr__(self) -> str:
        return f"Caja(id={self.id_caja}, empleado={self.id_empleado}, estado={self.estado}, monto_inicial={self.monto_inicial})"


class MovimientoCaja:
    """
    Modelo de Movimiento de Caja.
    Representa cada ingreso o egreso en una caja.
    """
    
    def __init__(
        self,
        id_caja: int,
        tipo: str,
        concepto: str,
        monto: float,
        id_empleado: int,
        id_movimiento: Optional[int] = None,
        fecha_movimiento: Optional[datetime] = None,
        observaciones: Optional[str] = None,
        created_at: Optional[datetime] = None,
        # Campos denormalizados
        empleado_nombre: Optional[str] = None
    ):
        self.id_movimiento = id_movimiento
        self.id_caja = id_caja
        self.tipo = tipo  # 'ingreso' o 'egreso'
        self.concepto = concepto
        self.monto = monto
        self.id_empleado = id_empleado
        self.fecha_movimiento = fecha_movimiento or datetime.now()
        self.observaciones = observaciones
        self.created_at = created_at or datetime.now()
        
        # Para visualización
        self.empleado_nombre = empleado_nombre
    
    def validar(self) -> tuple[bool, str]:
        """Valida los datos del movimiento."""
        if not self.id_caja:
            return False, "La caja es requerida"
        
        if self.tipo not in ['ingreso', 'egreso']:
            return False, "Tipo de movimiento inválido"
        
        if not self.concepto or not self.concepto.strip():
            return False, "El concepto es requerido"
        
        if self.monto <= 0:
            return False, "El monto debe ser mayor a 0"
        
        if not self.id_empleado:
            return False, "El empleado es requerido"
        
        return True, "OK"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario."""
        return {
            "id_movimiento": self.id_movimiento,
            "id_caja": self.id_caja,
            "tipo": self.tipo,
            "concepto": self.concepto,
            "monto": float(self.monto),
            "id_empleado": self.id_empleado,
            "fecha_movimiento": self.fecha_movimiento.isoformat() if isinstance(self.fecha_movimiento, datetime) else self.fecha_movimiento,
            "observaciones": self.observaciones,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "empleado_nombre": self.empleado_nombre
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MovimientoCaja':
        """Crea una instancia desde un diccionario."""
        fecha_movimiento = data.get('fecha_movimiento')
        if isinstance(fecha_movimiento, str):
            fecha_movimiento = datetime.fromisoformat(fecha_movimiento.replace('Z', '+00:00'))
        
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return MovimientoCaja(
            id_movimiento=data.get('id_movimiento'),
            id_caja=data['id_caja'],
            tipo=data['tipo'],
            concepto=data['concepto'],
            monto=float(data['monto']),
            id_empleado=data['id_empleado'],
            fecha_movimiento=fecha_movimiento,
            observaciones=data.get('observaciones'),
            created_at=created_at,
            empleado_nombre=data.get('empleado_nombre')
        )
    
    def __repr__(self) -> str:
        return f"MovimientoCaja(id={self.id_movimiento}, tipo={self.tipo}, monto={self.monto}, concepto={self.concepto})"
