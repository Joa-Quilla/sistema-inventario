"""
Modelos del sistema de inventario
"""
from models.persona import Persona
from models.cliente import Cliente
from models.proveedor import Proveedor
from models.empleado import Empleado
from models.categoria import Categoria
from models.producto import Producto
from models.venta import Venta, DetalleVenta
from models.compra import Compra, DetalleCompra

__all__ = [
    'Persona',
    'Cliente',
    'Proveedor',
    'Empleado',
    'Categoria',
    'Producto',
    'Venta',
    'DetalleVenta',
    'Compra',
    'DetalleCompra'
]
