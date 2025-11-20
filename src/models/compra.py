"""
Modelos para Compra y DetalleCompra
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class DetalleCompra:
    """Modelo para detalle de compras (productos comprados)"""
    
    id_detalle_compra: Optional[int] = None
    id_compra: Optional[int] = None
    id_producto: Optional[int] = None
    cantidad: int = 0
    precio_unitario: float = 0.0
    subtotal: float = 0.0
    created_at: Optional[datetime] = None
    
    # Datos del producto (denormalizados para mostrar en vistas)
    codigo_producto: Optional[str] = None
    nombre_producto: Optional[str] = None
    
    @property
    def total(self) -> float:
        """Calcula el total del detalle"""
        return self.cantidad * self.precio_unitario
    
    def calcular_subtotal(self):
        """Calcula y asigna el subtotal"""
        self.subtotal = self.total
    
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
            'id_detalle_compra': self.id_detalle_compra,
            'id_compra': self.id_compra,
            'id_producto': self.id_producto,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'subtotal': self.subtotal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'codigo_producto': self.codigo_producto,
            'nombre_producto': self.nombre_producto
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DetalleCompra':
        """Crea una instancia desde un diccionario"""
        # Parsear created_at
        created_at = None
        if data.get('created_at'):
            val = data['created_at']
            if isinstance(val, datetime):
                created_at = val
            elif isinstance(val, str):
                created_at = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        return cls(
            id_detalle_compra=data.get('id_detalle_compra'),
            id_compra=data.get('id_compra'),
            id_producto=data.get('id_producto'),
            cantidad=int(data.get('cantidad', 0)),
            precio_unitario=float(data.get('precio_unitario', 0.0)),
            subtotal=float(data.get('subtotal', 0.0)),
            created_at=created_at,
            codigo_producto=data.get('codigo_producto') or data.get('codigo'),
            nombre_producto=data.get('nombre_producto') or data.get('nombre')
        )


@dataclass
class Compra:
    """Modelo para compras"""
    
    id_compra: Optional[int] = None
    numero_factura: Optional[str] = None
    id_proveedor: Optional[int] = None
    id_empleado: Optional[int] = None
    fecha_compra: Optional[datetime] = None
    total: float = 0.0
    estado: str = "completada"  # completada, pendiente, cancelada
    observaciones: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Datos relacionados (denormalizados para mostrar en vistas)
    nombre_proveedor: Optional[str] = None
    nombre_empleado: Optional[str] = None
    
    # Detalles de la compra
    detalles: List[DetalleCompra] = field(default_factory=list)
    
    def calcular_totales(self):
        """Calcula el total de la compra basándose en los detalles"""
        self.total = sum(detalle.subtotal for detalle in self.detalles)
    
    def agregar_detalle(self, detalle: DetalleCompra):
        """Agrega un detalle a la compra"""
        detalle.calcular_subtotal()
        self.detalles.append(detalle)
        self.calcular_totales()
    
    def validar(self) -> tuple[bool, str]:
        """Valida los datos de la compra"""
        if not self.id_proveedor:
            return False, "Debe seleccionar un proveedor"
        
        if not self.id_empleado:
            return False, "Debe seleccionar un empleado"
        
        if not self.detalles:
            return False, "Debe agregar al menos un producto"
        
        # Validar cada detalle
        for i, detalle in enumerate(self.detalles, 1):
            es_valido, mensaje = detalle.validar()
            if not es_valido:
                return False, f"Producto #{i}: {mensaje}"
        
        if self.total <= 0:
            return False, "El total debe ser mayor a cero"
        
        if self.estado not in ["completada", "pendiente", "cancelada"]:
            return False, "Estado inválido"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        return {
            'id_compra': self.id_compra,
            'numero_factura': self.numero_factura,
            'id_proveedor': self.id_proveedor,
            'id_empleado': self.id_empleado,
            'fecha_compra': self.fecha_compra.isoformat() if self.fecha_compra else None,
            'total': self.total,
            'estado': self.estado,
            'observaciones': self.observaciones,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'nombre_proveedor': self.nombre_proveedor,
            'nombre_empleado': self.nombre_empleado,
            'detalles': [detalle.to_dict() for detalle in self.detalles]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Compra':
        """Crea una instancia desde un diccionario"""
        # Parsear fecha_compra
        fecha_compra = None
        if data.get('fecha_compra'):
            val = data['fecha_compra']
            if isinstance(val, datetime):
                fecha_compra = val
            elif isinstance(val, str):
                fecha_compra = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        # Parsear created_at
        created_at = None
        if data.get('created_at'):
            val = data['created_at']
            if isinstance(val, datetime):
                created_at = val
            elif isinstance(val, str):
                created_at = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        # Parsear updated_at
        updated_at = None
        if data.get('updated_at'):
            val = data['updated_at']
            if isinstance(val, datetime):
                updated_at = val
            elif isinstance(val, str):
                updated_at = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        detalles = []
        if 'detalles' in data:
            detalles = [DetalleCompra.from_dict(d) for d in data['detalles']]
        
        return cls(
            id_compra=data.get('id_compra'),
            numero_factura=data.get('numero_factura'),
            id_proveedor=data.get('id_proveedor'),
            id_empleado=data.get('id_empleado'),
            fecha_compra=fecha_compra,
            total=float(data.get('total', 0)),
            estado=data.get('estado', 'completada'),
            observaciones=data.get('observaciones'),
            created_at=created_at,
            updated_at=updated_at,
            nombre_proveedor=data.get('nombre_proveedor'),
            nombre_empleado=data.get('nombre_empleado'),
            detalles=detalles
        )
