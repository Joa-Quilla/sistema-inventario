import flet as ft
from datetime import datetime
import math
from repositories.venta_repository import VentaRepository
from repositories.cliente_repository import ClienteRepository
from repositories.producto_repository import ProductoRepository
from services.caja_service import CajaService
from models.venta import Venta, DetalleVenta
from utils.theme import VoltTheme


class VentasView:
    """Vista para gestión de Ventas (Punto de Venta)"""
    
    def __init__(self, page: ft.Page, empleado):
        self.page = page
        self.empleado = empleado
        self.venta_repo = VentaRepository()
        self.cliente_repo = ClienteRepository()
        self.producto_repo = ProductoRepository()
        self.caja_service = CajaService()
        
        # Estado
        self.ventas = []
        self.clientes = []
        self.productos = []
        self.carrito = []  # Lista de DetalleVenta
        self.caja_actual = None
        self.cliente_seleccionado = None
        
        # Paginación
        self.pagina_actual = 1
        self.items_por_pagina = 5
        
        # Referencias a controles
        self.tabla_ventas = None
        self.paginacion_container = None
        self.modal = None
        
        # Para nueva venta
        self.dropdown_cliente = None
        self.campo_busqueda_producto = None
        self.lista_sugerencias = None
        self.tabla_carrito = None
        self.texto_subtotal = None
        self.texto_descuento = None
        self.texto_total = None
        self.dropdown_metodo_pago = None
        self.campo_observaciones = None
    
    def build(self):
        """Construye la vista de ventas"""
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("Ventas / POS", size=28, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                        ft.Text("Gestión de ventas y facturación", size=14, color=VoltTheme.TEXT_SECONDARY)
                    ], spacing=5),
                    ft.ElevatedButton(
                        "Nueva Venta",
                        icon=ft.Icons.ADD_SHOPPING_CART,
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: self.abrir_modal_nueva_venta()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            padding=ft.padding.only(bottom=20)
        )
        
        # Barra de búsqueda y filtros
        self.campo_busqueda = ft.TextField(
            hint_text="Buscar por número de factura o cliente...",
            prefix_icon="search",
            width=350,
            on_submit=lambda _: self.buscar_ventas(),
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        self.campo_fecha_inicio = ft.TextField(
            label="Fecha Inicio",
            hint_text="DD/MM/YYYY",
            width=140,
            border_color=VoltTheme.BORDER_COLOR,
            prefix_icon=ft.Icons.CALENDAR_TODAY
        )
        
        self.campo_fecha_fin = ft.TextField(
            label="Fecha Fin",
            hint_text="DD/MM/YYYY",
            width=140,
            border_color=VoltTheme.BORDER_COLOR,
            prefix_icon=ft.Icons.CALENDAR_TODAY
        )
        
        self.dropdown_estado_filtro = ft.Dropdown(
            label="Estado",
            options=[
                ft.dropdown.Option(key="", text="Todos"),
                ft.dropdown.Option(key="completada", text="Completadas"),
                ft.dropdown.Option(key="anulada", text="Anuladas")
            ],
            width=150,
            value="",
            border_color=VoltTheme.BORDER_COLOR
        )
        
        barra_busqueda = ft.Container(
            content=ft.Row([
                self.campo_busqueda,
                self.campo_fecha_inicio,
                self.campo_fecha_fin,
                self.dropdown_estado_filtro,
                ft.ElevatedButton(
                    "Buscar",
                    icon=ft.Icons.SEARCH,
                    on_click=lambda _: self.buscar_ventas(),
                    bgcolor=VoltTheme.SECONDARY,
                    color=ft.Colors.WHITE
                ),
                ft.IconButton(
                    icon="refresh",
                    tooltip="Limpiar filtros",
                    on_click=lambda _: self.limpiar_filtros(),
                    icon_color=VoltTheme.PRIMARY
                )
            ], spacing=10),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            margin=ft.margin.only(bottom=20)
        )
        
        # Tabla de ventas
        self.tabla_ventas = ft.Column(spacing=0, expand=True)
        
        tabla_container = ft.Container(
            content=self.tabla_ventas,
            bgcolor=ft.Colors.WHITE,
            padding=20,
            expand=True
        )
        
        # Paginación
        self.paginacion_container = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        paginacion_wrapper = ft.Container(
            content=self.paginacion_container,
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        
        # Layout principal
        contenido = ft.Container(
            content=ft.Column([
                header,
                barra_busqueda,
                tabla_container,
                paginacion_wrapper
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            padding=30,
            bgcolor=VoltTheme.BG_PRIMARY,
            expand=True
        )
        
        # Cargar ventas
        self.cargar_ventas()
        
        return contenido
    
    def cargar_ventas(self):
        """Carga las ventas desde la base de datos"""
        try:
            # Cargar ventas con paginación
            offset = (self.pagina_actual - 1) * self.items_por_pagina
            resultado = self.venta_repo.listar(
                limit=self.items_por_pagina,
                offset=offset
            )
            
            self.ventas = resultado['ventas']
            total_ventas = resultado['total']
            
            # Actualizar tabla
            self.actualizar_tabla_ventas()
            
            # Actualizar paginación
            total_paginas = math.ceil(total_ventas / self.items_por_pagina)
            self.actualizar_paginacion(total_paginas)
            
        except Exception as e:
            print(f"Error al cargar ventas: {e}")
            self.mostrar_alerta("Error", f"No se pudieron cargar las ventas: {str(e)}", VoltTheme.DANGER)
    
    def actualizar_tabla_ventas(self):
        """Actualiza la tabla de ventas"""
        self.tabla_ventas.controls.clear()
        
        # Header de la tabla
        header = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text("Factura", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Cliente", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=2),
                ft.Container(ft.Text("Fecha", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=2),
                ft.Container(ft.Text("Total", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Método Pago", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
            ]),
            bgcolor=VoltTheme.SECONDARY,
            padding=10,
            border_radius=ft.border_radius.only(top_left=5, top_right=5)
        )
        self.tabla_ventas.controls.append(header)
        
        # Filas de datos
        for venta in self.ventas:
            fila = self._crear_fila_venta(venta)
            self.tabla_ventas.controls.append(fila)
        
        if not self.ventas:
            mensaje_vacio = ft.Container(
                content=ft.Text(
                    "No hay ventas registradas",
                    size=14,
                    color=VoltTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=40,
                alignment=ft.alignment.center
            )
            self.tabla_ventas.controls.append(mensaje_vacio)
        
        self.page.update()
    
    def _crear_fila_venta(self, venta):
        """Crea una fila para una venta"""
        # Estado color
        if venta.estado == "completada":
            estado_color = VoltTheme.SUCCESS
            estado_text = "Completada"
        else:  # anulada
            estado_color = VoltTheme.DANGER
            estado_text = "Anulada"
        
        # Formato de fecha
        fecha_str = venta.fecha_venta.strftime("%d/%m/%Y %H:%M") if venta.fecha_venta else ""
        
        # Método de pago
        metodos_pago = {
            "efectivo": "Efectivo",
            "tarjeta": "Tarjeta",
            "transferencia": "Transferencia",
            "credito": "Crédito"
        }
        metodo_texto = metodos_pago.get(venta.metodo_pago, venta.metodo_pago)
        
        fila = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text(venta.numero_factura, size=12, text_align=ft.TextAlign.CENTER), expand=1, alignment=ft.alignment.center),
                ft.Container(
                    ft.Text(venta.cliente_nombre or "Sin cliente", size=12, overflow=ft.TextOverflow.ELLIPSIS), 
                    expand=2
                ),
                ft.Container(ft.Text(fecha_str, size=12, text_align=ft.TextAlign.CENTER), expand=2, alignment=ft.alignment.center),
                ft.Container(ft.Text(f"Q {venta.total:.2f}", size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER), expand=1, alignment=ft.alignment.center),
                ft.Container(ft.Text(metodo_texto, size=12, text_align=ft.TextAlign.CENTER), expand=1, alignment=ft.alignment.center),
                ft.Container(
                    ft.Container(
                        content=ft.Text(estado_text, size=11, color=ft.Colors.WHITE),
                        bgcolor=estado_color,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=5
                    ),
                    expand=1,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Row([
                        ft.IconButton(
                            icon="visibility",
                            icon_size=18,
                            icon_color=VoltTheme.INFO,
                            tooltip="Ver detalle",
                            on_click=lambda _, v=venta: self.ver_detalle_venta(v.id_venta)
                        ),
                        ft.IconButton(
                            icon="cancel",
                            icon_size=18,
                            icon_color=VoltTheme.DANGER if venta.estado == "completada" else VoltTheme.TEXT_SECONDARY,
                            tooltip="Anular venta" if venta.estado == "completada" else "Ya anulada",
                            disabled=venta.estado != "completada",
                            on_click=lambda _, v=venta: self.confirmar_anular_venta(v.id_venta)
                        ),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    expand=1,
                    alignment=ft.alignment.center
                ),
            ], spacing=10),
            padding=10,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        return fila
    
    def actualizar_paginacion(self, total_paginas):
        """Actualiza los controles de paginación"""
        self.paginacion_container.controls.clear()
        
        if total_paginas <= 1:
            self.page.update()
            return
        
        botones = []
        
        # Botón anterior
        botones.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual - 1) if self.pagina_actual > 1 else None,
                disabled=self.pagina_actual == 1,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual > 1 else VoltTheme.TEXT_SECONDARY
            )
        )
        
        # Botones de números de página
        for i in range(1, total_paginas + 1):
            es_actual = i == self.pagina_actual
            botones.append(
                ft.Container(
                    content=ft.Text(
                        str(i),
                        size=14,
                        weight=ft.FontWeight.BOLD if es_actual else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if es_actual else VoltTheme.TEXT_PRIMARY
                    ),
                    width=35,
                    height=35,
                    bgcolor=VoltTheme.PRIMARY if es_actual else ft.Colors.TRANSPARENT,
                    border=ft.border.all(1, VoltTheme.PRIMARY) if not es_actual else None,
                    border_radius=5,
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda _, p=i: self.cambiar_pagina(p) if p != self.pagina_actual else None
                )
            )
        
        # Botón siguiente
        botones.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual + 1) if self.pagina_actual < total_paginas else None,
                disabled=self.pagina_actual == total_paginas,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual < total_paginas else VoltTheme.TEXT_SECONDARY
            )
        )
        
        self.paginacion_container.controls.extend(botones)
        self.page.update()
    
    def cambiar_pagina(self, nueva_pagina):
        """Cambia a una página diferente"""
        self.pagina_actual = nueva_pagina
        self.cargar_ventas()
    
    def buscar_ventas(self):
        """Aplica los filtros de búsqueda"""
        self.pagina_actual = 1
        self.cargar_ventas_con_filtros()
    
    def limpiar_filtros(self):
        """Limpia todos los filtros y recarga"""
        self.campo_busqueda.value = ""
        self.campo_fecha_inicio.value = ""
        self.campo_fecha_fin.value = ""
        self.dropdown_estado_filtro.value = ""
        self.pagina_actual = 1
        self.cargar_ventas()
        self.page.update()
    
    def cargar_ventas_con_filtros(self):
        """Carga las ventas aplicando filtros"""
        try:
            from datetime import datetime
            
            # Preparar parámetros de filtro
            busqueda = self.campo_busqueda.value.strip() if self.campo_busqueda.value else None
            estado = self.dropdown_estado_filtro.value if self.dropdown_estado_filtro.value else None
            
            # Parsear fechas
            fecha_inicio = None
            fecha_fin = None
            
            if self.campo_fecha_inicio.value:
                try:
                    fecha_inicio = datetime.strptime(self.campo_fecha_inicio.value, "%d/%m/%Y").date()
                except:
                    self.mostrar_alerta("Error", "Formato de fecha inicio inválido. Use DD/MM/YYYY", VoltTheme.WARNING)
                    return
            
            if self.campo_fecha_fin.value:
                try:
                    fecha_fin = datetime.strptime(self.campo_fecha_fin.value, "%d/%m/%Y").date()
                except:
                    self.mostrar_alerta("Error", "Formato de fecha fin inválido. Use DD/MM/YYYY", VoltTheme.WARNING)
                    return
            
            # Cargar ventas con paginación y filtros
            offset = (self.pagina_actual - 1) * self.items_por_pagina
            resultado = self.venta_repo.listar(
                limit=self.items_por_pagina,
                offset=offset,
                busqueda=busqueda,
                estado=estado,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            self.ventas = resultado['ventas']
            total_ventas = resultado['total']
            
            # Actualizar tabla
            self.actualizar_tabla_ventas()
            
            # Actualizar paginación
            total_paginas = math.ceil(total_ventas / self.items_por_pagina) if total_ventas > 0 else 1
            self.actualizar_paginacion(total_paginas)
            
        except Exception as e:
            print(f"Error al buscar ventas: {e}")
            self.mostrar_alerta("Error", f"No se pudieron buscar las ventas: {str(e)}", VoltTheme.DANGER)
    
    def abrir_modal_nueva_venta(self):
        """Abre el modal para crear una nueva venta"""
        try:
            # Verificar que hay caja abierta
            resultado = self.caja_service.verificar_caja_abierta(self.empleado['id_empleado'])
            if not resultado['success']:
                self.mostrar_alerta(
                    "Caja Cerrada",
                    resultado['message'],
                    VoltTheme.WARNING
                )
                return
            
            self.caja_actual = resultado['caja']
            
            # Cargar clientes
            self.clientes = self.cliente_repo.listar_todos()
            
            # Cargar productos activos con stock > 0
            self.productos = self.producto_repo.listar_activos_para_ventas()
            
            if not self.productos:
                self.mostrar_alerta(
                    "Sin productos",
                    "No hay productos disponibles con stock para vender.",
                    VoltTheme.WARNING
                )
                return
            
            # Resetear carrito y cliente
            self.carrito = []
            self.cliente_seleccionado = None
            
            # Dropdown de clientes
            opciones_clientes = [ft.dropdown.Option(key="0", text="Sin cliente (Venta rápida)")]
            opciones_clientes.extend([
                ft.dropdown.Option(
                    key=str(c.id_cliente),
                    text=f"{c.persona.nombre} {c.persona.apellido} - {c.tipo_cliente.capitalize()}"
                )
                for c in self.clientes
            ])
            
            self.dropdown_cliente = ft.Dropdown(
                label="Cliente",
                hint_text="Seleccione un cliente (opcional)",
                options=opciones_clientes,
                border_color=VoltTheme.BORDER_COLOR,
                width=500,
                on_change=self.on_cliente_seleccionado
            )
            
            # Campo de búsqueda de producto
            self.campo_busqueda_producto = ft.TextField(
                label="Buscar Producto (Código o Nombre)",
                hint_text="Escanee código de barras o escriba para buscar...",
                border_color=VoltTheme.BORDER_COLOR,
                width=450,
                autofocus=True,
                on_submit=lambda e: self.buscar_y_agregar_producto(),
                on_change=lambda e: self.filtrar_productos_sugerencias()
            )
            
            # Campo de cantidad
            self.campo_cantidad_agregar = ft.TextField(
                label="Cantidad",
                hint_text="1",
                value="1",
                width=100,
                border_color=VoltTheme.BORDER_COLOR,
                keyboard_type=ft.KeyboardType.NUMBER,
                on_submit=lambda e: self.buscar_y_agregar_producto()
            )
            
            # Lista de sugerencias
            self.lista_sugerencias = ft.Column(visible=False, spacing=0)
            
            # Tabla del carrito
            self.tabla_carrito = ft.Column(spacing=0)
            
            # Totales
            self.texto_subtotal = ft.Text("Q 0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            self.texto_descuento = ft.Text("Q 0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            self.texto_total = ft.Text("Q 0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            
            # Método de pago
            self.dropdown_metodo_pago = ft.Dropdown(
                label="Método de Pago *",
                value="efectivo",
                options=[
                    ft.dropdown.Option(key="efectivo", text="Efectivo"),
                    ft.dropdown.Option(key="tarjeta", text="Tarjeta"),
                    ft.dropdown.Option(key="transferencia", text="Transferencia"),
                    ft.dropdown.Option(key="credito", text="Crédito")
                ],
                border_color=VoltTheme.BORDER_COLOR,
                width=200
            )
            
            self.campo_observaciones = ft.TextField(
                label="Observaciones",
                multiline=True,
                min_lines=2,
                max_lines=3,
                border_color=VoltTheme.BORDER_COLOR
            )
            
            # Contenido del modal
            contenido_modal = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.POINT_OF_SALE, color=VoltTheme.PRIMARY, size=30),
                        ft.Text("Nueva Venta", size=24, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(
                                "📄 Factura: Automática",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=VoltTheme.SUCCESS
                            ),
                            bgcolor=ft.Colors.GREEN_50,
                            padding=8,
                            border_radius=5
                        )
                    ]),
                    ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                    
                    # Información de caja
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=VoltTheme.SUCCESS, size=20),
                            ft.Text(
                                f"Caja Abierta - Monto Inicial: Q {self.caja_actual['monto_inicial']:.2f}",
                                size=14,
                                color=VoltTheme.SUCCESS,
                                weight=ft.FontWeight.BOLD
                            )
                        ], spacing=10),
                        bgcolor=ft.Colors.GREEN_50,
                        padding=10,
                        border_radius=5,
                        margin=ft.margin.only(bottom=10)
                    ),
                    
                    # Cliente
                    self.dropdown_cliente,
                    
                    ft.Divider(height=1),
                    
                    # Búsqueda de productos
                    ft.Text("🔍 Escanear/Buscar Producto", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.QR_CODE_SCANNER, size=24, color=VoltTheme.INFO),
                            self.campo_busqueda_producto,
                            self.campo_cantidad_agregar,
                        ], spacing=10),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=10,
                        border_radius=5
                    ),
                    self.lista_sugerencias,
                    
                    ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                    
                    # Carrito
                    ft.Text("🛒 Carrito de Compra", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.tabla_carrito,
                        border=ft.border.all(1, VoltTheme.BORDER_COLOR),
                        border_radius=5,
                        padding=10,
                        height=200
                    ),
                    
                    # Totales
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Subtotal:", size=14, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                self.texto_subtotal
                            ]),
                            ft.Row([
                                ft.Text("Descuento:", size=14, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                self.texto_descuento
                            ]),
                            ft.Divider(height=1, color=ft.Colors.WHITE70),
                            ft.Row([
                                ft.Text("TOTAL:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                self.texto_total
                            ]),
                        ], spacing=5),
                        bgcolor=VoltTheme.SECONDARY,
                        padding=15,
                        border_radius=5
                    ),
                    
                    # Método de pago y observaciones
                    ft.Row([
                        self.dropdown_metodo_pago,
                        self.campo_observaciones,
                    ], spacing=10),
                    
                    # Botones
                    ft.Row([
                        ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                        ft.ElevatedButton(
                            "Realizar Venta",
                            icon=ft.Icons.SHOPPING_CART_CHECKOUT,
                            bgcolor=VoltTheme.PRIMARY,
                            color=ft.Colors.WHITE,
                            on_click=lambda _: self.guardar_venta()
                        ),
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ], scroll=ft.ScrollMode.AUTO, spacing=15),
                padding=20,
                width=900,
                height=700,
                bgcolor=ft.Colors.WHITE
            )
            
            self.modal = ft.AlertDialog(
                modal=True,
                content=contenido_modal
            )
            
            self.page.open(self.modal)
            self.actualizar_vista_carrito()
            
        except Exception as e:
            print(f"Error al abrir modal: {e}")
            self.mostrar_alerta("Error", f"No se pudo abrir el formulario: {str(e)}", VoltTheme.DANGER)
    
    def on_cliente_seleccionado(self, e):
        """Maneja la selección de un cliente"""
        id_cliente = e.control.value
        
        if id_cliente == "0":
            self.cliente_seleccionado = None
        else:
            # Buscar el cliente seleccionado
            self.cliente_seleccionado = next(
                (c for c in self.clientes if str(c.id_cliente) == id_cliente),
                None
            )
        
        # Recalcular totales con descuento del cliente
        self.calcular_totales()
    
    def filtrar_productos_sugerencias(self):
        """Muestra sugerencias de productos mientras se escribe"""
        try:
            busqueda = self.campo_busqueda_producto.value.strip().lower()
            
            if not busqueda or len(busqueda) < 2:
                self.lista_sugerencias.visible = False
                self.lista_sugerencias.controls.clear()
                self.page.update()
                return
            
            # Filtrar productos
            productos_filtrados = [
                p for p in self.productos
                if busqueda in p.codigo.lower() or busqueda in p.nombre.lower()
            ][:5]  # Máximo 5 sugerencias
            
            self.lista_sugerencias.controls.clear()
            
            if productos_filtrados:
                for producto in productos_filtrados:
                    btn_sugerencia = ft.Container(
                        content=ft.Row([
                            ft.Text(producto.codigo, size=12, weight=ft.FontWeight.BOLD, width=100),
                            ft.Text(producto.nombre, size=12, width=250),
                            ft.Text(f"Stock: {producto.stock_actual}", size=11, color=VoltTheme.TEXT_SECONDARY, width=80),
                            ft.Text(f"Q{float(producto.precio_venta):.2f}", size=12, weight=ft.FontWeight.BOLD),
                        ]),
                        bgcolor=ft.Colors.WHITE,
                        padding=8,
                        border=ft.border.all(1, VoltTheme.BORDER_COLOR),
                        border_radius=3,
                        on_click=lambda _, p=producto: self.agregar_producto_desde_sugerencia(p),
                        ink=True
                    )
                    self.lista_sugerencias.controls.append(btn_sugerencia)
                
                self.lista_sugerencias.visible = True
            else:
                self.lista_sugerencias.visible = False
            
            self.page.update()
            
        except Exception as e:
            print(f"Error al filtrar productos: {e}")
    
    def buscar_y_agregar_producto(self):
        """Busca un producto por código exacto y lo agrega al carrito (para scanner)"""
        try:
            busqueda = self.campo_busqueda_producto.value.strip().upper()
            
            if not busqueda:
                return
            
            # Buscar producto por código exacto primero (para scanner)
            producto = next((p for p in self.productos if p.codigo.upper() == busqueda), None)
            
            # Si no se encuentra por código exacto, buscar por nombre
            if not producto:
                productos_coincidentes = [
                    p for p in self.productos
                    if busqueda in p.nombre.upper() or busqueda in p.codigo.upper()
                ]
                
                if len(productos_coincidentes) == 1:
                    producto = productos_coincidentes[0]
                elif len(productos_coincidentes) > 1:
                    # Si hay múltiples coincidencias, mostrar sugerencias
                    self.mostrar_alerta(
                        "Múltiples productos",
                        "Se encontraron varios productos. Use las sugerencias o sea más específico.",
                        VoltTheme.INFO
                    )
                    return
            
            if not producto:
                self.mostrar_alerta(
                    "Producto no encontrado",
                    f"No se encontró el producto: {busqueda}",
                    VoltTheme.WARNING
                )
                return
            
            self.agregar_producto_desde_sugerencia(producto)
            
        except Exception as e:
            print(f"Error al buscar producto: {e}")
            self.mostrar_alerta("Error", f"Error al buscar producto: {str(e)}", VoltTheme.DANGER)
    
    def agregar_producto_desde_sugerencia(self, producto):
        """Agrega un producto al carrito (desde sugerencia o búsqueda directa)"""
        try:
            # Obtener cantidad del campo
            try:
                cantidad_agregar = int(self.campo_cantidad_agregar.value or 1)
                if cantidad_agregar <= 0:
                    cantidad_agregar = 1
            except:
                cantidad_agregar = 1
            
            # Verificar si ya está en el carrito
            detalle_existente = next((d for d in self.carrito if d.id_producto == producto.id_producto), None)
            
            if detalle_existente:
                # Si ya existe, sumar la cantidad especificada
                cantidad_nueva = detalle_existente.cantidad + cantidad_agregar
                
                # Verificar stock
                if cantidad_nueva > producto.stock_actual:
                    self.mostrar_alerta(
                        "Stock Insuficiente",
                        f"{producto.nombre}: Stock disponible {producto.stock_actual}. Ya tiene {detalle_existente.cantidad} en el carrito.",
                        VoltTheme.WARNING
                    )
                    return
                
                detalle_existente.cantidad = cantidad_nueva
                detalle_existente.calcular_subtotal()
            else:
                # Verificar stock disponible
                if producto.stock_actual < cantidad_agregar:
                    self.mostrar_alerta(
                        "Stock Insuficiente",
                        f"{producto.nombre}: Stock disponible {producto.stock_actual}. Solicitado: {cantidad_agregar}",
                        VoltTheme.WARNING
                    )
                    return
                
                # Crear nuevo detalle
                detalle = DetalleVenta(
                    id_venta=None,
                    id_producto=producto.id_producto,
                    cantidad=cantidad_agregar,
                    precio_unitario=float(producto.precio_venta),
                    subtotal=0,
                    producto_codigo=producto.codigo,
                    producto_nombre=producto.nombre
                )
                detalle.calcular_subtotal()
                self.carrito.append(detalle)
            
            # Limpiar búsqueda, resetear cantidad y ocultar sugerencias
            self.campo_busqueda_producto.value = ""
            self.campo_cantidad_agregar.value = "1"
            self.lista_sugerencias.visible = False
            self.lista_sugerencias.controls.clear()
            
            # Actualizar vista
            self.actualizar_vista_carrito()
            self.campo_busqueda_producto.focus()
            self.page.update()
            
        except Exception as e:
            print(f"Error al agregar producto: {e}")
            self.mostrar_alerta("Error", f"Error al agregar producto: {str(e)}", VoltTheme.DANGER)
    
    def actualizar_vista_carrito(self):
        """Actualiza la vista del carrito"""
        self.tabla_carrito.controls.clear()
        
        if not self.carrito:
            self.tabla_carrito.controls.append(
                ft.Text("No hay productos en el carrito", color=VoltTheme.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER)
            )
        else:
            # Header
            header = ft.Container(
                content=ft.Row([
                    ft.Container(ft.Text("Código", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=80),
                    ft.Container(ft.Text("Producto", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), expand=2),
                    ft.Container(ft.Text("Cantidad", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=120),
                    ft.Container(ft.Text("Precio Unit.", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=90),
                    ft.Container(ft.Text("Subtotal", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=90),
                    ft.Container(ft.Text("", size=11), width=50),
                ], spacing=5),
                bgcolor=VoltTheme.SECONDARY,
                padding=8,
                border_radius=5
            )
            self.tabla_carrito.controls.append(header)
            
            # Filas de productos
            for detalle in self.carrito:
                fila = self._crear_fila_carrito(detalle)
                self.tabla_carrito.controls.append(fila)
        
        # Calcular totales
        self.calcular_totales()
        self.page.update()
    
    def _crear_fila_carrito(self, detalle):
        """Crea una fila para un producto en el carrito"""
        fila = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text(detalle.producto_codigo, size=11), width=80),
                ft.Container(ft.Text(detalle.producto_nombre, size=11, overflow=ft.TextOverflow.ELLIPSIS), expand=2),
                ft.Container(
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.REMOVE,
                            icon_size=16,
                            icon_color=VoltTheme.DANGER,
                            on_click=lambda _, d=detalle: self.cambiar_cantidad_carrito(d, -1)
                        ),
                        ft.Text(str(detalle.cantidad), size=12, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_size=16,
                            icon_color=VoltTheme.SUCCESS,
                            on_click=lambda _, d=detalle: self.cambiar_cantidad_carrito(d, 1)
                        ),
                    ], spacing=0),
                    width=120
                ),
                ft.Container(ft.Text(f"Q {detalle.precio_unitario:.2f}", size=11), width=90),
                ft.Container(ft.Text(f"Q {detalle.subtotal:.2f}", size=11, weight=ft.FontWeight.BOLD), width=90),
                ft.Container(
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_size=18,
                        icon_color=VoltTheme.DANGER,
                        on_click=lambda _, d=detalle: self.eliminar_del_carrito(d)
                    ),
                    width=50
                ),
            ], spacing=5),
            padding=5,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        return fila
    
    def cambiar_cantidad_carrito(self, detalle, cambio):
        """Cambia la cantidad de un producto en el carrito"""
        try:
            nueva_cantidad = detalle.cantidad + cambio
            
            if nueva_cantidad <= 0:
                self.eliminar_del_carrito(detalle)
                return
            
            # Buscar el producto para verificar stock
            producto = next((p for p in self.productos if p.id_producto == detalle.id_producto), None)
            if producto and nueva_cantidad > producto.stock_actual:
                self.mostrar_alerta(
                    "Stock Insuficiente",
                    f"Stock disponible: {producto.stock_actual}",
                    VoltTheme.WARNING
                )
                return
            
            detalle.cantidad = nueva_cantidad
            detalle.calcular_subtotal()
            self.actualizar_vista_carrito()
            
        except Exception as e:
            print(f"Error al cambiar cantidad: {e}")
    
    def eliminar_del_carrito(self, detalle):
        """Elimina un producto del carrito"""
        try:
            self.carrito.remove(detalle)
            self.actualizar_vista_carrito()
        except Exception as e:
            print(f"Error al eliminar del carrito: {e}")
    
    def calcular_totales(self):
        """Calcula los totales de la venta"""
        subtotal = sum(d.subtotal for d in self.carrito)
        
        # Aplicar descuento del cliente si hay uno seleccionado
        descuento = 0.0
        if self.cliente_seleccionado and self.cliente_seleccionado.descuento_habitual > 0:
            descuento = subtotal * (self.cliente_seleccionado.descuento_habitual / 100)
        
        total = subtotal - descuento
        
        self.texto_subtotal.value = f"Q {subtotal:.2f}"
        self.texto_descuento.value = f"Q {descuento:.2f}"
        if self.cliente_seleccionado and descuento > 0:
            self.texto_descuento.value += f" ({self.cliente_seleccionado.descuento_habitual}%)"
        self.texto_total.value = f"Q {total:.2f}"
        
        self.page.update()
    
    def generar_numero_factura(self):
        """Genera un número de factura automático"""
        try:
            # Obtener el último número de factura
            ultima_venta = self.venta_repo.obtener_ultima_factura()
            
            if ultima_venta and ultima_venta.get('numero_factura'):
                # Extraer el número y sumar 1
                ultimo_num = ultima_venta['numero_factura']
                # Si el formato es FACT-00001, extraer el número
                if '-' in ultimo_num:
                    partes = ultimo_num.split('-')
                    numero = int(partes[-1]) + 1
                else:
                    # Si es solo número
                    try:
                        numero = int(ultimo_num) + 1
                    except:
                        numero = 1
            else:
                numero = 1
            
            # Generar factura con formato FACT-00001
            return f"FACT-{numero:05d}"
            
        except Exception as e:
            print(f"Error al generar número de factura: {e}")
            # Si hay error, usar timestamp
            import time
            return f"FACT-{int(time.time())}"
    
    def guardar_venta(self):
        """Guarda la nueva venta"""
        try:
            # Validaciones
            if not self.carrito:
                self.mostrar_alerta("Error", "Debe agregar al menos un producto", VoltTheme.WARNING)
                return
            
            if not self.dropdown_metodo_pago.value:
                self.mostrar_alerta("Error", "Seleccione un método de pago", VoltTheme.WARNING)
                return
            
            # Generar número de factura automático
            numero_factura = self.generar_numero_factura()
            
            # Calcular totales
            subtotal = sum(d.subtotal for d in self.carrito)
            descuento = 0.0
            if self.cliente_seleccionado and self.cliente_seleccionado.descuento_habitual > 0:
                descuento = subtotal * (self.cliente_seleccionado.descuento_habitual / 100)
            total = subtotal - descuento
            
            # Crear objeto venta
            venta = Venta(
                numero_factura=numero_factura,
                id_cliente=self.cliente_seleccionado.id_cliente if self.cliente_seleccionado else None,
                id_empleado=self.empleado['id_empleado'],
                id_caja=self.caja_actual['id_caja'],
                subtotal=subtotal,
                descuento=descuento,
                total=total,
                metodo_pago=self.dropdown_metodo_pago.value,
                observaciones=self.campo_observaciones.value or None
            )
            
            # Asignar detalles
            venta.detalles = self.carrito
            
            # Guardar venta
            resultado = self.venta_repo.crear(venta, self.caja_actual['id_caja'])
            
            if resultado['success']:
                # Obtener la venta completa para imprimir
                venta_guardada = self.venta_repo.obtener_por_id(resultado['id_venta'])
                
                self.cerrar_modal()
                self.cargar_ventas()
                
                # Mostrar diálogo de impresión
                self.mostrar_dialogo_imprimir(venta_guardada)
            else:
                self.mostrar_alerta("Error", resultado['message'], VoltTheme.DANGER)
                
        except Exception as e:
            print(f"Error al guardar venta: {e}")
            self.mostrar_alerta("Error", f"No se pudo guardar la venta: {str(e)}", VoltTheme.DANGER)
    
    def ver_detalle_venta(self, id_venta):
        """Muestra el detalle de una venta"""
        try:
            venta = self.venta_repo.obtener_por_id(id_venta)
            if not venta:
                self.mostrar_alerta("Error", "No se encontró la venta", VoltTheme.DANGER)
                return
            
            # Crear tabla de productos
            tabla_productos = ft.Column(spacing=0)
            
            # Header
            header = ft.Container(
                content=ft.Row([
                    ft.Container(ft.Text("Código", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=80),
                    ft.Container(ft.Text("Producto", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), expand=2),
                    ft.Container(ft.Text("Cant.", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=60),
                    ft.Container(ft.Text("Precio", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=80),
                    ft.Container(ft.Text("Subtotal", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=80),
                ], spacing=5),
                bgcolor=VoltTheme.SECONDARY,
                padding=8,
                border_radius=5
            )
            tabla_productos.controls.append(header)
            
            # Productos
            for detalle in venta.detalles:
                fila = ft.Container(
                    content=ft.Row([
                        ft.Container(ft.Text(detalle.producto_codigo, size=11), width=80),
                        ft.Container(ft.Text(detalle.producto_nombre, size=11), expand=2),
                        ft.Container(ft.Text(str(detalle.cantidad), size=11), width=60),
                        ft.Container(ft.Text(f"Q{detalle.precio_unitario:.2f}", size=11), width=80),
                        ft.Container(ft.Text(f"Q{detalle.subtotal:.2f}", size=11, weight=ft.FontWeight.BOLD), width=80),
                    ], spacing=5),
                    padding=5,
                    border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
                )
                tabla_productos.controls.append(fila)
            
            # Contenido del modal
            contenido = ft.Container(
                content=ft.Column([
                    ft.Text(f"Detalle de Venta - {venta.numero_factura}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    
                    # Información general
                    ft.Row([
                        ft.Column([
                            ft.Text(f"Cliente: {venta.cliente_nombre or 'Sin cliente'}", size=12),
                            ft.Text(f"Empleado: {venta.empleado_nombre}", size=12),
                            ft.Text(f"Fecha: {venta.fecha_venta.strftime('%d/%m/%Y %H:%M')}", size=12),
                        ], spacing=5),
                        ft.Container(expand=True),
                        ft.Column([
                            ft.Text(f"Método de pago: {venta.metodo_pago.capitalize()}", size=12),
                            ft.Container(
                                content=ft.Text(
                                    venta.estado.capitalize(),
                                    size=12,
                                    color=ft.Colors.WHITE
                                ),
                                bgcolor=VoltTheme.SUCCESS if venta.estado == "completada" else VoltTheme.DANGER,
                                padding=8,
                                border_radius=5
                            )
                        ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.END)
                    ]),
                    
                    ft.Divider(),
                    
                    # Tabla de productos
                    ft.Text("Productos", size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=tabla_productos,
                        border=ft.border.all(1, VoltTheme.BORDER_COLOR),
                        border_radius=5,
                        padding=5,
                        height=200
                    ),
                    
                    # Totales
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Subtotal:", size=14, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                ft.Text(f"Q {venta.subtotal:.2f}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                            ]),
                            ft.Row([
                                ft.Text("Descuento:", size=14, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                ft.Text(f"Q {venta.descuento:.2f}", size=14, color=ft.Colors.WHITE)
                            ]),
                            ft.Divider(height=1, color=ft.Colors.WHITE70),
                            ft.Row([
                                ft.Text("TOTAL:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                ft.Text(f"Q {venta.total:.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                            ]),
                        ], spacing=5),
                        bgcolor=VoltTheme.SECONDARY,
                        padding=15,
                        border_radius=5
                    ),
                    
                    # Observaciones
                    ft.Text(f"Observaciones: {venta.observaciones or 'N/A'}", size=12),
                    
                    # Botones
                    ft.Row([
                        ft.ElevatedButton(
                            "Imprimir Comprobante",
                            icon=ft.Icons.PRINT,
                            on_click=lambda _: self.imprimir_comprobante(venta),
                            bgcolor=VoltTheme.SUCCESS,
                            color=ft.Colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "Cerrar",
                            on_click=lambda _: self.cerrar_modal(),
                            bgcolor=VoltTheme.PRIMARY,
                            color=ft.Colors.WHITE
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=15, scroll=ft.ScrollMode.AUTO),
                padding=20,
                width=700,
                height=600,
                bgcolor=ft.Colors.WHITE
            )
            
            self.modal = ft.AlertDialog(
                modal=True,
                content=contenido
            )
            
            self.page.open(self.modal)
            
        except Exception as e:
            print(f"Error al ver detalle: {e}")
            self.mostrar_alerta("Error", f"No se pudo cargar el detalle: {str(e)}", VoltTheme.DANGER)
    
    def confirmar_anular_venta(self, id_venta):
        """Confirma la anulación de una venta"""
        def anular():
            self.cerrar_modal()
            resultado = self.venta_repo.anular(id_venta, self.empleado['id_empleado'])
            
            if resultado['success']:
                self.mostrar_alerta("Éxito", resultado['message'], VoltTheme.SUCCESS)
                self.cargar_ventas()
            else:
                self.mostrar_alerta("Error", resultado['message'], VoltTheme.DANGER)
        
        self.modal = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=VoltTheme.WARNING, size=30),
                ft.Text("¿Anular Venta?", weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Text(
                "Esta acción devolverá el stock de los productos y registrará un egreso en la caja.",
                size=14
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                ft.ElevatedButton(
                    "Sí, Anular",
                    bgcolor=VoltTheme.DANGER,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: anular()
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(self.modal)
    
    def cerrar_modal(self):
        """Cierra el modal actual"""
        if self.modal:
            self.page.close(self.modal)
            self.modal = None
            self.page.update()
    
    def mostrar_alerta(self, titulo, mensaje, tipo=VoltTheme.INFO):
        """Muestra una alerta al usuario"""
        # Determinar icono según tipo
        if tipo == VoltTheme.SUCCESS:
            icono = ft.Icons.CHECK_CIRCLE
            color_icono = VoltTheme.SUCCESS
        elif tipo == VoltTheme.DANGER:
            icono = ft.Icons.ERROR
            color_icono = VoltTheme.DANGER
        elif tipo == VoltTheme.WARNING:
            icono = ft.Icons.WARNING
            color_icono = VoltTheme.WARNING
        else:
            icono = ft.Icons.INFO
            color_icono = VoltTheme.INFO
        
        alerta = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(icono, color=color_icono, size=30),
                ft.Text(titulo, size=20, weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Text(mensaje, size=14),
            actions=[
                ft.TextButton("Aceptar", on_click=lambda _: self.page.close(alerta))
            ]
        )
        
        self.page.open(alerta)
    
    def mostrar_dialogo_imprimir(self, venta):
        """Muestra diálogo para imprimir comprobante después de crear venta"""
        contenido = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=60, color=VoltTheme.SUCCESS),
                ft.Text("¡Venta Registrada Exitosamente!", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Factura N°: {venta.numero_factura}", size=16, color=VoltTheme.PRIMARY),
                ft.Text(f"Total: Q {venta.total:.2f}", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("¿Desea imprimir el comprobante?", size=14),
                ft.Row([
                    ft.ElevatedButton(
                        "Seguir",
                        icon=ft.Icons.ARROW_FORWARD,
                        on_click=lambda _: self.cerrar_modal(),
                        bgcolor=VoltTheme.SECONDARY,
                        color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Imprimir Comprobante",
                        icon=ft.Icons.PRINT,
                        on_click=lambda _: self.imprimir_y_cerrar(venta),
                        bgcolor=VoltTheme.SUCCESS,
                        color=ft.Colors.WHITE
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10)
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            padding=30,
            width=450,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def imprimir_y_cerrar(self, venta):
        """Imprime el comprobante y cierra el diálogo"""
        self.imprimir_comprobante(venta)
        self.cerrar_modal()
    
    def imprimir_comprobante(self, venta):
        """Genera e imprime el comprobante de venta en PDF"""
        try:
            import os
            from datetime import datetime
            
            # Verificar si reportlab está instalado
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.units import inch
                from reportlab.pdfgen import canvas
                from reportlab.lib import colors
            except ImportError:
                self.mostrar_alerta(
                    "Biblioteca no disponible",
                    "Para generar PDF necesita instalar: pip install reportlab\n\nGenerando archivo de texto como alternativa...",
                    VoltTheme.WARNING
                )
                self.imprimir_comprobante_txt(venta)
                return
            
            # Crear directorio de comprobantes si no existe
            comprobantes_dir = os.path.join(os.getcwd(), "comprobantes")
            if not os.path.exists(comprobantes_dir):
                os.makedirs(comprobantes_dir)
            
            # Nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"comprobante_{venta.numero_factura.replace('/', '_')}_{timestamp}.pdf"
            ruta_archivo = os.path.join(comprobantes_dir, nombre_archivo)
            
            # Crear PDF
            c = canvas.Canvas(ruta_archivo, pagesize=letter)
            width, height = letter
            
            # Título
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height - 50, "SISTEMA DE INVENTARIO")
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width/2, height - 70, "COMPROBANTE DE VENTA")
            
            # Línea separadora
            c.line(50, height - 85, width - 50, height - 85)
            
            # Información de la venta
            y = height - 110
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, f"Factura N°:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y, venta.numero_factura)
            
            y -= 20
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, f"Fecha:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y, venta.fecha_venta.strftime('%d/%m/%Y %H:%M:%S'))
            
            y -= 20
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, f"Empleado:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y, venta.empleado_nombre)
            
            y -= 20
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, f"Cliente:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y, venta.cliente_nombre or 'Sin cliente')
            
            y -= 20
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, f"Método de Pago:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y, venta.metodo_pago.capitalize())
            
            # Línea separadora
            y -= 15
            c.line(50, y, width - 50, y)
            
            # Encabezado de productos
            y -= 25
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "Código")
            c.drawString(120, y, "Producto")
            c.drawString(320, y, "Cant.")
            c.drawString(380, y, "P.Unit")
            c.drawString(470, y, "Subtotal")
            
            y -= 5
            c.line(50, y, width - 50, y)
            
            # Productos
            y -= 20
            c.setFont("Helvetica", 9)
            for detalle in venta.detalles:
                if y < 100:  # Nueva página si es necesario
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 9)
                
                c.drawString(50, y, detalle.producto_codigo[:10])
                c.drawString(120, y, detalle.producto_nombre[:25])
                c.drawString(330, y, str(detalle.cantidad))
                c.drawString(380, y, f"Q {detalle.precio_unitario:.2f}")
                c.drawString(470, y, f"Q {detalle.subtotal:.2f}")
                y -= 15
            
            # Línea antes de totales
            y -= 10
            c.line(50, y, width - 50, y)
            
            # Totales
            y -= 25
            c.setFont("Helvetica", 11)
            c.drawString(380, y, "Subtotal:")
            c.drawString(470, y, f"Q {venta.subtotal:.2f}")
            
            y -= 20
            c.drawString(380, y, "Descuento:")
            c.drawString(470, y, f"Q {venta.descuento:.2f}")
            
            y -= 5
            c.line(380, y, width - 50, y)
            
            y -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(380, y, "TOTAL:")
            c.drawString(470, y, f"Q {venta.total:.2f}")
            
            # Observaciones
            if venta.observaciones:
                y -= 30
                c.setFont("Helvetica", 9)
                c.drawString(50, y, f"Observaciones: {venta.observaciones}")
            
            # Pie de página
            y = 50
            c.setFont("Helvetica", 9)
            c.drawCentredString(width/2, y, "¡Gracias por su compra!")
            y -= 15
            c.drawCentredString(width/2, y, f"Documento generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Guardar PDF
            c.save()
            
            # Intentar abrir el archivo
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(ruta_archivo)
                elif os.name == 'posix':  # Linux/Mac
                    os.system(f'xdg-open "{ruta_archivo}"')
                
                self.mostrar_alerta(
                    "Comprobante Generado",
                    f"El comprobante PDF se guardó en:\n{ruta_archivo}\n\nSe abrirá automáticamente.",
                    VoltTheme.SUCCESS
                )
            except:
                self.mostrar_alerta(
                    "Comprobante Guardado",
                    f"El comprobante se guardó en:\n{ruta_archivo}\n\nPuede abrirlo manualmente.",
                    VoltTheme.SUCCESS
                )
            
        except Exception as e:
            print(f"Error al generar comprobante PDF: {e}")
            self.mostrar_alerta(
                "Error",
                f"No se pudo generar el comprobante: {str(e)}",
                VoltTheme.DANGER
            )
    
    def imprimir_comprobante_txt(self, venta):
        """Genera comprobante en formato TXT como alternativa"""
        try:
            import os
            from datetime import datetime
            
            # Crear directorio de comprobantes si no existe
            comprobantes_dir = os.path.join(os.getcwd(), "comprobantes")
            if not os.path.exists(comprobantes_dir):
                os.makedirs(comprobantes_dir)
            
            # Nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"comprobante_{venta.numero_factura.replace('/', '_')}_{timestamp}.txt"
            ruta_archivo = os.path.join(comprobantes_dir, nombre_archivo)
            
            # Generar contenido del comprobante
            linea = "=" * 50
            contenido = f"""
{linea}
           SISTEMA DE INVENTARIO
              COMPROBANTE DE VENTA
{linea}

Factura N°:         {venta.numero_factura}
Fecha:              {venta.fecha_venta.strftime('%d/%m/%Y %H:%M:%S')}
Empleado:           {venta.empleado_nombre}
Cliente:            {venta.cliente_nombre or 'Sin cliente'}
Método de Pago:     {venta.metodo_pago.capitalize()}
Estado:             {venta.estado.capitalize()}

{linea}
DETALLE DE PRODUCTOS
{linea}
{'Código':<12} {'Producto':<25} {'Cant.':<6} {'P.Unit':<10} {'Subtotal':<10}
{'-'*50}
"""
            
            # Agregar productos
            for detalle in venta.detalles:
                contenido += f"{detalle.producto_codigo:<12} {detalle.producto_nombre[:25]:<25} {detalle.cantidad:<6} Q{detalle.precio_unitario:<9.2f} Q{detalle.subtotal:<9.2f}\n"
            
            # Agregar totales
            contenido += f"""
{linea}
{'Subtotal:':<40} Q{venta.subtotal:>8.2f}
{'Descuento:':<40} Q{venta.descuento:>8.2f}
{'-'*50}
{'TOTAL:':<40} Q{venta.total:>8.2f}
{linea}

"""
            
            # Agregar observaciones si hay
            if venta.observaciones:
                contenido += f"Observaciones: {venta.observaciones}\n\n"
            
            contenido += f"""
        ¡Gracias por su compra!
            
{linea}
Documento generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
            
            # Guardar archivo
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            # Intentar abrir el archivo con el programa predeterminado
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(ruta_archivo)
                elif os.name == 'posix':  # Linux/Mac
                    os.system(f'xdg-open "{ruta_archivo}"')
                
                self.mostrar_alerta(
                    "Comprobante Generado",
                    f"El comprobante se guardó en:\n{ruta_archivo}\n\nSe abrirá automáticamente para imprimir.",
                    VoltTheme.SUCCESS
                )
            except Exception as e:
                self.mostrar_alerta(
                    "Comprobante Guardado",
                    f"El comprobante se guardó en:\n{ruta_archivo}\n\nPuede abrirlo manualmente para imprimir.",
                    VoltTheme.SUCCESS
                )
            
        except Exception as e:
            print(f"Error al generar comprobante: {e}")
            self.mostrar_alerta(
                "Error",
                f"No se pudo generar el comprobante: {str(e)}",
                VoltTheme.DANGER
            )
