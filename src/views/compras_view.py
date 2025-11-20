import flet as ft
from datetime import datetime
import math
from repositories.compra_repository import CompraRepository
from repositories.proveedor_repository import ProveedorRepository
from repositories.producto_repository import ProductoRepository
from models.compra import Compra, DetalleCompra
from utils.theme import VoltTheme


class ComprasView:
    def __init__(self, page: ft.Page, empleado):
        self.page = page
        self.empleado = empleado
        self.compra_repo = CompraRepository()
        self.proveedor_repo = ProveedorRepository()
        self.producto_repo = ProductoRepository()
        
        # Estado
        self.compras = []
        self.proveedores = []
        self.productos = []
        self.carrito = []  # Lista de DetalleCompra
        
        # Paginación
        self.pagina_actual = 1
        self.items_por_pagina = 5
        
        # Búsqueda y filtros
        self.busqueda_actual = ""
        self.fecha_desde = None
        self.fecha_hasta = None
        
        # Referencias a controles
        self.tabla_compras = None
        self.paginacion_container = None
        self.modal = None
        self.campo_busqueda = None
        self.campo_fecha_desde = None
        self.campo_fecha_hasta = None
        
        # Para nueva compra
        self.dropdown_proveedor = None
        self.dropdown_producto = None
        self.campo_cantidad = None
        self.campo_precio = None
        self.tabla_carrito = None
        self.texto_total = None
        self.campo_numero_factura = None
        self.campo_observaciones = None
    
    def build(self):
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=VoltTheme.PRIMARY,
                    on_click=lambda _: self.page.go("/dashboard"),
                    tooltip="Volver al Dashboard"
                ),
                ft.Text(
                    "Gestión de Compras",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        # Barra de búsqueda y filtros
        self.campo_busqueda = ft.TextField(
            hint_text="Buscar por número de factura o proveedor...",
            prefix_icon=ft.Icons.SEARCH,
            width=350,
            on_change=lambda e: self.buscar_compras(e.control.value),
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        self.campo_fecha_desde = ft.TextField(
            label="Desde",
            hint_text="DD/MM/AAAA",
            width=130,
            on_change=lambda e: self.filtrar_por_fecha(),
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        self.campo_fecha_hasta = ft.TextField(
            label="Hasta",
            hint_text="DD/MM/AAAA",
            width=130,
            on_change=lambda e: self.filtrar_por_fecha(),
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        barra_busqueda = ft.Container(
            content=ft.Row([
                self.campo_busqueda,
                self.campo_fecha_desde,
                self.campo_fecha_hasta,
                ft.IconButton(
                    icon=ft.Icons.CLEAR,
                    tooltip="Limpiar filtros",
                    on_click=lambda _: self.limpiar_filtros(),
                    icon_color=VoltTheme.WARNING
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Recargar",
                    on_click=lambda _: self.cargar_compras(),
                    icon_color=VoltTheme.PRIMARY
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Nueva Compra",
                    icon=ft.Icons.ADD,
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.abrir_modal_nueva_compra()
                ),
            ], spacing=10, alignment=ft.MainAxisAlignment.START),
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        
        # Tabla de compras
        self.tabla_compras = ft.Column(
            spacing=0,
            scroll=ft.ScrollMode.AUTO
        )
        
        tabla_container = ft.Container(
            content=self.tabla_compras,
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
        content = ft.Column([
            header,
            barra_busqueda,
            tabla_container,
            paginacion_wrapper
        ], spacing=0, expand=True)
        
        # Cargar datos iniciales
        self.cargar_compras()
        
        return content
    
    def cargar_compras(self):
        """Carga la lista de compras desde la base de datos"""
        try:
            self.compras = self.compra_repo.listar()
            self.busqueda_actual = ""
            self.fecha_desde = None
            self.fecha_hasta = None
            if self.campo_busqueda:
                self.campo_busqueda.value = ""
            if self.campo_fecha_desde:
                self.campo_fecha_desde.value = ""
            if self.campo_fecha_hasta:
                self.campo_fecha_hasta.value = ""
            self.pagina_actual = 1
            self.actualizar_tabla()
            self.actualizar_paginacion()
        except Exception as e:
            self.mostrar_mensaje("Error", f"Error al cargar compras: {str(e)}", "error")
    
    def limpiar_filtros(self):
        """Limpia todos los filtros aplicados"""
        self.busqueda_actual = ""
        self.fecha_desde = None
        self.fecha_hasta = None
        if self.campo_busqueda:
            self.campo_busqueda.value = ""
        if self.campo_fecha_desde:
            self.campo_fecha_desde.value = ""
        if self.campo_fecha_hasta:
            self.campo_fecha_hasta.value = ""
        self.pagina_actual = 1
        self.actualizar_tabla()
        self.actualizar_paginacion()
        self.page.update()
    
    def filtrar_por_fecha(self):
        """Filtra las compras por rango de fechas"""
        try:
            # Parsear fecha desde
            if self.campo_fecha_desde.value.strip():
                try:
                    self.fecha_desde = datetime.strptime(self.campo_fecha_desde.value.strip(), "%d/%m/%Y")
                except:
                    self.fecha_desde = None
            else:
                self.fecha_desde = None
            
            # Parsear fecha hasta
            if self.campo_fecha_hasta.value.strip():
                try:
                    self.fecha_hasta = datetime.strptime(self.campo_fecha_hasta.value.strip(), "%d/%m/%Y")
                except:
                    self.fecha_hasta = None
            else:
                self.fecha_hasta = None
            
            self.pagina_actual = 1
            self.actualizar_tabla()
            self.actualizar_paginacion()
        except Exception as e:
            print(f"Error al filtrar por fecha: {e}")
    
    def buscar_compras(self, termino):
        """Filtra las compras según el término de búsqueda"""
        self.busqueda_actual = termino.lower().strip()
        self.pagina_actual = 1
        self.actualizar_tabla()
        self.actualizar_paginacion()
    
    def obtener_compras_filtradas(self):
        """Obtiene las compras filtradas según la búsqueda y fechas"""
        compras_filtradas = self.compras
        
        # Filtrar por búsqueda de texto
        if self.busqueda_actual:
            compras_filtradas = [
                c for c in compras_filtradas
                if (self.busqueda_actual in (c.numero_factura or "").lower() or
                    self.busqueda_actual in (c.nombre_proveedor or "").lower())
            ]
        
        # Filtrar por rango de fechas
        if self.fecha_desde or self.fecha_hasta:
            compras_con_fecha = []
            for c in compras_filtradas:
                fecha_compra = c.fecha_compra
                if isinstance(fecha_compra, str):
                    try:
                        fecha_compra = datetime.fromisoformat(fecha_compra.replace('Z', '+00:00'))
                    except:
                        continue
                
                if isinstance(fecha_compra, datetime):
                    # Comparar solo la fecha, sin hora
                    fecha_solo = fecha_compra.date()
                    
                    # Verificar si está en el rango
                    if self.fecha_desde and fecha_solo < self.fecha_desde.date():
                        continue
                    if self.fecha_hasta and fecha_solo > self.fecha_hasta.date():
                        continue
                    
                    compras_con_fecha.append(c)
            
            compras_filtradas = compras_con_fecha
        
        return compras_filtradas
    
    def actualizar_tabla(self):
        """Actualiza la tabla de compras con los datos paginados"""
        self.tabla_compras.controls.clear()
        
        # Header de la tabla
        header = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text("Factura", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Proveedor", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=2),
                ft.Container(ft.Text("Fecha", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Total", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
            ]),
            bgcolor=VoltTheme.PRIMARY,
            padding=15,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        self.tabla_compras.controls.append(header)
        
        # Obtener compras filtradas
        compras_filtradas = self.obtener_compras_filtradas()
        
        # Calcular índices de paginación
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        compras_pagina = compras_filtradas[inicio:fin]
        
        # Filas de compras
        if not compras_pagina:
            mensaje = "No se encontraron compras" if self.busqueda_actual else "No hay compras registradas"
            self.tabla_compras.controls.append(
                ft.Container(
                    content=ft.Text(mensaje, size=14, color=ft.Colors.GREY_600),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        else:
            for compra in compras_pagina:
                fila = self.crear_fila_compra(compra)
                self.tabla_compras.controls.append(fila)
        
        self.page.update()
    
    def crear_fila_compra(self, compra: Compra):
        """Crea una fila de la tabla para una compra"""
        # Color de estado
        if compra.estado == "completada":
            estado_color = VoltTheme.SUCCESS
            estado_texto = "Completada"
        elif compra.estado == "pendiente":
            estado_color = VoltTheme.WARNING
            estado_texto = "Pendiente"
        else:
            estado_color = VoltTheme.DANGER
            estado_texto = "Cancelada"
        
        # Formatear fecha
        fecha_texto = "N/A"
        if compra.fecha_compra:
            if isinstance(compra.fecha_compra, str):
                fecha_texto = compra.fecha_compra[:10]
            else:
                fecha_texto = compra.fecha_compra.strftime("%d/%m/%Y")
        
        fila = ft.Container(
            content=ft.Row([
                ft.Container(
                    ft.Text(compra.numero_factura or "S/N", size=13),
                    expand=1
                ),
                ft.Container(
                    ft.Text(compra.nombre_proveedor or "N/A", size=13),
                    expand=2
                ),
                ft.Container(
                    ft.Text(fecha_texto, size=13),
                    expand=1
                ),
                ft.Container(
                    ft.Text(f"Q {compra.total:.2f}", size=13, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                    expand=1
                ),
                ft.Container(
                    content=ft.Container(
                        content=ft.Text(estado_texto, size=10, color=ft.Colors.WHITE),
                        bgcolor=estado_color,
                        padding=ft.padding.symmetric(horizontal=10, vertical=3),
                        border_radius=15
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
                            tooltip="Ver Detalle",
                            on_click=lambda _, c=compra: self.ver_detalle_compra(c)
                        ),
                        ft.IconButton(
                            icon="cancel",
                            icon_size=18,
                            icon_color=VoltTheme.DANGER,
                            tooltip="Anular Compra",
                            on_click=lambda _, c=compra: self.confirmar_anular_compra(c),
                            disabled=compra.estado == "cancelada"
                        ),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    expand=1,
                    alignment=ft.alignment.center
                ),
            ]),
            padding=15,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        return fila
    
    def actualizar_paginacion(self):
        """Actualiza los controles de paginación"""
        self.paginacion_container.controls.clear()
        
        # Usar compras filtradas para calcular total de páginas
        compras_filtradas = self.obtener_compras_filtradas()
        total_paginas = (len(compras_filtradas) + self.items_por_pagina - 1) // self.items_por_pagina
        
        if total_paginas <= 1:
            self.page.update()
            return
        
        # Botón anterior
        self.paginacion_container.controls.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                disabled=self.pagina_actual == 1,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual > 1 else VoltTheme.TEXT_SECONDARY,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual - 1)
            )
        )
        
        # Números de página
        for i in range(1, total_paginas + 1):
            es_actual = i == self.pagina_actual
            self.paginacion_container.controls.append(
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
                    on_click=lambda _, pagina=i: self.cambiar_pagina(pagina) if not es_actual else None,
                    ink=True if not es_actual else False
                )
            )
        
        # Botón siguiente
        self.paginacion_container.controls.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                disabled=self.pagina_actual == total_paginas,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual < total_paginas else VoltTheme.TEXT_SECONDARY,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual + 1)
            )
        )
        
        self.page.update()
    
    def cambiar_pagina(self, nueva_pagina):
        """Cambia a la página especificada"""
        self.pagina_actual = nueva_pagina
        self.actualizar_tabla()
        self.actualizar_paginacion()
    
    def abrir_modal_nueva_compra(self):
        """Abre el modal para registrar una nueva compra"""
        try:
            # Cargar proveedores y productos
            self.proveedores = self.proveedor_repo.listar()  # Ya filtra por estado='activo'
            self.productos = self.producto_repo.listar(solo_activos=True)
            self.carrito = []
            
            if not self.proveedores:
                self.mostrar_mensaje("Error", "No hay proveedores activos. Debe crear al menos un proveedor.", "error")
                return
            
            if not self.productos:
                self.mostrar_mensaje("Error", "No hay productos activos. Debe crear al menos un producto.", "error")
                return
        except Exception as e:
            print(f"[ERROR] Al cargar datos para nueva compra: {str(e)}")
            self.mostrar_mensaje("Error", f"Error al cargar datos: {str(e)}", "error")
            return
        
        # Campos del formulario
        self.campo_numero_factura = ft.TextField(
            label="Número de Factura",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Opcional"
        )
        
        self.dropdown_proveedor = ft.Dropdown(
            label="Proveedor *",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            options=[
                ft.dropdown.Option(str(p.id_proveedor), p.nombre_empresa)
                for p in self.proveedores
            ]
        )
        
        self.campo_observaciones = ft.TextField(
            label="Observaciones",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            multiline=True,
            min_lines=2,
            max_lines=3,
            hint_text="Opcional"
        )
        
        # Sección para agregar productos al carrito
        self.dropdown_producto = ft.Dropdown(
            label="Producto",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            options=[
                ft.dropdown.Option(str(p.id_producto), f"{p.codigo} - {p.nombre}")
                for p in self.productos
            ],
            on_change=self.al_seleccionar_producto
        )
        
        self.campo_cantidad = ft.TextField(
            label="Cantidad",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="1"
        )
        
        self.campo_precio = ft.TextField(
            label="Precio Unitario",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0.00"
        )
        
        # Tabla del carrito
        self.tabla_carrito = ft.Column(spacing=5)
        
        # Texto del total
        self.texto_total = ft.Text("Total: Q 0.00", size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY)
        
        # Contenido del modal con scroll
        modal_content = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Nueva Compra",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                
                # Información general
                self.campo_numero_factura,
                self.dropdown_proveedor,
                
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                ft.Text("Agregar Productos", size=16, weight=ft.FontWeight.BOLD),
                
                # Formulario para agregar productos
                self.dropdown_producto,
                ft.Row([
                    ft.Column([self.campo_cantidad], expand=1),
                    ft.Column([self.campo_precio], expand=1),
                ], spacing=10),
                ft.ElevatedButton(
                    "Agregar al Carrito",
                    icon=ft.Icons.ADD_SHOPPING_CART,
                    bgcolor=VoltTheme.SUCCESS,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.agregar_al_carrito()
                ),
                
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                ft.Text("Productos en el Carrito", size=16, weight=ft.FontWeight.BOLD),
                
                # Carrito
                ft.Container(
                    content=self.tabla_carrito,
                    height=150,
                    border=ft.border.all(1, VoltTheme.BORDER_COLOR),
                    border_radius=5,
                    padding=10
                ),
                
                self.campo_observaciones,
                
                # Total
                ft.Container(
                    content=self.texto_total,
                    alignment=ft.alignment.center_right,
                    padding=10,
                    bgcolor=VoltTheme.BG_PRIMARY,
                    border_radius=5
                ),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            width=1000,
            height=600,
            border_radius=10
        )
        
        # Botones fuera del scroll
        botones = ft.Container(
            content=ft.Row([
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda _: self.cerrar_modal()
                ),
                ft.ElevatedButton(
                    "Guardar Compra",
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.guardar_compra()
                ),
            ], alignment=ft.MainAxisAlignment.END, spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.only(left=30, right=30, bottom=20),
            width=1000
        )
        
        # Contenedor principal
        contenedor_principal = ft.Column([
            modal_content,
            botones
        ], spacing=0)
        
        self.modal = ft.AlertDialog(
            modal=True,
            content=contenedor_principal
        )
        
        self.page.open(self.modal)
        self.actualizar_vista_carrito()
    
    def al_seleccionar_producto(self, e):
        """Cuando se selecciona un producto, cargar su precio de costo"""
        if not self.dropdown_producto.value:
            return
        
        id_producto = int(self.dropdown_producto.value)
        producto = next((p for p in self.productos if p.id_producto == id_producto), None)
        
        if producto:
            self.campo_precio.value = str(producto.precio_costo)
            self.page.update()
    
    def agregar_al_carrito(self):
        """Agrega un producto al carrito"""
        # Validar campos
        if not self.dropdown_producto.value:
            self.mostrar_mensaje("Error", "Debe seleccionar un producto", "error")
            return
        
        try:
            cantidad = int(self.campo_cantidad.value or "0")
            precio = float(self.campo_precio.value or "0")
            
            if cantidad <= 0:
                self.mostrar_mensaje("Error", "La cantidad debe ser mayor a cero", "error")
                return
            
            if precio <= 0:
                self.mostrar_mensaje("Error", "El precio debe ser mayor a cero", "error")
                return
            
            # Buscar el producto
            id_producto = int(self.dropdown_producto.value)
            producto = next((p for p in self.productos if p.id_producto == id_producto), None)
            
            if not producto:
                self.mostrar_mensaje("Error", "Producto no encontrado", "error")
                return
            
            # Verificar si ya está en el carrito
            existe = next((d for d in self.carrito if d.id_producto == id_producto), None)
            if existe:
                existe.cantidad += cantidad
                existe.calcular_subtotal()
            else:
                # Crear detalle
                detalle = DetalleCompra(
                    id_producto=id_producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    codigo_producto=producto.codigo,
                    nombre_producto=producto.nombre
                )
                detalle.calcular_subtotal()
                self.carrito.append(detalle)
            
            # Limpiar campos
            self.dropdown_producto.value = None
            self.campo_cantidad.value = "1"
            self.campo_precio.value = "0.00"
            
            # Actualizar vista
            self.actualizar_vista_carrito()
            
        except ValueError:
            self.mostrar_mensaje("Error", "Valores numéricos inválidos", "error")
    
    def actualizar_vista_carrito(self):
        """Actualiza la visualización del carrito"""
        self.tabla_carrito.controls.clear()
        
        if not self.carrito:
            self.tabla_carrito.controls.append(
                ft.Text("No hay productos en el carrito", size=12, color=ft.Colors.GREY_600)
            )
        else:
            # Header del carrito
            header_carrito = ft.Row([
                ft.Text("Código", size=11, weight=ft.FontWeight.BOLD, expand=1),
                ft.Text("Producto", size=11, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Cantidad", size=11, weight=ft.FontWeight.BOLD, expand=1),
                ft.Text("Precio Unit.", size=11, weight=ft.FontWeight.BOLD, expand=1),
                ft.Text("Subtotal", size=11, weight=ft.FontWeight.BOLD, expand=1),
                ft.Container(width=100),  # Espacio para acciones
            ])
            self.tabla_carrito.controls.append(header_carrito)
            self.tabla_carrito.controls.append(ft.Divider(height=1, color=VoltTheme.BORDER_COLOR))
            
            for detalle in self.carrito:
                fila = ft.Row([
                    ft.Text(f"{detalle.codigo_producto}", size=11, expand=1),
                    ft.Text(f"{detalle.nombre_producto}", size=11, expand=2),
                    
                    # Controles de cantidad con botones +/-
                    ft.Container(
                        content=ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.REMOVE,
                                icon_size=16,
                                icon_color=VoltTheme.DANGER,
                                tooltip="Disminuir",
                                on_click=lambda _, d=detalle: self.cambiar_cantidad_carrito(d, -1)
                            ),
                            ft.Text(f"{detalle.cantidad}", size=12, weight=ft.FontWeight.BOLD, width=30, text_align=ft.TextAlign.CENTER),
                            ft.IconButton(
                                icon=ft.Icons.ADD,
                                icon_size=16,
                                icon_color=VoltTheme.SUCCESS,
                                tooltip="Aumentar",
                                on_click=lambda _, d=detalle: self.cambiar_cantidad_carrito(d, 1)
                            ),
                        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                        expand=1
                    ),
                    
                    ft.Text(f"Q {detalle.precio_unitario:.2f}", size=11, expand=1),
                    ft.Text(f"Q {detalle.subtotal:.2f}", size=11, weight=ft.FontWeight.BOLD, expand=1),
                    
                    # Botón eliminar
                    ft.Container(
                        content=ft.IconButton(
                            icon="delete",
                            icon_size=18,
                            icon_color=VoltTheme.DANGER,
                            tooltip="Quitar",
                            on_click=lambda _, d=detalle: self.quitar_del_carrito(d)
                        ),
                        width=100,
                        alignment=ft.alignment.center
                    ),
                ], spacing=5)
                self.tabla_carrito.controls.append(fila)
        
        # Calcular total
        total = sum(d.subtotal for d in self.carrito)
        self.texto_total.value = f"Total: Q {total:.2f}"
        
        self.page.update()
    
    def cambiar_cantidad_carrito(self, detalle: DetalleCompra, cambio: int):
        """Cambia la cantidad de un producto en el carrito"""
        nueva_cantidad = detalle.cantidad + cambio
        
        # Validar que la cantidad sea al menos 1
        if nueva_cantidad < 1:
            return
        
        # Actualizar cantidad y recalcular subtotal
        detalle.cantidad = nueva_cantidad
        detalle.calcular_subtotal()
        
        # Actualizar vista
        self.actualizar_vista_carrito()
    
    def quitar_del_carrito(self, detalle: DetalleCompra):
        """Quita un producto del carrito"""
        self.carrito.remove(detalle)
        self.actualizar_vista_carrito()
    
    def guardar_compra(self):
        """Guarda la compra en la base de datos"""
        # Validaciones
        if not self.dropdown_proveedor.value:
            self.mostrar_mensaje("Error", "Debe seleccionar un proveedor", "error")
            return
        
        if not self.carrito:
            self.mostrar_mensaje("Error", "Debe agregar al menos un producto al carrito", "error")
            return
        
        try:
            # Crear objeto Compra
            compra = Compra(
                numero_factura=self.campo_numero_factura.value.strip() if self.campo_numero_factura.value else None,
                id_proveedor=int(self.dropdown_proveedor.value),
                id_empleado=self.empleado['id_empleado'],
                observaciones=self.campo_observaciones.value.strip() if self.campo_observaciones.value else None,
                detalles=self.carrito.copy()
            )
            
            # Calcular totales
            compra.calcular_totales()
            
            # Validar
            es_valido, mensaje = compra.validar()
            if not es_valido:
                self.mostrar_mensaje("Error de Validación", mensaje, "error")
                return
            
            # Guardar en BD
            resultado = self.compra_repo.crear(compra)
            
            if resultado.get('success'):
                self.mostrar_mensaje("Éxito", "Compra registrada exitosamente. Stock y precios actualizados.", "success")
                self.cerrar_modal()
                self.cargar_compras()
            else:
                mensaje_error = resultado.get('message', 'Error al guardar la compra')
                
                # Detectar error de factura duplicada
                if 'duplicate' in mensaje_error.lower() or 'unique' in mensaje_error.lower() or 'numero_factura' in mensaje_error.lower():
                    self.mostrar_mensaje("Factura Duplicada", 
                        "El número de factura ya existe. Por favor ingrese un número diferente o deje el campo vacío para generar uno automático.", 
                        "warning")
                else:
                    self.mostrar_mensaje("Error", mensaje_error, "error")
                
        except Exception as e:
            error_msg = str(e)
            
            # Detectar error de factura duplicada en la excepción
            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower() or 'numero_factura' in error_msg.lower():
                self.mostrar_mensaje("Factura Duplicada", 
                    "El número de factura ya existe. Por favor ingrese un número diferente o deje el campo vacío.", 
                    "warning")
            else:
                self.mostrar_mensaje("Error", f"Error al guardar la compra: {error_msg}", "error")
    
    def ver_detalle_compra(self, compra: Compra):
        """Muestra el detalle completo de una compra"""
        # Cargar compra con detalles
        compra_completa = self.compra_repo.obtener_por_id(compra.id_compra)
        
        if not compra_completa:
            self.mostrar_mensaje("Error", "No se pudo cargar el detalle de la compra", "error")
            return
        
        # Formatear fecha
        fecha_texto = "N/A"
        if compra_completa.fecha_compra:
            if isinstance(compra_completa.fecha_compra, str):
                fecha_texto = compra_completa.fecha_compra
            else:
                fecha_texto = compra_completa.fecha_compra.strftime("%d/%m/%Y %H:%M")
        
        # Crear tabla de productos
        tabla_productos = ft.Column(spacing=5)
        
        # Header
        tabla_productos.controls.append(
            ft.Row([
                ft.Text("Producto", size=11, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Cant.", size=11, weight=ft.FontWeight.BOLD, expand=1),
                ft.Text("Precio", size=11, weight=ft.FontWeight.BOLD, expand=1),
                ft.Text("Subtotal", size=11, weight=ft.FontWeight.BOLD, expand=1),
            ])
        )
        
        # Detalles
        for detalle in compra_completa.detalles:
            tabla_productos.controls.append(
                ft.Row([
                    ft.Text(f"{detalle.codigo_producto} - {detalle.nombre_producto}", size=11, expand=2),
                    ft.Text(str(detalle.cantidad), size=11, expand=1),
                    ft.Text(f"Q {detalle.precio_unitario:.2f}", size=11, expand=1),
                    ft.Text(f"Q {detalle.subtotal:.2f}", size=11, expand=1),
                ])
            )
        
        # Contenido del detalle
        detalle_content = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Detalle de Compra",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Número de Factura:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(compra_completa.numero_factura or "S/N", size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Estado:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(compra_completa.estado.capitalize(), size=13),
                    ], expand=1),
                ]),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Proveedor:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(compra_completa.nombre_proveedor or "N/A", size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Fecha:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(fecha_texto, size=13),
                    ], expand=1),
                ]),
                
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                ft.Text("Productos Comprados", size=16, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                
                ft.Container(
                    content=tabla_productos,
                    border=ft.border.all(1, VoltTheme.BORDER_COLOR),
                    border_radius=5,
                    padding=10
                ),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Total:", size=18, weight=ft.FontWeight.BOLD),
                    ], expand=1),
                    ft.Column([
                        ft.Text(f"Q {compra_completa.total:.2f}", size=18, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                    ], expand=1, horizontal_alignment=ft.CrossAxisAlignment.END),
                ]),
                
                ft.Column([
                    ft.Text("Observaciones:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(compra_completa.observaciones or "Sin observaciones", size=13),
                ]) if compra_completa.observaciones else ft.Container(),
                
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            width=1000,
            height=450,
            border_radius=10
        )
        
        # Botón cerrar fuera del scroll
        boton_cerrar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Cerrar",
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.cerrar_modal()
                ),
            ], alignment=ft.MainAxisAlignment.END),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.only(left=30, right=30, bottom=20),
            width=1000
        )
        
        # Contenedor principal
        contenedor_detalle = ft.Column([
            detalle_content,
            boton_cerrar
        ], spacing=0)
        
        self.modal = ft.AlertDialog(
            modal=True,
            content=contenedor_detalle
        )
        
        self.page.open(self.modal)
    
    def confirmar_anular_compra(self, compra: Compra):
        """Muestra diálogo de confirmación para anular una compra"""
        def anular(_):
            try:
                resultado = self.compra_repo.anular(compra.id_compra)
                
                if resultado.get('success'):
                    self.mostrar_mensaje("Éxito", "Compra anulada exitosamente. Stock revertido.", "success")
                    self.cerrar_modal()
                    self.cargar_compras()
                else:
                    self.mostrar_mensaje("Error", resultado.get('message', 'Error al anular la compra'), "error")
                    
            except Exception as e:
                self.mostrar_mensaje("Error", f"Error al anular la compra: {str(e)}", "error")
        
        confirmacion = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Anulación"),
            content=ft.Text(f"¿Está seguro que desea anular la compra {compra.numero_factura or 'S/N'}?\n\nEsta acción revertirá el stock de los productos."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                ft.ElevatedButton(
                    "Anular",
                    bgcolor=VoltTheme.DANGER,
                    color=ft.Colors.WHITE,
                    on_click=anular
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.modal = confirmacion
        self.page.open(self.modal)
    
    def cerrar_modal(self):
        """Cierra el modal actual"""
        if self.modal:
            self.page.close(self.modal)
            self.modal = None
    
    def mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        """Muestra un mensaje estilo SweetAlert"""
        # Iconos según el tipo
        icon_map = {
            "success": ft.Icons.CHECK_CIRCLE,
            "error": ft.Icons.ERROR,
            "warning": ft.Icons.WARNING,
            "info": ft.Icons.INFO
        }
        
        color_map = {
            "success": VoltTheme.SUCCESS,
            "error": VoltTheme.DANGER,
            "warning": VoltTheme.WARNING,
            "info": VoltTheme.INFO
        }
        
        icono = icon_map.get(tipo, ft.Icons.INFO)
        color = color_map.get(tipo, VoltTheme.INFO)
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(icono, color=color, size=30),
                ft.Text(titulo, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Text(mensaje),
            actions=[
                ft.ElevatedButton(
                    "Aceptar",
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.page.close(dialogo)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.open(dialogo)
