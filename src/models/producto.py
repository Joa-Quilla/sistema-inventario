"""
Modelo para Producto
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from models.categoria import Categoria


@dataclass
class Producto:
    """Modelo para productos del inventario - Coincide con BD"""
    
    # Campos que EXISTEN en la BD
    id_producto: Optional[int] = None
    id_categoria: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    descripcion: Optional[str] = None
    precio_compra: float = 0.0  # precio_costo en BD
    precio_venta: float = 0.0
    stock_actual: int = 0
    stock_minimo: int = 0
    unidad_medida: str = "unidad"
    lote: Optional[str] = None
    fecha_vencimiento: Optional[datetime] = None
    ubicacion: Optional[str] = None
    estado: str = "activo"  # Boolean en BD, pero manejamos como string
    fecha_creacion: Optional[datetime] = None  # created_at en BD
    fecha_actualizacion: Optional[datetime] = None  # updated_at en BD
    fecha_registro: Optional[datetime] = None  # fecha_registro en BD
    
    # Datos de categoría (denormalizados)
    categoria: Optional[Categoria] = None
    nombre_categoria: Optional[str] = None
    
    @property
    def margen_ganancia(self) -> float:
        """Calcula el margen de ganancia en porcentaje"""
        if self.precio_compra > 0:
            return ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        return 0.0
    
    def validar(self) -> tuple[bool, str]:
        """
        Valida los datos del producto
        
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if not self.codigo or not self.codigo.strip():
            return False, "El código del producto es obligatorio"
        
        if not self.nombre or not self.nombre.strip():
            return False, "El nombre del producto es obligatorio"
        
        if len(self.nombre) < 3:
            return False, "El nombre debe tener al menos 3 caracteres"
        
        if self.precio_compra < 0:
            return False, "El precio de compra no puede ser negativo"
        
        if self.precio_venta < 0:
            return False, "El precio de venta no puede ser negativo"
        
        if self.precio_venta < self.precio_compra:
            return False, "El precio de venta debe ser mayor o igual al precio de compra"
        
        if self.stock_actual < 0:
            return False, "El stock actual no puede ser negativo"
        
        if self.stock_minimo < 0:
            return False, "El stock mínimo no puede ser negativo"
        
        if self.estado not in ["activo", "inactivo", "descontinuado"]:
            return False, "Estado inválido"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        data = {
            'id_producto': self.id_producto,
            'id_categoria': self.id_categoria,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'unidad_medida': self.unidad_medida,
            'precio_compra': self.precio_compra,
            'precio_venta': self.precio_venta,
            'stock_actual': self.stock_actual,
            'stock_minimo': self.stock_minimo,
            'lote': self.lote,
            'fecha_vencimiento': self.fecha_vencimiento,
            'ubicacion': self.ubicacion,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion,
            'fecha_actualizacion': self.fecha_actualizacion,
            'fecha_registro': self.fecha_registro,
            'nombre_categoria': self.nombre_categoria
        }
        
        if self.categoria:
            data['categoria'] = self.categoria.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Producto':
        """Crea una instancia desde un diccionario"""
        categoria = None
        if 'categoria' in data:
            categoria = Categoria.from_dict(data['categoria'])
        
        return cls(
            id_producto=data.get('id_producto'),
            id_categoria=data.get('id_categoria'),
            codigo=data.get('codigo', ''),
            nombre=data.get('nombre', ''),
            descripcion=data.get('descripcion'),
            unidad_medida=data.get('unidad_medida', 'unidad'),
            precio_compra=data.get('precio_compra', 0.0),
            precio_venta=data.get('precio_venta', 0.0),
            stock_actual=data.get('stock_actual', 0),
            stock_minimo=data.get('stock_minimo', 0),
            lote=data.get('lote'),
            fecha_vencimiento=data.get('fecha_vencimiento'),
            ubicacion=data.get('ubicacion'),
            estado=data.get('estado', 'activo'),
            fecha_creacion=data.get('fecha_creacion'),
            fecha_actualizacion=data.get('fecha_actualizacion'),
            fecha_registro=data.get('fecha_registro'),
            categoria=categoria,
            nombre_categoria=data.get('nombre_categoria')
        )
