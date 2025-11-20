"""
Modelos para Venta y DetalleVenta alineados con el schema de BD
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class DetalleVenta:
    """
    Modelo para detalle de ventas (productos vendidos).
    Corresponde a la tabla detalle_ventas de la BD.
    """
    
    id_detalle_venta: Optional[int] = None  # PK de detalle_ventas
    id_venta: Optional[int] = None
    id_producto: Optional[int] = None
    cantidad: int = 0
    precio_unitario: float = 0.0
    subtotal: float = 0.0  # cantidad * precio_unitario (sin descuento en detalle)
    created_at: Optional[datetime] = None
    
    # Datos del producto (denormalizados para display)
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None
    
    def calcular_subtotal(self):
        """Calcula y asigna el subtotal del detalle"""
        self.subtotal = self.cantidad * self.precio_unitario
    
    def validar(self) -> tuple[bool, str]:
        """Valida los datos del detalle"""
        if not self.id_producto:
            return False, "Debe seleccionar un producto"
        
        if self.cantidad <= 0:
            return False, "La cantidad debe ser mayor a cero"
        
        if self.precio_unitario <= 0:
            return False, "El precio unitario debe ser mayor a cero"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        return {
            'id_detalle_venta': self.id_detalle_venta,
            'id_venta': self.id_venta,
            'id_producto': self.id_producto,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'subtotal': self.subtotal,
            'created_at': self.created_at,
            'producto_codigo': self.producto_codigo,
            'producto_nombre': self.producto_nombre
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DetalleVenta':
        """Crea una instancia desde un diccionario"""
        return cls(
            id_detalle_venta=data.get('id_detalle_venta'),
            id_venta=data.get('id_venta'),
            id_producto=data.get('id_producto'),
            cantidad=data.get('cantidad', 0),
            precio_unitario=data.get('precio_unitario', 0.0),
            subtotal=data.get('subtotal', 0.0),
            created_at=data.get('created_at'),
            producto_codigo=data.get('producto_codigo'),
            producto_nombre=data.get('producto_nombre')
        )


@dataclass
class Venta:
    """
    Modelo para ventas.
    Corresponde a la tabla ventas de la BD.
    """
    
    id_venta: Optional[int] = None
    numero_factura: str = ""  # UNIQUE NOT NULL en BD
    id_cliente: Optional[int] = None  # Puede ser NULL (venta sin cliente)
    id_empleado: Optional[int] = None
    id_caja: Optional[int] = None
    fecha_venta: Optional[datetime] = None
    subtotal: float = 0.0  # Suma de subtotales de detalles
    descuento: float = 0.0  # Descuento aplicado (por cliente o manual)
    total: float = 0.0  # subtotal - descuento (sin impuesto en BD)
    metodo_pago: str = "efectivo"  # efectivo, tarjeta, transferencia, credito
    estado: str = "completada"  # completada, anulada
    observaciones: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Datos relacionados (denormalizados para display)
    cliente_nombre: Optional[str] = None
    empleado_nombre: Optional[str] = None
    
    # Detalles de la venta
    detalles: List[DetalleVenta] = field(default_factory=list)
    
    def calcular_totales(self):
        """Calcula los totales de la venta basándose en los detalles"""
        self.subtotal = sum(detalle.subtotal for detalle in self.detalles)
        self.total = self.subtotal - self.descuento
    
    def agregar_detalle(self, detalle: DetalleVenta):
        """Agrega un detalle a la venta y recalcula totales"""
        detalle.calcular_subtotal()
        self.detalles.append(detalle)
        self.calcular_totales()
    
    def validar(self) -> tuple[bool, str]:
        """Valida los datos de la venta"""
        if not self.numero_factura or not self.numero_factura.strip():
            return False, "El número de factura es requerido"
        
        if not self.id_empleado:
            return False, "Debe seleccionar un empleado"
        
        if not self.detalles:
            return False, "Debe agregar al menos un producto"
        
        # Validar cada detalle
        for i, detalle in enumerate(self.detalles, 1):
            es_valido, mensaje = detalle.validar()
            if not es_valido:
                return False, f"Producto #{i}: {mensaje}"
        
        if self.subtotal <= 0:
            return False, "El subtotal debe ser mayor a cero"
        
        if self.descuento < 0:
            return False, "El descuento no puede ser negativo"
        
        if self.descuento > self.subtotal:
            return False, "El descuento no puede ser mayor al subtotal"
        
        if self.total <= 0:
            return False, "El total debe ser mayor a cero"
        
        if self.metodo_pago not in ["efectivo", "tarjeta", "transferencia", "credito"]:
            return False, "Método de pago inválido"
        
        if self.estado not in ["completada", "anulada"]:
            return False, "Estado inválido"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        return {
            'id_venta': self.id_venta,
            'numero_factura': self.numero_factura,
            'id_cliente': self.id_cliente,
            'id_empleado': self.id_empleado,
            'id_caja': self.id_caja,
            'fecha_venta': self.fecha_venta,
            'subtotal': self.subtotal,
            'descuento': self.descuento,
            'total': self.total,
            'metodo_pago': self.metodo_pago,
            'estado': self.estado,
            'observaciones': self.observaciones,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'cliente_nombre': self.cliente_nombre,
            'empleado_nombre': self.empleado_nombre,
            'detalles': [detalle.to_dict() for detalle in self.detalles]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Venta':
        """Crea una instancia desde un diccionario"""
        detalles = []
        if 'detalles' in data:
            detalles = [DetalleVenta.from_dict(d) for d in data['detalles']]
        
        return cls(
            id_venta=data.get('id_venta'),
            numero_factura=data.get('numero_factura', ''),
            id_cliente=data.get('id_cliente'),
            id_empleado=data.get('id_empleado'),
            id_caja=data.get('id_caja'),
            fecha_venta=data.get('fecha_venta'),
            subtotal=data.get('subtotal', 0.0),
            descuento=data.get('descuento', 0.0),
            total=data.get('total', 0.0),
            metodo_pago=data.get('metodo_pago', 'efectivo'),
            estado=data.get('estado', 'completada'),
            observaciones=data.get('observaciones'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            cliente_nombre=data.get('cliente_nombre'),
            empleado_nombre=data.get('empleado_nombre'),
            detalles=detalles
        )

