"""
Vista de Reportes
Pantalla para generar y visualizar reportes del sistema
"""
import flet as ft
from datetime import datetime, date
from services.reporte_service import ReporteService
from utils.theme import VoltTheme
from utils.exportar_reportes import ExportadorReportes
import os
import subprocess


class ReportesView:
    """Vista para generación de reportes"""
    
    def __init__(self, page: ft.Page, empleado):
        self.page = page
        self.empleado = empleado
        self.reporte_service = ReporteService()
        
        # Estado
        self.reporte_actual = None
        self.datos_reporte = None
        self.tipo_reporte_actual = None  # Para saber qué reporte está mostrándose
        
        # Referencias a controles
        self.tipo_reporte = None
        self.fecha_inicio = None
        self.fecha_fin = None
        self.fecha_unica = None
        self.mes_selector = None
        self.año_selector = None
        self.filtros_container = None
        self.resultado_container = None
        
    def build(self):
        """Construye la interfaz de reportes"""
        # Título
        titulo = ft.Container(
            content=ft.Column([
                ft.Text("Reportes del Sistema", size=28, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                ft.Text("Genera y visualiza reportes de operaciones", size=14, color=VoltTheme.TEXT_SECONDARY)
            ], spacing=5),
            padding=ft.padding.only(left=20, top=20, bottom=10)
        )
        
        # Selector de tipo de reporte
        self.tipo_reporte = ft.Dropdown(
            label="Tipo de Reporte",
            width=400,
            border_color=VoltTheme.BORDER_COLOR,
            options=[
                ft.dropdown.Option(key="cierre_diario", text="Cierre de Caja Diario"),
                ft.dropdown.Option(key="cierre_mensual", text="Cierre de Caja Mensual"),
                ft.dropdown.Option(key="compras_periodo", text="Compras por Periodo"),
                ft.dropdown.Option(key="productos_existencias", text="Productos y Existencias"),
                ft.dropdown.Option(key="cartera_clientes", text="Cartera de Clientes"),
                ft.dropdown.Option(key="cartera_proveedores", text="Cartera de Proveedores"),
                ft.dropdown.Option(key="cartera_empleados", text="Cartera de Empleados"),
            ],
            on_change=lambda _: self.cambiar_tipo_reporte()
        )
        
        # Contenedor de filtros (se actualiza según el tipo de reporte)
        self.filtros_container = ft.Container(
            content=ft.Column([
                ft.Text("Seleccione un tipo de reporte", color=VoltTheme.TEXT_SECONDARY)
            ]),
            padding=20,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD
        )
        
        # Panel de selección
        panel_seleccion = ft.Container(
            content=ft.Column([
                ft.Text("Selección de Reporte", size=18, weight=ft.FontWeight.W_600, color=VoltTheme.TEXT_PRIMARY),
                ft.Container(height=10),
                self.tipo_reporte,
                ft.Container(height=20),
                self.filtros_container,
            ]),
            padding=20,
            bgcolor=VoltTheme.BG_SECONDARY,
            border_radius=VoltTheme.RADIUS_LG
        )
        
        # Contenedor de resultados
        self.resultado_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Icon("description", size=80, color=VoltTheme.TEXT_MUTED),
                        ft.Container(height=10),
                        ft.Text(
                            "No hay reporte generado",
                            size=16,
                            color=VoltTheme.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Container(height=5),
                        ft.Text(
                            "Selecciona un tipo de reporte y genera el informe",
                            size=14,
                            color=VoltTheme.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0
                    ),
                    alignment=ft.alignment.center,
                    padding=60
                )
            ]),
            padding=20,
            bgcolor=VoltTheme.BG_SECONDARY,
            border_radius=VoltTheme.RADIUS_LG,
            expand=True
        )
        
        # Layout principal
        contenido = ft.Container(
            content=ft.Column([
                titulo,
                ft.Container(
                    content=ft.Row([
                        # Columna izquierda: Selección
                        ft.Container(
                            content=panel_seleccion,
                            width=450
                        ),
                        # Columna derecha: Resultados
                        ft.Container(
                            content=self.resultado_container,
                            expand=True
                        )
                    ], spacing=20, expand=True),
                    padding=20,
                    expand=True
                )
            ], expand=True),
            expand=True
        )
        
        return contenido
    
    def cambiar_tipo_reporte(self):
        """Actualiza los filtros según el tipo de reporte seleccionado"""
        tipo = self.tipo_reporte.value
        
        if tipo == "cierre_diario":
            self.mostrar_filtro_fecha_unica()
        elif tipo == "cierre_mensual":
            self.mostrar_filtro_mes_año()
        elif tipo == "compras_periodo":
            self.mostrar_filtro_periodo()
        else:
            # Reportes sin filtros
            self.mostrar_sin_filtros()
    
    def mostrar_filtro_fecha_unica(self):
        """Muestra filtro de fecha única para cierre diario"""
        self.fecha_unica = ft.TextField(
            label="Fecha",
            hint_text="DD/MM/AAAA",
            width=200,
            value=datetime.now().strftime("%d/%m/%Y"),
            border_color=VoltTheme.BORDER_COLOR
        )
        
        self.filtros_container.content = ft.Column([
            ft.Text("Filtros", size=16, weight=ft.FontWeight.W_600, color=VoltTheme.TEXT_PRIMARY),
            ft.Container(height=10),
            self.fecha_unica,
            ft.Container(height=20),
            ft.ElevatedButton(
                "Generar Reporte",
                icon=ft.Icons.ANALYTICS,
                bgcolor=VoltTheme.PRIMARY,
                color=ft.Colors.WHITE,
                on_click=lambda _: self.generar_cierre_diario()
            )
        ])
        self.page.update()
    
    def mostrar_filtro_mes_año(self):
        """Muestra filtros de mes y año para cierre mensual"""
        año_actual = datetime.now().year
        mes_actual = datetime.now().month
        
        self.mes_selector = ft.Dropdown(
            label="Mes",
            width=200,
            value=str(mes_actual),
            border_color=VoltTheme.BORDER_COLOR,
            options=[
                ft.dropdown.Option("1", "Enero"),
                ft.dropdown.Option("2", "Febrero"),
                ft.dropdown.Option("3", "Marzo"),
                ft.dropdown.Option("4", "Abril"),
                ft.dropdown.Option("5", "Mayo"),
                ft.dropdown.Option("6", "Junio"),
                ft.dropdown.Option("7", "Julio"),
                ft.dropdown.Option("8", "Agosto"),
                ft.dropdown.Option("9", "Septiembre"),
                ft.dropdown.Option("10", "Octubre"),
                ft.dropdown.Option("11", "Noviembre"),
                ft.dropdown.Option("12", "Diciembre"),
            ]
        )
        
        self.año_selector = ft.TextField(
            label="Año",
            width=120,
            value=str(año_actual),
            border_color=VoltTheme.BORDER_COLOR
        )
        
        self.filtros_container.content = ft.Column([
            ft.Text("Filtros", size=16, weight=ft.FontWeight.W_600, color=VoltTheme.TEXT_PRIMARY),
            ft.Container(height=10),
            ft.Row([self.mes_selector, self.año_selector], spacing=10),
            ft.Container(height=20),
            ft.ElevatedButton(
                "Generar Reporte",
                icon=ft.Icons.ANALYTICS,
                bgcolor=VoltTheme.PRIMARY,
                color=ft.Colors.WHITE,
                on_click=lambda _: self.generar_cierre_mensual()
            )
        ])
        self.page.update()
    
    def mostrar_filtro_periodo(self):
        """Muestra filtros de periodo para compras"""
        self.fecha_inicio = ft.TextField(
            label="Fecha Inicio",
            hint_text="DD/MM/AAAA",
            width=200,
            value=datetime.now().replace(day=1).strftime("%d/%m/%Y"),
            border_color=VoltTheme.BORDER_COLOR
        )
        
        self.fecha_fin = ft.TextField(
            label="Fecha Fin",
            hint_text="DD/MM/AAAA",
            width=200,
            value=datetime.now().strftime("%d/%m/%Y"),
            border_color=VoltTheme.BORDER_COLOR
        )
        
        self.filtros_container.content = ft.Column([
            ft.Text("Filtros", size=16, weight=ft.FontWeight.W_600, color=VoltTheme.TEXT_PRIMARY),
            ft.Container(height=10),
            ft.Row([self.fecha_inicio, self.fecha_fin], spacing=10),
            ft.Container(height=20),
            ft.ElevatedButton(
                "Generar Reporte",
                icon=ft.Icons.ANALYTICS,
                bgcolor=VoltTheme.PRIMARY,
                color=ft.Colors.WHITE,
                on_click=lambda _: self.generar_compras_periodo()
            )
        ])
        self.page.update()
    
    def mostrar_sin_filtros(self):
        """Muestra botón para reportes que no requieren filtros"""
        tipo = self.tipo_reporte.value
        
        if tipo == "productos_existencias":
            handler = self.generar_productos_existencias
        elif tipo == "cartera_clientes":
            handler = self.generar_cartera_clientes
        elif tipo == "cartera_proveedores":
            handler = self.generar_cartera_proveedores
        elif tipo == "cartera_empleados":
            handler = self.generar_cartera_empleados
        else:
            handler = None
        
        self.filtros_container.content = ft.Column([
            ft.Text("Este reporte no requiere filtros", size=14, color=VoltTheme.TEXT_SECONDARY),
            ft.Container(height=20),
            ft.ElevatedButton(
                "Generar Reporte",
                icon=ft.Icons.ANALYTICS,
                bgcolor=VoltTheme.PRIMARY,
                color=ft.Colors.WHITE,
                on_click=lambda _: handler() if handler else None
            )
        ])
        self.page.update()
    
    # Métodos para generar cada tipo de reporte
    
    def generar_cierre_diario(self):
        """Genera reporte de cierre de caja diario"""
        try:
            fecha_str = self.fecha_unica.value
            fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
            
            resultado = self.reporte_service.generar_cierre_caja_diario(fecha)
            
            if resultado['success']:
                self.datos_reporte = resultado
                self.tipo_reporte_actual = 'cierre_diario'
                self.mostrar_reporte_cierre_diario(resultado)
            else:
                self.mostrar_error(resultado.get('message', 'Error al generar reporte'))
        except ValueError:
            self.mostrar_error("Formato de fecha inválido. Use DD/MM/AAAA")
        except Exception as e:
            self.mostrar_error(f"Error: {str(e)}")
    
    def generar_cierre_mensual(self):
        """Genera reporte de cierre de caja mensual"""
        try:
            mes = int(self.mes_selector.value)
            año = int(self.año_selector.value)
            
            resultado = self.reporte_service.generar_cierre_caja_mensual(año, mes)
            
            if resultado['success']:
                self.datos_reporte = resultado
                self.tipo_reporte_actual = 'cierre_mensual'
                self.mostrar_reporte_cierre_mensual(resultado)
            else:
                self.mostrar_error(resultado.get('message', 'Error al generar reporte'))
        except ValueError:
            self.mostrar_error("Valores de mes o año inválidos")
        except Exception as e:
            self.mostrar_error(f"Error: {str(e)}")
    
    def generar_compras_periodo(self):
        """Genera reporte de compras por periodo"""
        try:
            fecha_inicio = datetime.strptime(self.fecha_inicio.value, "%d/%m/%Y").date()
            fecha_fin = datetime.strptime(self.fecha_fin.value, "%d/%m/%Y").date()
            
            resultado = self.reporte_service.generar_compras_por_periodo(fecha_inicio, fecha_fin)
            
            if resultado['success']:
                self.datos_reporte = resultado
                self.tipo_reporte_actual = 'compras_periodo'
                self.mostrar_reporte_compras(resultado)
            else:
                self.mostrar_error(resultado.get('message', 'Error al generar reporte'))
        except ValueError:
            self.mostrar_error("Formato de fecha inválido. Use DD/MM/AAAA")
        except Exception as e:
            self.mostrar_error(f"Error: {str(e)}")
    
    def generar_productos_existencias(self):
        """Genera reporte de productos y existencias"""
        try:
            resultado = self.reporte_service.generar_productos_y_existencias()
            
            if resultado['success']:
                self.datos_reporte = resultado
                self.tipo_reporte_actual = 'productos_existencias'
                self.mostrar_reporte_productos(resultado)
            else:
                self.mostrar_error(resultado.get('message', 'Error al generar reporte'))
        except Exception as e:
            self.mostrar_error(f"Error: {str(e)}")
    
    def generar_cartera_clientes(self):
        """Genera reporte de cartera de clientes"""
        try:
            resultado = self.reporte_service.generar_cartera_clientes()
            
            if resultado['success']:
                self.datos_reporte = resultado
                self.tipo_reporte_actual = 'cartera_clientes'
                self.mostrar_reporte_clientes(resultado)
            else:
                self.mostrar_error(resultado.get('message', 'Error al generar reporte'))
        except Exception as e:
            self.mostrar_error(f"Error: {str(e)}")
    
    def generar_cartera_proveedores(self):
        """Genera reporte de cartera de proveedores"""
        try:
            resultado = self.reporte_service.generar_cartera_proveedores()
            
            if resultado['success']:
                self.datos_reporte = resultado
                self.tipo_reporte_actual = 'cartera_proveedores'
                self.mostrar_reporte_proveedores(resultado)
            else:
                self.mostrar_error(resultado.get('message', 'Error al generar reporte'))
        except Exception as e:
            self.mostrar_error(f"Error: {str(e)}")
    
    def generar_cartera_empleados(self):
        """Genera reporte de cartera de empleados"""
        try:
            resultado = self.reporte_service.generar_cartera_empleados()
            
            if resultado['success']:
                self.datos_reporte = resultado
                self.tipo_reporte_actual = 'cartera_empleados'
                self.mostrar_reporte_empleados(resultado)
            else:
                self.mostrar_error(resultado.get('message', 'Error al generar reporte'))
        except Exception as e:
            self.mostrar_error(f"Error: {str(e)}")
    
    # Métodos para mostrar resultados
    
    def mostrar_reporte_cierre_diario(self, resultado):
        """Muestra los resultados del cierre de caja diario"""
        resumen = resultado['resumen']
        ventas = resultado['ventas']
        
        # Tarjetas de resumen
        tarjetas = ft.Row([
            self.crear_tarjeta_metrica("Total Ventas", str(resumen.get('total_ventas', 0)), "shopping_cart", VoltTheme.PRIMARY),
            self.crear_tarjeta_metrica("Ingresos", f"Q{resumen.get('total_ingresos', 0):,.2f}", "attach_money", VoltTheme.SUCCESS),
            self.crear_tarjeta_metrica("Efectivo", f"Q{resumen.get('efectivo', 0):,.2f}", "payments", VoltTheme.INFO),
            self.crear_tarjeta_metrica("Tarjeta", f"Q{resumen.get('tarjeta', 0):,.2f}", "credit_card", VoltTheme.WARNING),
        ], spacing=15)
        
        # Tabla de ventas
        tabla = self.crear_tabla_ventas(ventas)
        
        self.resultado_container.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text(f"Cierre de Caja - {resultado['fecha'].strftime('%d/%m/%Y')}", 
                           size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    self.crear_botones_exportacion()
                ]),
                padding=ft.padding.only(bottom=15)
            ),
            tarjetas,
            ft.Container(height=20),
            tabla
        ], scroll=ft.ScrollMode.AUTO)
        
        self.page.update()
    
    def mostrar_reporte_cierre_mensual(self, resultado):
        """Muestra los resultados del cierre de caja mensual"""
        resumen = resultado['resumen']
        datos = resultado['datos_diarios']
        
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        # Tarjetas de resumen
        tarjetas = ft.Row([
            self.crear_tarjeta_metrica("Total Ventas", str(resumen.get('total_ventas', 0)), "shopping_cart", VoltTheme.PRIMARY),
            self.crear_tarjeta_metrica("Ingresos", f"Q{resumen.get('total_ingresos', 0):,.2f}", "attach_money", VoltTheme.SUCCESS),
            self.crear_tarjeta_metrica("Promedio/Venta", f"Q{resumen.get('promedio_venta', 0):,.2f}", "analytics", VoltTheme.INFO),
        ], spacing=15)
        
        # Tabla de datos diarios
        tabla = self.crear_tabla_cierre_mensual(datos)
        
        self.resultado_container.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text(f"Cierre Mensual - {meses[resultado['mes']]} {resultado['año']}", 
                           size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    self.crear_botones_exportacion()
                ]),
                padding=ft.padding.only(bottom=15)
            ),
            tarjetas,
            ft.Container(height=20),
            tabla
        ], scroll=ft.ScrollMode.AUTO)
        
        self.page.update()
    
    def mostrar_reporte_compras(self, resultado):
        """Muestra los resultados del reporte de compras"""
        resumen = resultado['resumen']
        compras = resultado['compras']
        
        # Tarjetas de resumen
        tarjetas = ft.Row([
            self.crear_tarjeta_metrica("Total Compras", str(resumen.get('total_compras', 0)), "shopping_cart", VoltTheme.PRIMARY),
            self.crear_tarjeta_metrica("Total Gastado", f"Q{resumen.get('total_gastado', 0):,.2f}", "money_off", VoltTheme.DANGER),
            self.crear_tarjeta_metrica("Promedio/Compra", f"Q{resumen.get('promedio_compra', 0):,.2f}", "analytics", VoltTheme.INFO),
        ], spacing=15)
        
        # Tabla de compras
        tabla = self.crear_tabla_compras(compras)
        
        self.resultado_container.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text(f"Compras del {resultado['fecha_inicio'].strftime('%d/%m/%Y')} al {resultado['fecha_fin'].strftime('%d/%m/%Y')}", 
                           size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    self.crear_botones_exportacion()
                ]),
                padding=ft.padding.only(bottom=15)
            ),
            tarjetas,
            ft.Container(height=20),
            tabla
        ], scroll=ft.ScrollMode.AUTO)
        
        self.page.update()
    
    def mostrar_reporte_productos(self, resultado):
        """Muestra los resultados del reporte de productos"""
        stats = resultado['estadisticas']
        productos = resultado['productos']
        
        # Tarjetas de resumen
        tarjetas = ft.Row([
            self.crear_tarjeta_metrica("Total Productos", str(stats.get('total_productos', 0)), "inventory_2", VoltTheme.PRIMARY),
            self.crear_tarjeta_metrica("Sin Stock", str(stats.get('sin_stock', 0)), "error", VoltTheme.DANGER),
            self.crear_tarjeta_metrica("Bajo Stock", str(stats.get('bajo_stock', 0)), "warning", VoltTheme.WARNING),
            self.crear_tarjeta_metrica("Valor Inventario", f"Q{stats.get('valor_inventario', 0):,.2f}", "attach_money", VoltTheme.SUCCESS),
        ], spacing=15)
        
        # Tabla de productos
        tabla = self.crear_tabla_productos(productos)
        
        self.resultado_container.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("Productos y Existencias", 
                           size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    self.crear_botones_exportacion()
                ]),
                padding=ft.padding.only(bottom=15)
            ),
            tarjetas,
            ft.Container(height=20),
            tabla
        ], scroll=ft.ScrollMode.AUTO)
        
        self.page.update()
    
    def mostrar_reporte_clientes(self, resultado):
        """Muestra los resultados del reporte de clientes"""
        stats = resultado['estadisticas']
        clientes = resultado['clientes']
        
        # Tarjetas de resumen
        tarjetas = ft.Row([
            self.crear_tarjeta_metrica("Total Clientes", str(stats.get('total_clientes', 0)), "people", VoltTheme.PRIMARY),
            self.crear_tarjeta_metrica("Total Ventas", str(stats.get('total_ventas', 0)), "shopping_cart", VoltTheme.INFO),
            self.crear_tarjeta_metrica("Ticket Promedio", f"Q{stats.get('ticket_promedio', 0):,.2f}", "analytics", VoltTheme.SUCCESS),
        ], spacing=15)
        
        # Tabla de clientes
        tabla = self.crear_tabla_clientes(clientes)
        
        self.resultado_container.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("Cartera de Clientes", 
                           size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    self.crear_botones_exportacion()
                ]),
                padding=ft.padding.only(bottom=15)
            ),
            tarjetas,
            ft.Container(height=20),
            tabla
        ], scroll=ft.ScrollMode.AUTO)
        
        self.page.update()
    
    def mostrar_reporte_proveedores(self, resultado):
        """Muestra los resultados del reporte de proveedores"""
        stats = resultado['estadisticas']
        proveedores = resultado['proveedores']
        
        # Tarjetas de resumen
        tarjetas = ft.Row([
            self.crear_tarjeta_metrica("Total Proveedores", str(stats.get('total_proveedores', 0)), "local_shipping", VoltTheme.PRIMARY),
            self.crear_tarjeta_metrica("Total Compras", str(stats.get('total_compras', 0)), "shopping_cart", VoltTheme.INFO),
            self.crear_tarjeta_metrica("Compra Promedio", f"Q{stats.get('compra_promedio', 0):,.2f}", "analytics", VoltTheme.SUCCESS),
        ], spacing=15)
        
        # Tabla de proveedores
        tabla = self.crear_tabla_proveedores(proveedores)
        
        self.resultado_container.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("Cartera de Proveedores", 
                           size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    self.crear_botones_exportacion()
                ]),
                padding=ft.padding.only(bottom=15)
            ),
            tarjetas,
            ft.Container(height=20),
            tabla
        ], scroll=ft.ScrollMode.AUTO)
        
        self.page.update()
    
    def mostrar_reporte_empleados(self, resultado):
        """Muestra los resultados del reporte de empleados"""
        stats = resultado['estadisticas']
        empleados = resultado['empleados']
        
        # Tarjetas de resumen
        tarjetas = ft.Row([
            self.crear_tarjeta_metrica("Total Empleados", str(stats.get('total_empleados', 0)), "badge", VoltTheme.PRIMARY),
            self.crear_tarjeta_metrica("Activos", str(stats.get('empleados_activos', 0)), "check_circle", VoltTheme.SUCCESS),
            self.crear_tarjeta_metrica("Inactivos", str(stats.get('empleados_inactivos', 0)), "cancel", VoltTheme.DANGER),
            self.crear_tarjeta_metrica("Salario Promedio", f"Q{stats.get('salario_promedio', 0):,.2f}", "attach_money", VoltTheme.INFO),
        ], spacing=15)
        
        # Tabla de empleados
        tabla = self.crear_tabla_empleados_reporte(empleados)
        
        self.resultado_container.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("Cartera de Empleados", 
                           size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    self.crear_botones_exportacion()
                ]),
                padding=ft.padding.only(bottom=15)
            ),
            tarjetas,
            ft.Container(height=20),
            tabla
        ], scroll=ft.ScrollMode.AUTO)
        
        self.page.update()
    
    # Métodos auxiliares para crear componentes
    
    def crear_tarjeta_metrica(self, titulo, valor, icono, color):
        """Crea una tarjeta de métrica"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icono, color=color, size=24),
                    ft.Container(expand=True),
                ]),
                ft.Container(height=10),
                ft.Text(valor, size=24, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                ft.Text(titulo, size=12, color=VoltTheme.TEXT_SECONDARY),
            ], spacing=5),
            padding=20,
            bgcolor=VoltTheme.BG_PRIMARY,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD,
            expand=True
        )
    
    def crear_tabla_ventas(self, ventas):
        """Crea tabla de ventas"""
        if not ventas:
            return ft.Text("No hay ventas registradas", color=VoltTheme.TEXT_SECONDARY)
        
        filas = []
        for v in ventas:
            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(v.get('numero_factura', ''), size=13)),
                    ft.DataCell(ft.Text(v.get('cliente', ''), size=13)),
                    ft.DataCell(ft.Text(v.get('empleado', ''), size=13)),
                    ft.DataCell(ft.Text(v.get('metodo_pago', '').capitalize(), size=13)),
                    ft.DataCell(ft.Text(f"Q{v.get('total', 0):,.2f}", size=13, weight=ft.FontWeight.W_600)),
                ])
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Factura", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Cliente", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Vendedor", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Método Pago", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD)),
            ],
            rows=filas,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD,
            vertical_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
            horizontal_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
        )
    
    def crear_tabla_cierre_mensual(self, datos):
        """Crea tabla de cierre mensual"""
        if not datos:
            return ft.Text("No hay datos para este mes", color=VoltTheme.TEXT_SECONDARY)
        
        filas = []
        for d in datos:
            fecha = d.get('fecha')
            if isinstance(fecha, str):
                try:
                    fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
                except:
                    pass
            
            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(fecha.strftime("%d/%m/%Y") if hasattr(fecha, 'strftime') else str(fecha), size=13)),
                    ft.DataCell(ft.Text(str(d.get('total_ventas', 0)), size=13)),
                    ft.DataCell(ft.Text(f"Q{d.get('efectivo', 0):,.2f}", size=13)),
                    ft.DataCell(ft.Text(f"Q{d.get('tarjeta', 0):,.2f}", size=13)),
                    ft.DataCell(ft.Text(f"Q{d.get('transferencia', 0):,.2f}", size=13)),
                    ft.DataCell(ft.Text(f"Q{d.get('total_ingresos', 0):,.2f}", size=13, weight=ft.FontWeight.W_600)),
                ])
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ventas", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Efectivo", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Tarjeta", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Transferencia", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD)),
            ],
            rows=filas,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD,
            vertical_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
            horizontal_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
        )
    
    def crear_tabla_compras(self, compras):
        """Crea tabla de compras"""
        if not compras:
            return ft.Text("No hay compras en este periodo", color=VoltTheme.TEXT_SECONDARY)
        
        filas = []
        for c in compras:
            fecha = c.get('fecha_compra')
            if isinstance(fecha, str):
                try:
                    fecha = datetime.strptime(fecha.split()[0], "%Y-%m-%d").date()
                except:
                    pass
            
            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(c.get('numero_factura', ''), size=13)),
                    ft.DataCell(ft.Text(fecha.strftime("%d/%m/%Y") if hasattr(fecha, 'strftime') else str(fecha), size=13)),
                    ft.DataCell(ft.Text(c.get('proveedor', ''), size=13)),
                    ft.DataCell(ft.Text(str(c.get('total_productos', 0)), size=13)),
                    ft.DataCell(ft.Text(f"Q{c.get('total', 0):,.2f}", size=13, weight=ft.FontWeight.W_600)),
                ])
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Factura", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Fecha", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Proveedor", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Productos", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD)),
            ],
            rows=filas,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD,
            vertical_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
            horizontal_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
        )
    
    def crear_tabla_productos(self, productos):
        """Crea tabla de productos"""
        if not productos:
            return ft.Text("No hay productos registrados", color=VoltTheme.TEXT_SECONDARY)
        
        filas = []
        for p in productos:
            nivel = p.get('nivel_stock', 'NORMAL')
            color_stock = VoltTheme.DANGER if nivel == 'SIN_STOCK' else (VoltTheme.WARNING if nivel == 'BAJO_STOCK' else VoltTheme.SUCCESS)
            
            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p.get('codigo', ''), size=13)),
                    ft.DataCell(ft.Text(p.get('nombre', ''), size=13)),
                    ft.DataCell(ft.Text(p.get('categoria', ''), size=13)),
                    ft.DataCell(ft.Text(str(p.get('stock_actual', 0)), size=13, color=color_stock, weight=ft.FontWeight.W_600)),
                    ft.DataCell(ft.Text(str(p.get('stock_minimo', 0)), size=13)),
                    ft.DataCell(ft.Text(f"Q{p.get('precio_venta', 0):,.2f}", size=13)),
                ])
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Producto", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Categoría", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Stock", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Mínimo", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Precio", weight=ft.FontWeight.BOLD)),
            ],
            rows=filas,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD,
            vertical_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
            horizontal_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
        )
    
    def crear_tabla_clientes(self, clientes):
        """Crea tabla de clientes"""
        if not clientes:
            return ft.Text("No hay clientes registrados", color=VoltTheme.TEXT_SECONDARY)
        
        filas = []
        for c in clientes:
            ultima = c.get('ultima_compra')
            if ultima and isinstance(ultima, str):
                try:
                    ultima = datetime.strptime(ultima.split()[0], "%Y-%m-%d").date()
                except:
                    pass
            
            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"{c.get('nombre', '')} {c.get('apellido', '')}", size=13)),
                    ft.DataCell(ft.Text(c.get('email', ''), size=13)),
                    ft.DataCell(ft.Text(c.get('telefono', ''), size=13)),
                    ft.DataCell(ft.Text(str(c.get('total_compras', 0)), size=13)),
                    ft.DataCell(ft.Text(f"Q{c.get('total_gastado', 0):,.2f}", size=13, weight=ft.FontWeight.W_600)),
                    ft.DataCell(ft.Text(ultima.strftime("%d/%m/%Y") if hasattr(ultima, 'strftime') else '-', size=13)),
                ])
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Cliente", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Email", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Teléfono", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Compras", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Total Gastado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Última Compra", weight=ft.FontWeight.BOLD)),
            ],
            rows=filas,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD,
            vertical_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
            horizontal_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
        )
    
    def crear_tabla_proveedores(self, proveedores):
        """Crea tabla de proveedores"""
        if not proveedores:
            return ft.Text("No hay proveedores registrados", color=VoltTheme.TEXT_SECONDARY)
        
        filas = []
        for p in proveedores:
            ultima = p.get('ultima_compra')
            if ultima and isinstance(ultima, str):
                try:
                    ultima = datetime.strptime(ultima.split()[0], "%Y-%m-%d").date()
                except:
                    pass
            
            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p.get('nombre_empresa', ''), size=13)),
                    ft.DataCell(ft.Text(p.get('nombre_contacto', ''), size=13)),
                    ft.DataCell(ft.Text(p.get('telefono', ''), size=13)),
                    ft.DataCell(ft.Text(str(p.get('total_compras', 0)), size=13)),
                    ft.DataCell(ft.Text(f"Q{p.get('total_comprado', 0):,.2f}", size=13, weight=ft.FontWeight.W_600)),
                    ft.DataCell(ft.Text(ultima.strftime("%d/%m/%Y") if hasattr(ultima, 'strftime') else '-', size=13)),
                ])
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Empresa", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Contacto", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Teléfono", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Compras", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Total Comprado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Última Compra", weight=ft.FontWeight.BOLD)),
            ],
            rows=filas,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD,
            vertical_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
            horizontal_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
        )
    
    def crear_tabla_empleados_reporte(self, empleados):
        """Crea tabla de empleados"""
        if not empleados:
            return ft.Text("No hay empleados registrados", color=VoltTheme.TEXT_SECONDARY)
        
        filas = []
        for e in empleados:
            filas.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"{e.get('nombre', '')} {e.get('apellido', '')}", size=13)),
                    ft.DataCell(ft.Text(e.get('puesto', ''), size=13)),
                    ft.DataCell(ft.Text(e.get('rol', ''), size=13)),
                    ft.DataCell(ft.Text(e.get('telefono', ''), size=13)),
                    ft.DataCell(ft.Text(str(e.get('total_ventas_realizadas', 0)), size=13)),
                    ft.DataCell(ft.Text("Activo" if e.get('estado') else "Inactivo", 
                                      size=13, 
                                      color=VoltTheme.SUCCESS if e.get('estado') else VoltTheme.DANGER)),
                ])
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Empleado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Puesto", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Rol", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Teléfono", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ventas", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
            ],
            rows=filas,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=VoltTheme.RADIUS_MD,
            vertical_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
            horizontal_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
        )
    
    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error"""
        self.resultado_container.content = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon("error", size=60, color=VoltTheme.DANGER),
                    ft.Container(height=10),
                    ft.Text("Error", size=18, weight=ft.FontWeight.BOLD, color=VoltTheme.DANGER),
                    ft.Container(height=5),
                    ft.Text(mensaje, size=14, color=VoltTheme.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center,
                padding=60
            )
        ])
        self.page.update()
    
    def crear_botones_exportacion(self):
        """Crea botones para exportar a PDF y Excel"""
        return ft.Row([
            ft.IconButton(
                icon=ft.Icons.PICTURE_AS_PDF,
                icon_color=VoltTheme.DANGER,
                tooltip="Exportar a PDF",
                on_click=lambda _: self.exportar_pdf()
            ),
            ft.IconButton(
                icon=ft.Icons.TABLE_CHART,
                icon_color=VoltTheme.SUCCESS,
                tooltip="Exportar a Excel",
                on_click=lambda _: self.exportar_excel()
            )
        ], spacing=5)
    
    def exportar_pdf(self):
        """Exporta el reporte actual a PDF"""
        if not self.datos_reporte or not self.tipo_reporte_actual:
            self.mostrar_mensaje("No hay reporte para exportar", VoltTheme.WARNING)
            return
        
        try:
            ruta = ExportadorReportes.exportar_a_pdf(
                self.datos_reporte,
                self.tipo_reporte_actual
            )
            
            # Abrir el archivo
            if os.path.exists(ruta):
                os.startfile(ruta)  # Windows
                self.mostrar_mensaje(f"PDF generado: {os.path.basename(ruta)}", VoltTheme.SUCCESS)
            
        except Exception as e:
            self.mostrar_mensaje(f"Error al exportar PDF: {str(e)}", VoltTheme.DANGER)
    
    def exportar_excel(self):
        """Exporta el reporte actual a Excel"""
        if not self.datos_reporte or not self.tipo_reporte_actual:
            self.mostrar_mensaje("No hay reporte para exportar", VoltTheme.WARNING)
            return
        
        try:
            ruta = ExportadorReportes.exportar_a_excel(
                self.datos_reporte,
                self.tipo_reporte_actual
            )
            
            # Abrir el archivo
            if os.path.exists(ruta):
                os.startfile(ruta)  # Windows
                self.mostrar_mensaje(f"Excel generado: {os.path.basename(ruta)}", VoltTheme.SUCCESS)
            
        except Exception as e:
            self.mostrar_mensaje(f"Error al exportar Excel: {str(e)}", VoltTheme.DANGER)
    
    def mostrar_mensaje(self, mensaje, color):
        """Muestra un mensaje temporal al usuario"""
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
