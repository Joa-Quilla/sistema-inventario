"""
Servicio de Reportes
Maneja la lógica de negocio para generación de reportes
"""
from datetime import date, datetime
from typing import Dict, Any
from repositories.reporte_repository import ReporteRepository


class ReporteService:
    """Servicio para gestión de reportes"""
    
    def __init__(self):
        self.repository = ReporteRepository()
    
    def generar_cierre_caja_diario(self, fecha: date) -> Dict[str, Any]:
        """
        Genera reporte de cierre de caja diario
        
        Args:
            fecha: Fecha del reporte
            
        Returns:
            Dict con el reporte generado
        """
        return self.repository.cierre_caja_diario(fecha)
    
    def generar_cierre_caja_mensual(self, año: int, mes: int) -> Dict[str, Any]:
        """
        Genera reporte de cierre de caja mensual
        
        Args:
            año: Año del reporte
            mes: Mes del reporte (1-12)
            
        Returns:
            Dict con el reporte generado
        """
        if mes < 1 or mes > 12:
            return {'success': False, 'message': 'El mes debe estar entre 1 y 12'}
        
        return self.repository.cierre_caja_mensual(año, mes)
    
    def generar_compras_por_periodo(self, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
        """
        Genera reporte de compras en un periodo
        
        Args:
            fecha_inicio: Fecha inicial
            fecha_fin: Fecha final
            
        Returns:
            Dict con el reporte generado
        """
        if fecha_inicio > fecha_fin:
            return {'success': False, 'message': 'La fecha inicial no puede ser mayor a la fecha final'}
        
        return self.repository.compras_por_periodo(fecha_inicio, fecha_fin)
    
    def generar_productos_y_existencias(self) -> Dict[str, Any]:
        """
        Genera reporte de productos y existencias
        
        Returns:
            Dict con el reporte generado
        """
        return self.repository.productos_y_existencias()
    
    def generar_cartera_clientes(self) -> Dict[str, Any]:
        """
        Genera reporte de cartera de clientes
        
        Returns:
            Dict con el reporte generado
        """
        return self.repository.cartera_clientes()
    
    def generar_cartera_proveedores(self) -> Dict[str, Any]:
        """
        Genera reporte de cartera de proveedores
        
        Returns:
            Dict con el reporte generado
        """
        return self.repository.cartera_proveedores()
    
    def generar_cartera_empleados(self) -> Dict[str, Any]:
        """
        Genera reporte de cartera de empleados
        
        Returns:
            Dict con el reporte generado
        """
        return self.repository.cartera_empleados()
