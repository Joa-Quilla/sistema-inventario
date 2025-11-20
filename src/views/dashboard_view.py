"""
Vista del Dashboard Principal
Incluye sidebar, header y área de contenido
"""
import flet as ft
from utils.theme import VoltTheme
from views.productos_view import ProductosView
from views.clientes_view import ClientesView
from views.compras_view import ComprasView
from views.proveedores_view import ProveedoresView
from views.ventas_view import VentasView
from views.cajas_view import CajasView
from views.empleados_view import EmpleadosView
from views.reportes_view import ReportesView
from views.configuracion_view import ConfiguracionView
from database.connection import get_db
from datetime import date
import threading
import time


class DashboardView:
    """Dashboard principal del sistema"""
    
    def __init__(self, page: ft.Page, auth_service, empleado, on_logout):
        self.page = page
        self.auth = auth_service
        self.empleado = empleado
        self.on_logout = on_logout
        self.contenido_actual = None
        self.sidebar_expanded = True
        self.contenedor_contenido = None
        self.ruta_actual = "dashboard"
        
    def build(self):
        """Construye el dashboard completo"""
        
        # Crear sidebar
        self.sidebar = self._crear_sidebar()
        
        # Crear header
        self.header = self._crear_header()
        
        # Contenido inicial (dashboard home)
        self.contenido_actual = self._crear_dashboard_home()
        
        # Contenedor de contenido (para poder actualizarlo dinámicamente)
        self.contenedor_contenido = ft.Container(
            content=self.contenido_actual,
            expand=True,
            padding=0
        )
        
        # Mostrar diálogo de bienvenida
        self.page.overlay.append(self._crear_dialogo_bienvenida())
        threading.Thread(target=self._auto_cerrar_bienvenida, daemon=True).start()
        
        # Layout principal
        return ft.Row([
            # Sidebar
            self.sidebar,
            
            # Área principal (header + contenido)
            ft.Container(
                content=ft.Column([
                    self.header,
                    self.contenedor_contenido
                ], spacing=0),
                expand=True,
                bgcolor=VoltTheme.BG_PRIMARY
            )
        ], spacing=0, expand=True)
    
    def _crear_sidebar(self):
        """Crea el menú lateral"""
        
        # Opciones del menú según permisos
        menu_items = []
        
        # Dashboard (todos)
        menu_items.append(self._crear_menu_item("dashboard", "Dashboard", "dashboard", True))
        
        # Ventas
        if self.auth.verificar_permiso('ventas', 'crear'):
            menu_items.append(self._crear_menu_item("point_of_sale", "Ventas", "ventas", False))
        
        # Productos
        if self.auth.verificar_permiso('productos', 'leer'):
            menu_items.append(self._crear_menu_item("inventory_2", "Productos", "productos", False))
        
        # Clientes
        if self.auth.verificar_permiso('clientes', 'leer'):
            menu_items.append(self._crear_menu_item("people", "Clientes", "clientes", False))
        
        # Compras
        if self.auth.verificar_permiso('compras', 'leer'):
            menu_items.append(self._crear_menu_item("shopping_cart", "Compras", "compras", False))
        
        # Proveedores
        if self.auth.verificar_permiso('proveedores', 'leer'):
            menu_items.append(self._crear_menu_item("local_shipping", "Proveedores", "proveedores", False))
        
        # Cajas
        if self.auth.verificar_permiso('cajas', 'abrir'):
            menu_items.append(self._crear_menu_item("account_balance_wallet", "Cajas", "cajas", False))
        
        # Empleados (solo admin/gerente)
        if self.auth.verificar_permiso('empleados', 'leer'):
            menu_items.append(self._crear_menu_item("badge", "Empleados", "empleados", False))
        
        # Reportes
        if self.auth.verificar_permiso('reportes', 'cierre_caja'):
            menu_items.append(self._crear_menu_item("assessment", "Reportes", "reportes", False))
        
        # Configuración (solo admin)
        if self.auth.verificar_permiso('configuracion', 'acceder'):
            menu_items.append(self._crear_menu_item("settings", "Configuración", "configuracion", False))
        
        return ft.Container(
            content=ft.Column([
                # Logo/Título
                ft.Container(
                    content=ft.Row([
                        ft.Icon("inventory_2", color=VoltTheme.TEXT_WHITE, size=32),
                        ft.Text(
                            "Inventario",
                            size=VoltTheme.FONT_SIZE_LG,
                            weight=ft.FontWeight.BOLD,
                            color=VoltTheme.TEXT_WHITE
                        )
                    ], spacing=12),
                    padding=VoltTheme.SPACING_LG,
                    border=ft.border.only(bottom=ft.BorderSide(1, "#3D4254"))
                ),
                
                # Menú
                ft.Container(
                    content=ft.Column(menu_items, spacing=4),
                    padding=ft.padding.symmetric(vertical=VoltTheme.SPACING_MD),
                    expand=True
                ),
                
                # Usuario actual
                ft.Container(
                    content=ft.Column([
                        ft.Divider(color="#3D4254", height=1),
                        ft.Row([
                            ft.Icon("account_circle", color=VoltTheme.TEXT_WHITE, size=40),
                            ft.Column([
                                ft.Text(
                                    f"{self.empleado['nombre']} {self.empleado['apellido']}",
                                    size=VoltTheme.FONT_SIZE_SM,
                                    weight=ft.FontWeight.W_600,
                                    color=VoltTheme.TEXT_WHITE,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                ft.Text(
                                    self.empleado['nombre_rol'],
                                    size=VoltTheme.FONT_SIZE_XS,
                                    color=VoltTheme.TEXT_MUTED
                                )
                            ], spacing=0, expand=True)
                        ], spacing=12)
                    ], spacing=8),
                    padding=VoltTheme.SPACING_LG
                )
            ], spacing=0),
            width=200,
            bgcolor=VoltTheme.PRIMARY
        )
    
    def _crear_menu_item(self, icon, texto, route, activo=False):
        """Crea un item del menú"""
        es_activo = self.ruta_actual == route
        bg_color = ft.Colors.with_opacity(0.2, ft.Colors.WHITE) if es_activo else "transparent"
        border_left = ft.border.only(left=ft.BorderSide(4, ft.Colors.WHITE)) if es_activo else None
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=VoltTheme.TEXT_WHITE, size=20),
                ft.Text(
                    texto,
                    size=VoltTheme.FONT_SIZE_SM,
                    color=VoltTheme.TEXT_WHITE,
                    weight=ft.FontWeight.BOLD if es_activo else ft.FontWeight.NORMAL
                )
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=VoltTheme.SPACING_LG, vertical=12),
            bgcolor=bg_color,
            border=border_left,
            border_radius=ft.border_radius.only(top_right=8, bottom_right=8),
            margin=ft.margin.only(right=VoltTheme.SPACING_SM),
            ink=True,
            on_click=lambda e, r=route: self._navegar(r)
        )
    
    def _crear_header(self):
        """Crea el header superior"""
        return ft.Container(
            content=ft.Row([
                ft.Text(
                    "Dashboard",
                    size=VoltTheme.FONT_SIZE_2XL,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.TEXT_PRIMARY
                ),
                ft.Container(expand=True),
                # Botón de cerrar sesión
                ft.Container(
                    content=ft.Row([
                        ft.Icon("logout", color=VoltTheme.DANGER, size=18),
                        ft.Text(
                            "Cerrar Sesión",
                            size=VoltTheme.FONT_SIZE_SM,
                            color=VoltTheme.DANGER,
                            weight=ft.FontWeight.W_500
                        )
                    ], spacing=8),
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    border=ft.border.all(1, VoltTheme.DANGER),
                    border_radius=VoltTheme.RADIUS_MD,
                    ink=True,
                    on_click=lambda e: self.on_logout()
                )
            ]),
            padding=VoltTheme.SPACING_LG,
            bgcolor=VoltTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
    
    def _crear_dashboard_home(self):
        """Crea el contenido inicial del dashboard"""
        
        # Obtener datos reales de forma segura
        try:
            db = get_db()
            
            # Total productos
            result = db.execute_query("SELECT COUNT(*) as total FROM productos WHERE estado = TRUE", fetch='one')
            total_productos = result['total'] if result else 0
            
            # Ventas hoy
            hoy = date.today()
            result = db.execute_query("""
                SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto 
                FROM ventas 
                WHERE DATE(fecha_venta) = %s
            """, (hoy,), fetch='one')
            ventas_hoy = result['monto'] if result else 0
            
            # Total clientes
            result = db.execute_query("SELECT COUNT(*) as total FROM clientes WHERE estado = TRUE", fetch='one')
            total_clientes = result['total'] if result else 0
            
            # Productos bajo stock
            result = db.execute_query("""
                SELECT COUNT(*) as total 
                FROM productos 
                WHERE stock_actual <= stock_minimo AND estado = TRUE
            """, fetch='one')
            stock_bajo = result['total'] if result else 0
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo datos dashboard: {e}")
            import traceback
            traceback.print_exc()
            total_productos = 0
            ventas_hoy = 0
            total_clientes = 0
            stock_bajo = 0
        
        # Tarjetas de estadísticas
        stats_cards = ft.Container(
            content=ft.Row([
                self._crear_stat_card("Total Productos", str(total_productos), "inventory", VoltTheme.INFO),
                self._crear_stat_card("Ventas Hoy", f"Q {ventas_hoy:,.2f}", "attach_money", VoltTheme.SUCCESS),
                self._crear_stat_card("Clientes", str(total_clientes), "people", VoltTheme.WARNING),
                self._crear_stat_card("Stock Bajo", str(stock_bajo), "warning", VoltTheme.DANGER),
            ], wrap=True, spacing=VoltTheme.SPACING_MD, alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.only(left=20, right=20, top=20, bottom=0)
        )
        
        return ft.Column([
            # Estadísticas
            stats_cards,
            
            ft.Container(height=VoltTheme.SPACING_LG),
            
            # Información adicional
            ft.Row([
                # Últimas ventas
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("shopping_bag", size=20, color=VoltTheme.PRIMARY),
                            ft.Text("Actividad Reciente", size=16, weight=ft.FontWeight.W_600, color=VoltTheme.TEXT_PRIMARY)
                        ], spacing=8),
                        ft.Container(height=10),
                        ft.Text("• Ventas del mes: Ver en Reportes", size=14, color=VoltTheme.TEXT_SECONDARY),
                        ft.Text("• Productos más vendidos: Ver en Reportes", size=14, color=VoltTheme.TEXT_SECONDARY),
                        ft.Text("• Inventario actualizado: Ver en Productos", size=14, color=VoltTheme.TEXT_SECONDARY),
                    ]),
                    padding=VoltTheme.SPACING_LG,
                    bgcolor=VoltTheme.BG_SECONDARY,
                    border_radius=VoltTheme.RADIUS_LG,
                    border=ft.border.all(1, VoltTheme.BORDER_COLOR),
                    expand=1
                ),
                
                ft.Container(width=15),
                
                # Accesos rápidos
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("bolt", size=20, color=VoltTheme.SUCCESS),
                            ft.Text("Accesos Rápidos", size=16, weight=ft.FontWeight.W_600, color=VoltTheme.TEXT_PRIMARY)
                        ], spacing=8),
                        ft.Container(height=10),
                        ft.Text("✓ Nueva venta en módulo Ventas", size=14, color=VoltTheme.TEXT_SECONDARY),
                        ft.Text("✓ Registrar compra en Compras", size=14, color=VoltTheme.TEXT_SECONDARY),
                        ft.Text("✓ Gestionar productos en Productos", size=14, color=VoltTheme.TEXT_SECONDARY),
                    ]),
                    padding=VoltTheme.SPACING_LG,
                    bgcolor=VoltTheme.BG_SECONDARY,
                    border_radius=VoltTheme.RADIUS_LG,
                    border=ft.border.all(1, VoltTheme.BORDER_COLOR),
                    expand=1
                )
            ], spacing=0)
        ], scroll=ft.ScrollMode.AUTO)
    
    def _crear_stat_card(self, titulo, valor, icon, color):
        """Crea una card de estadística"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(
                            titulo,
                            size=VoltTheme.FONT_SIZE_SM,
                            color=VoltTheme.TEXT_SECONDARY,
                            text_align=ft.TextAlign.LEFT
                        ),
                        ft.Text(
                            valor,
                            size=VoltTheme.FONT_SIZE_2XL,
                            weight=ft.FontWeight.BOLD,
                            color=VoltTheme.TEXT_PRIMARY,
                            text_align=ft.TextAlign.LEFT
                        )
                    ], spacing=4, expand=True, horizontal_alignment=ft.CrossAxisAlignment.START),
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=32),
                        bgcolor=f"{color}20",
                        padding=12,
                        border_radius=VoltTheme.RADIUS_MD
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            width=280,
            padding=VoltTheme.SPACING_LG,
            bgcolor=VoltTheme.BG_SECONDARY,
            border_radius=VoltTheme.RADIUS_LG,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR)
        )
    
    def _crear_dialogo_bienvenida(self):
        """Crea el diálogo de bienvenida"""
        # Construir nombre completo desde el diccionario
        nombre_completo = f"{self.empleado.get('nombre', '')} {self.empleado.get('apellido', '')}".strip()
        if not nombre_completo:
            nombre_completo = self.empleado.get('usuario', 'Usuario')
        
        self.dialogo_bienvenida = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon("waving_hand", color=VoltTheme.SUCCESS, size=30),
                ft.Text("¡Bienvenido!", size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY)
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            content=ft.Column([
                ft.Text(
                    nombre_completo,
                    size=18,
                    weight=ft.FontWeight.W_500,
                    color=VoltTheme.TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=5),
                ft.Text(
                    f"Rol: {self.empleado.get('nombre_rol', 'Usuario')}",
                    size=14,
                    color=VoltTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=10),
                ft.Row([
                    ft.Icon("check_circle", color=VoltTheme.SUCCESS, size=16),
                    ft.Text("Sesión iniciada correctamente", size=12, color=VoltTheme.SUCCESS)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, tight=True),
            bgcolor=VoltTheme.BG_SECONDARY,
            shape=ft.RoundedRectangleBorder(radius=15),
            open=True
        )
        return self.dialogo_bienvenida
    
    def _auto_cerrar_bienvenida(self):
        """Cierra automáticamente el diálogo de bienvenida después de 3 segundos"""
        time.sleep(3)
        if hasattr(self, 'dialogo_bienvenida'):
            self.dialogo_bienvenida.open = False
            self.page.update()
    
    def _navegar(self, route):
        """Navega a una ruta específica"""
        print(f"[DEBUG] Navegando a: {route}")
        
        # Actualizar ruta actual
        self.ruta_actual = route
        
        # Cargar contenido según la ruta
        try:
            if route == "dashboard":
                nuevo_contenido = self._crear_dashboard_home()
            elif route == "productos":
                print("[DEBUG] Creando vista de productos...")
                vista_productos = ProductosView(self.page, self.empleado)
                nuevo_contenido = vista_productos.build()
                print("[DEBUG] Vista de productos creada")
            elif route == "clientes":
                print("[DEBUG] Creando vista de clientes...")
                vista_clientes = ClientesView(self.page, lambda: self._navegar("dashboard"))
                nuevo_contenido = vista_clientes.build()
                print("[DEBUG] Vista de clientes creada")
            elif route == "compras":
                print("[DEBUG] Creando vista de compras...")
                vista_compras = ComprasView(self.page, self.empleado)
                nuevo_contenido = vista_compras.build()
                print("[DEBUG] Vista de compras creada")
            elif route == "proveedores":
                print("[DEBUG] Creando vista de proveedores...")
                vista_proveedores = ProveedoresView(self.page, lambda: self._navegar("dashboard"))
                nuevo_contenido = vista_proveedores.build()
                print("[DEBUG] Vista de proveedores creada")
            elif route == "ventas":
                print("[DEBUG] Creando vista de ventas...")
                vista_ventas = VentasView(self.page, self.empleado)
                nuevo_contenido = vista_ventas.build()
                print("[DEBUG] Vista de ventas creada")
            elif route == "cajas":
                print("[DEBUG] Creando vista de cajas...")
                vista_cajas = CajasView(self.page, self.empleado)
                nuevo_contenido = vista_cajas.build()
                print("[DEBUG] Vista de cajas creada")
            elif route == "empleados":
                print("[DEBUG] Creando vista de empleados...")
                vista_empleados = EmpleadosView(self.page, self.empleado)
                nuevo_contenido = vista_empleados.build()
                print("[DEBUG] Vista de empleados creada")
            elif route == "reportes":
                print("[DEBUG] Creando vista de reportes...")
                vista_reportes = ReportesView(self.page, self.empleado)
                nuevo_contenido = vista_reportes.build()
                print("[DEBUG] Vista de reportes creada")
            elif route == "configuracion":
                print("[DEBUG] Creando vista de configuración...")
                vista_config = ConfiguracionView(self.page, self.empleado)
                nuevo_contenido = vista_config.build()
                print("[DEBUG] Vista de configuración creada")
            else:
                # Módulos en construcción
                nuevo_contenido = ft.Container(
                    content=ft.Column([
                        ft.Icon("construction", size=80, color=VoltTheme.WARNING),
                        ft.Text(
                            f"Módulo '{route}' en construcción",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=VoltTheme.TEXT_PRIMARY
                        ),
                        ft.Text(
                            "Este módulo estará disponible próximamente",
                            size=16,
                            color=VoltTheme.TEXT_SECONDARY
                        )
                    ], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20),
                    alignment=ft.alignment.center,
                    padding=50
                )
            
            # Actualizar solo el contenido
            print("[DEBUG] Actualizando contenedor...")
            self.contenedor_contenido.content = nuevo_contenido
            
            # Reconstruir sidebar para actualizar el item activo
            nuevo_sidebar = self._crear_sidebar()
            
            # Reemplazar el sidebar en el Row principal
            if self.page.controls and len(self.page.controls) > 0:
                row_principal = self.page.controls[0]
                if isinstance(row_principal, ft.Row) and len(row_principal.controls) > 0:
                    row_principal.controls[0] = nuevo_sidebar
            
            self.page.update()
            print("[DEBUG] Navegación completada")
            
        except Exception as e:
            print(f"[ERROR] Error al navegar: {e}")
            import traceback
            traceback.print_exc()
