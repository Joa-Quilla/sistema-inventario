"""
Repositorios para acceso a datos
"""
from repositories.categoria_repository import CategoriaRepository
from repositories.producto_repository import ProductoRepository
from repositories.cliente_repository import ClienteRepository
from repositories.proveedor_repository import ProveedorRepository
from repositories.compra_repository import CompraRepository
from repositories.venta_repository import VentaRepository
from repositories.reporte_repository import ReporteRepository
from repositories.configuracion_repository import ConfiguracionRepository
from repositories.dashboard_repository import DashboardRepository

__all__ = [
    'CategoriaRepository',
    'ProductoRepository',
    'ClienteRepository',
    'ProveedorRepository',
    'CompraRepository',
    'VentaRepository',
    'ReporteRepository',
    'ConfiguracionRepository',
    'DashboardRepository'
]
