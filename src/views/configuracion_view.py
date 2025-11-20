"""
Vista de Configuración del Sistema
"""
import flet as ft
from utils.theme import VoltTheme
from services.configuracion_service import ConfiguracionService


class ConfiguracionView:
    """Vista para gestionar la configuración del sistema"""
    
    def __init__(self, page: ft.Page, empleado):
        self.page = page
        self.empleado = empleado
        self.service = ConfiguracionService()
        self.config_actual = {}
        
        # Campos del formulario
        self.nombre_empresa = None
        self.nit_empresa = None
        self.direccion_empresa = None
        self.telefono_empresa = None
        self.email_empresa = None
        self.iva = None
        self.moneda = None
        self.prefijo_factura = None
        self.stock_minimo = None
        self.dias_vencimiento = None
    
    def build(self):
        """Construye la vista de configuración"""
        
        # Cargar configuración actual
        self._cargar_configuracion()
        
        # Crear formulario
        formulario = self._crear_formulario()
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon("settings", size=32, color=VoltTheme.PRIMARY),
                        ft.Text(
                            "Configuración del Sistema",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=VoltTheme.TEXT_PRIMARY
                        )
                    ], spacing=12),
                    padding=VoltTheme.SPACING_LG,
                    bgcolor=VoltTheme.BG_SECONDARY,
                    border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
                ),
                
                # Contenido
                ft.Container(
                    content=formulario,
                    padding=VoltTheme.SPACING_LG,
                    expand=True
                )
            ], spacing=0, expand=True),
            bgcolor=VoltTheme.BG_PRIMARY,
            expand=True
        )
    
    def _cargar_configuracion(self):
        """Carga la configuración actual del sistema"""
        resultado = self.service.obtener_configuracion()
        if resultado['success']:
            self.config_actual = resultado['configuracion']
    
    def _crear_formulario(self):
        """Crea el formulario de configuración"""
        
        # Inicializar campos
        self.nombre_empresa = ft.TextField(
            label="Nombre de la Empresa",
            value=self.config_actual.get('nombre_empresa', {}).get('valor', ''),
            border_color=VoltTheme.BORDER_COLOR,
            width=400
        )
        
        self.nit_empresa = ft.TextField(
            label="NIT",
            value=self.config_actual.get('nit_empresa', {}).get('valor', ''),
            border_color=VoltTheme.BORDER_COLOR,
            width=400,
            hint_text="Ej: 12345678-9"
        )
        
        self.direccion_empresa = ft.TextField(
            label="Dirección",
            value=self.config_actual.get('direccion_empresa', {}).get('valor', ''),
            border_color=VoltTheme.BORDER_COLOR,
            width=400,
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        
        self.telefono_empresa = ft.TextField(
            label="Teléfono",
            value=self.config_actual.get('telefono_empresa', {}).get('valor', ''),
            border_color=VoltTheme.BORDER_COLOR,
            width=400,
            hint_text="Ej: 2222-2222"
        )
        
        self.email_empresa = ft.TextField(
            label="Email",
            value=self.config_actual.get('email_empresa', {}).get('valor', ''),
            border_color=VoltTheme.BORDER_COLOR,
            width=400,
            hint_text="info@empresa.com"
        )
        
        self.iva = ft.TextField(
            label="IVA (%)",
            value=self.config_actual.get('iva', {}).get('valor', '12'),
            border_color=VoltTheme.BORDER_COLOR,
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.moneda = ft.TextField(
            label="Símbolo de Moneda",
            value=self.config_actual.get('moneda', {}).get('valor', 'Q'),
            border_color=VoltTheme.BORDER_COLOR,
            width=200
        )
        
        self.prefijo_factura = ft.TextField(
            label="Prefijo de Factura",
            value=self.config_actual.get('prefijo_factura', {}).get('valor', 'FACT'),
            border_color=VoltTheme.BORDER_COLOR,
            width=200,
            hint_text="Ej: FACT, INV"
        )
        
        self.stock_minimo = ft.TextField(
            label="Stock Mínimo para Alertas",
            value=self.config_actual.get('stock_minimo_alerta', {}).get('valor', '10'),
            border_color=VoltTheme.BORDER_COLOR,
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.dias_vencimiento = ft.TextField(
            label="Días de Vencimiento de Facturas",
            value=self.config_actual.get('dias_vencimiento_factura', {}).get('valor', '30'),
            border_color=VoltTheme.BORDER_COLOR,
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        return ft.Container(
            content=ft.Column([
                # Información de la Empresa
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Información de la Empresa",
                            size=18,
                            weight=ft.FontWeight.W_600,
                            color=VoltTheme.TEXT_PRIMARY
                        ),
                        ft.Container(height=10),
                        self.nombre_empresa,
                        ft.Container(height=10),
                        self.nit_empresa,
                        ft.Container(height=10),
                        self.direccion_empresa,
                        ft.Container(height=10),
                        ft.Row([
                            self.telefono_empresa,
                            self.email_empresa
                        ], spacing=20, wrap=True)
                    ]),
                    padding=VoltTheme.SPACING_LG,
                    bgcolor=VoltTheme.BG_SECONDARY,
                    border_radius=VoltTheme.RADIUS_LG,
                    border=ft.border.all(1, VoltTheme.BORDER_COLOR)
                ),
                
                ft.Container(height=20),
                
                # Parámetros del Sistema
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Parámetros del Sistema",
                            size=18,
                            weight=ft.FontWeight.W_600,
                            color=VoltTheme.TEXT_PRIMARY
                        ),
                        ft.Container(height=10),
                        ft.Row([
                            self.iva,
                            self.moneda
                        ], spacing=20),
                        ft.Container(height=10),
                        ft.Row([
                            self.prefijo_factura,
                            self.stock_minimo
                        ], spacing=20),
                        ft.Container(height=10),
                        self.dias_vencimiento
                    ]),
                    padding=VoltTheme.SPACING_LG,
                    bgcolor=VoltTheme.BG_SECONDARY,
                    border_radius=VoltTheme.RADIUS_LG,
                    border=ft.border.all(1, VoltTheme.BORDER_COLOR)
                ),
                
                ft.Container(height=20),
                
                # Botones
                ft.Row([
                    ft.ElevatedButton(
                        "Guardar Cambios",
                        icon=ft.Icons.SAVE,
                        bgcolor=VoltTheme.SUCCESS,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: self._guardar_configuracion()
                    ),
                    ft.OutlinedButton(
                        "Restablecer",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda _: self._cargar_configuracion()
                    )
                ], spacing=10)
                
            ], scroll=ft.ScrollMode.AUTO)
        )
    
    def _guardar_configuracion(self):
        """Guarda la configuración actualizada"""
        parametros = {
            'nombre_empresa': self.nombre_empresa.value.strip(),
            'nit_empresa': self.nit_empresa.value.strip(),
            'direccion_empresa': self.direccion_empresa.value.strip(),
            'telefono_empresa': self.telefono_empresa.value.strip(),
            'email_empresa': self.email_empresa.value.strip(),
            'iva': self.iva.value.strip(),
            'moneda': self.moneda.value.strip(),
            'prefijo_factura': self.prefijo_factura.value.strip(),
            'stock_minimo_alerta': self.stock_minimo.value.strip(),
            'dias_vencimiento_factura': self.dias_vencimiento.value.strip()
        }
        
        resultado = self.service.actualizar_configuracion(parametros)
        
        if resultado['success']:
            self._mostrar_mensaje("Configuración guardada correctamente", VoltTheme.SUCCESS)
            self._cargar_configuracion()
        else:
            self._mostrar_mensaje(resultado.get('message', 'Error al guardar'), VoltTheme.DANGER)
    
    def _mostrar_mensaje(self, mensaje: str, color: str):
        """Muestra un mensaje al usuario"""
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
