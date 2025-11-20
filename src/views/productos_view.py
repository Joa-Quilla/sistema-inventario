"""
Vista del módulo de Productos
"""
import flet as ft
from typing import Optional, Callable
from datetime import datetime, date
from utils.theme import VoltTheme
from models.producto import Producto
from models.categoria import Categoria
from repositories.producto_repository import ProductoRepository
from repositories.categoria_repository import CategoriaRepository
import math


class ProductosView:
    """Vista para gestión de productos"""
    
    def __init__(self, page: ft.Page, empleado: dict):
        self.page = page
        self.empleado = empleado
        self.producto_repo = ProductoRepository()
        self.categoria_repo = CategoriaRepository()
        
        # Estado
        self.productos = []
        self.categorias = []
        self.producto_seleccionado: Optional[Producto] = None
        self.busqueda_actual = ""
        self.categoria_filtro = None
        
        # Paginación
        self.pagina_actual = 1
        self.productos_por_pagina = 5
        
        # Componentes
        self.tabla_productos = None
        self.campo_busqueda = None
        self.dropdown_categoria_filtro = None
        self.contenedor_principal = None
        self.contenedor_paginacion = None
    
    def build(self) -> ft.Container:
        """Construye la vista de productos"""
        # Cargar datos iniciales
        self.cargar_categorias()
        self.cargar_productos()
        
        # Header
        header = self._crear_header()
        
        # Barra de búsqueda y filtros
        barra_busqueda = self._crear_barra_busqueda()
        
        # Tabla de productos
        self.tabla_productos = self._crear_tabla_productos()
        
        # Paginación
        self.contenedor_paginacion = self._crear_paginacion()
        
        # Contenedor principal
        self.contenedor_principal = ft.Container(
            content=ft.Column([
                header,
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                barra_busqueda,
                ft.Container(height=20),
                self.tabla_productos,
                self.contenedor_paginacion
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            padding=30,
            bgcolor=VoltTheme.BG_PRIMARY
        )
        
        return self.contenedor_principal
    
    def _crear_header(self) -> ft.Container:
        """Crea el header con título y botón de nuevo producto"""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Productos", size=28, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                    ft.Text("Gestión de inventario de productos", size=14, color=VoltTheme.TEXT_SECONDARY)
                ], spacing=5),
                ft.Row([
                    ft.ElevatedButton(
                        "Gestionar Categorías",
                        icon="category",
                        on_click=self.mostrar_dialog_categorias,
                        bgcolor=VoltTheme.SECONDARY,
                        color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Nuevo Producto",
                        icon="add",
                        on_click=lambda e: self.mostrar_dialog_producto(),
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE
                    )
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=20)
        )
    
    def _crear_barra_busqueda(self) -> ft.Container:
        """Crea la barra de búsqueda y filtros"""
        self.campo_busqueda = ft.TextField(
            hint_text="Buscar por código, nombre o descripción...",
            prefix_icon="search",
            width=400,
            on_change=self.on_buscar,
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        # Dropdown de categorías - Solo mostrar categorías activas
        opciones_categorias = [ft.dropdown.Option(key="", text="Todas las categorías")]
        opciones_categorias.extend([
            ft.dropdown.Option(key=str(cat.id_categoria), text=cat.nombre) 
            for cat in self.categorias if cat.estado == "activa"
        ])
        
        self.dropdown_categoria_filtro = ft.Dropdown(
            options=opciones_categorias,
            width=200,
            value="",
            on_change=self.on_filtrar_categoria,
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        return ft.Container(
            content=ft.Row([
                self.campo_busqueda,
                self.dropdown_categoria_filtro,
                ft.IconButton(
                    icon="refresh",
                    tooltip="Recargar",
                    on_click=lambda e: self.cargar_productos(),
                    icon_color=VoltTheme.PRIMARY
                )
            ], spacing=15),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _crear_tabla_productos(self) -> ft.Container:
        """Crea la tabla de productos con paginación"""
        # Cabecera
        header = ft.Container(
            content=ft.Row([
                ft.Text("Código", weight=ft.FontWeight.BOLD, size=12, width=100, color=ft.Colors.WHITE),
                ft.Text("Nombre", weight=ft.FontWeight.BOLD, size=12, width=200, color=ft.Colors.WHITE),
                ft.Text("Categoría", weight=ft.FontWeight.BOLD, size=12, width=120, color=ft.Colors.WHITE),
                ft.Text("Stock", weight=ft.FontWeight.BOLD, size=12, width=80, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE),
                ft.Text("P. Compra", weight=ft.FontWeight.BOLD, size=12, width=100, text_align=ft.TextAlign.RIGHT, color=ft.Colors.WHITE),
                ft.Text("P. Venta", weight=ft.FontWeight.BOLD, size=12, width=100, text_align=ft.TextAlign.RIGHT, color=ft.Colors.WHITE),
                ft.Text("Estado", weight=ft.FontWeight.BOLD, size=12, width=100, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE),
                ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=12, width=150, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE)
            ]),
            padding=15,
            bgcolor=VoltTheme.PRIMARY,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        
        # Calcular paginación
        total_productos = len(self.productos)
        total_paginas = math.ceil(total_productos / self.productos_por_pagina) if total_productos > 0 else 1
        
        # Ajustar página actual si es necesario
        if self.pagina_actual > total_paginas:
            self.pagina_actual = total_paginas
        
        # Obtener productos de la página actual
        inicio = (self.pagina_actual - 1) * self.productos_por_pagina
        fin = inicio + self.productos_por_pagina
        productos_pagina = self.productos[inicio:fin]
        
        # Filas de productos
        filas = ft.Column([], spacing=0)
        
        for producto in productos_pagina:
            fila = self._crear_fila_producto(producto)
            filas.controls.append(fila)
        
        # Si no hay productos
        if not self.productos:
            filas.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("inventory_2", size=60, color=VoltTheme.TEXT_SECONDARY),
                        ft.Text("No hay productos", size=16, color=VoltTheme.TEXT_SECONDARY),
                        ft.Text("Agrega tu primer producto usando el botón 'Nuevo Producto'", 
                               size=12, color=VoltTheme.TEXT_SECONDARY)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=50,
                    alignment=ft.alignment.center
                )
            )
        
        return ft.Container(
            content=ft.Column([header, filas], spacing=0),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR)
        )
    
    def _crear_fila_producto(self, producto: Producto) -> ft.Container:
        """Crea una fila para un producto"""
        # Color de stock - comparar stock_actual con stock_minimo
        stock_color = VoltTheme.DANGER if producto.stock_actual <= producto.stock_minimo else VoltTheme.SUCCESS
        
        # Estado badge
        estado_color = VoltTheme.SUCCESS if producto.estado == "activo" else VoltTheme.DANGER
        
        fila = ft.Container(
            content=ft.Row([
                ft.Text(producto.codigo, size=12, width=100),
                ft.Text(producto.nombre, size=12, width=200, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(producto.nombre_categoria or "-", size=12, width=120, color=VoltTheme.TEXT_SECONDARY),
                ft.Container(
                    content=ft.Text(
                        str(producto.stock_actual),
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=stock_color
                    ),
                    width=80,
                    alignment=ft.alignment.center
                ),
                ft.Text(f"Q {producto.precio_compra:.2f}", size=12, width=100, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"Q {producto.precio_venta:.2f}", size=12, width=100, text_align=ft.TextAlign.RIGHT, 
                       weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                ft.Container(
                    content=ft.Container(
                        content=ft.Text(producto.estado.capitalize(), size=10, color=ft.Colors.WHITE),
                        bgcolor=estado_color,
                        padding=ft.padding.symmetric(horizontal=10, vertical=3),
                        border_radius=15
                    ),
                    width=100,
                    alignment=ft.alignment.center
                ),
                ft.Row([
                    ft.IconButton(
                        icon="visibility",
                        icon_size=18,
                        tooltip="Ver Detalle",
                        on_click=lambda e, p=producto: self.mostrar_detalle_producto(p),
                        icon_color=VoltTheme.INFO
                    ),
                    ft.IconButton(
                        icon="edit",
                        icon_size=18,
                        tooltip="Editar",
                        on_click=lambda e, p=producto: self.mostrar_dialog_producto(p),
                        icon_color=VoltTheme.WARNING
                    ),
                    ft.IconButton(
                        icon="power_settings_new" if producto.estado == "activo" else "check_circle",
                        icon_size=18,
                        tooltip="Desactivar" if producto.estado == "activo" else "Activar",
                        on_click=lambda e, p=producto: self.cambiar_estado_producto(p),
                        icon_color=VoltTheme.DANGER if producto.estado == "activo" else VoltTheme.SUCCESS
                    )
                ], spacing=5, width=150)
            ]),
            padding=15,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        return fila
    
    def _crear_paginacion(self) -> ft.Container:
        """Crea los controles de paginación"""
        total_productos = len(self.productos)
        total_paginas = math.ceil(total_productos / self.productos_por_pagina) if total_productos > 0 else 1
        
        # Si solo hay una página o no hay productos, no mostrar paginación
        if total_paginas <= 1:
            return ft.Container()
        
        def cambiar_pagina(pagina):
            def handler(e):
                self.pagina_actual = pagina
                self.tabla_productos = self._crear_tabla_productos()
                self.contenedor_paginacion = self._crear_paginacion()
                # Actualizar el contenedor principal
                if self.contenedor_principal:
                    self.contenedor_principal.content.controls[4] = self.tabla_productos
                    self.contenedor_principal.content.controls[5] = self.contenedor_paginacion
                    self.page.update()
            return handler
        
        # Crear botones de paginación
        botones = []
        
        # Botón anterior
        botones.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                on_click=cambiar_pagina(self.pagina_actual - 1) if self.pagina_actual > 1 else None,
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
                    on_click=cambiar_pagina(i) if not es_actual else None,
                    ink=True if not es_actual else False
                )
            )
        
        # Botón siguiente
        botones.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                on_click=cambiar_pagina(self.pagina_actual + 1) if self.pagina_actual < total_paginas else None,
                disabled=self.pagina_actual == total_paginas,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual < total_paginas else VoltTheme.TEXT_SECONDARY
            )
        )
        
        return ft.Container(
            content=ft.Row(
                botones,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5
            ),
            padding=20
        )
    
    
    def mostrar_dialog_producto(self, producto: Optional[Producto] = None):
        """Muestra el diálogo para crear/editar producto"""
        es_edicion = producto is not None
        titulo = "Editar Producto" if es_edicion else "Nuevo Producto"
        
        # Crear campos del formulario con estilos simples (sin fondo)
        campo_codigo = ft.TextField(
            label="Código *",
            value=producto.codigo if es_edicion else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        campo_nombre = ft.TextField(
            label="Nombre *",
            value=producto.nombre if es_edicion else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        campo_descripcion = ft.TextField(
            label="Descripción",
            value=producto.descripcion if es_edicion and producto.descripcion else "",
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        # Dropdown de categoría
        opciones_categorias = [
            ft.dropdown.Option(key=str(cat.id_categoria), text=cat.nombre) 
            for cat in self.categorias if cat.estado == "activa"
        ]
        
        dropdown_categoria = ft.Dropdown(
            label="Categoría *",
            options=opciones_categorias,
            value=str(producto.id_categoria) if es_edicion and producto.id_categoria else None,
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        campo_unidad = ft.TextField(
            label="Unidad de Medida",
            value=producto.unidad_medida if es_edicion else "unidad",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        # Precios: Solo en creación, deshabilitados en edición
        campo_precio_compra = ft.TextField(
            label="Precio Compra *",
            value=str(producto.precio_compra) if es_edicion else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="Q ",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            disabled=es_edicion,
            hint_text="Se actualiza en Compras" if es_edicion else None
        )
        
        campo_precio_venta = ft.TextField(
            label="Precio Venta *",
            value=str(producto.precio_venta) if es_edicion else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="Q ",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            disabled=es_edicion,
            hint_text="Se actualiza en Compras" if es_edicion else None
        )
        
        # Stock: Siempre deshabilitado (se maneja en Compras/Ventas)
        campo_stock_actual = ft.TextField(
            label="Stock Actual",
            value=str(producto.stock_actual) if es_edicion else "0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            disabled=True,
            hint_text="Se actualiza en Compras/Ventas"
        )
        
        campo_stock_minimo = ft.TextField(
            label="Stock Mínimo *",
            value=str(producto.stock_minimo) if es_edicion else "0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        # Campos adicionales de BD
        campo_lote = ft.TextField(
            label="Lote",
            value=producto.lote if es_edicion and producto.lote else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Número de lote del producto"
        )
        
        # Campo de fecha de vencimiento (manual)
        fecha_venc_inicial = producto.fecha_vencimiento if es_edicion and producto.fecha_vencimiento else None
        
        campo_fecha_vencimiento = ft.TextField(
            label="Fecha de Vencimiento (Opcional)",
            value=fecha_venc_inicial.strftime("%d/%m/%Y") if fecha_venc_inicial else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="DD/MM/YYYY (ejemplo: 31/12/2025)",
            suffix_icon=ft.Icons.CALENDAR_TODAY
        )
        
        campo_ubicacion = ft.TextField(
            label="Ubicación",
            value=producto.ubicacion if es_edicion and producto.ubicacion else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        dropdown_estado = ft.Dropdown(
            label="Estado",
            options=[
                ft.dropdown.Option("activo", "Activo"),
                ft.dropdown.Option("inactivo", "Inactivo"),
                ft.dropdown.Option("descontinuado", "Descontinuado")
            ],
            value=producto.estado if es_edicion else "activo",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        def guardar_producto(e):
            try:
                print("[DEBUG] Iniciando guardado de producto...")
                
                # Limpiar errores previos
                campo_codigo.error_text = None
                campo_nombre.error_text = None
                dropdown_categoria.error_text = None
                campo_precio_compra.error_text = None
                campo_precio_venta.error_text = None
                campo_stock_minimo.error_text = None
                campo_fecha_vencimiento.error_text = None
                self.page.update()
                
                # Validar campos requeridos con mensajes debajo del campo
                tiene_errores = False
                
                if not campo_codigo.value or not campo_codigo.value.strip():
                    campo_codigo.error_text = "Por favor, introduce el código del producto"
                    tiene_errores = True
                
                if not campo_nombre.value or not campo_nombre.value.strip():
                    campo_nombre.error_text = "Por favor, introduce el nombre del producto"
                    tiene_errores = True
                
                if not dropdown_categoria.value:
                    dropdown_categoria.error_text = "Por favor, selecciona una categoría"
                    tiene_errores = True
                
                # Solo validar precios en creación (en edición están deshabilitados)
                if not es_edicion:
                    if not campo_precio_compra.value:
                        campo_precio_compra.error_text = "Por favor, introduce el precio de compra"
                        tiene_errores = True
                    else:
                        # Validar que sea número
                        try:
                            float(campo_precio_compra.value)
                        except ValueError:
                            campo_precio_compra.error_text = "Debe ser un número válido"
                            tiene_errores = True
                    
                    if not campo_precio_venta.value:
                        campo_precio_venta.error_text = "Por favor, introduce el precio de venta"
                        tiene_errores = True
                    else:
                        # Validar que sea número
                        try:
                            float(campo_precio_venta.value)
                        except ValueError:
                            campo_precio_venta.error_text = "Debe ser un número válido"
                            tiene_errores = True
                
                # Validar stock mínimo
                if campo_stock_minimo.value:
                    try:
                        int(campo_stock_minimo.value)
                    except ValueError:
                        campo_stock_minimo.error_text = "Debe ser un número entero"
                        tiene_errores = True
                
                if tiene_errores:
                    self.page.update()
                    return
                
                # Crear objeto producto
                print(f"[DEBUG] Código: {campo_codigo.value}, Nombre: {campo_nombre.value}")
                
                # Parsear fecha de vencimiento si existe (formato DD/MM/YYYY)
                fecha_venc = None
                if campo_fecha_vencimiento.value and campo_fecha_vencimiento.value.strip():
                    try:
                        fecha_venc = datetime.strptime(campo_fecha_vencimiento.value.strip(), "%d/%m/%Y").date()
                        # Validar que no sea fecha pasada
                        if fecha_venc < datetime.now().date():
                            campo_fecha_vencimiento.error_text = "La fecha de vencimiento no puede ser anterior a hoy"
                            tiene_errores = True
                    except ValueError:
                        campo_fecha_vencimiento.error_text = "Formato incorrecto. Use DD/MM/YYYY (ejemplo: 31/12/2025)"
                        tiene_errores = True
                
                if tiene_errores:
                    self.page.update()
                    return
                
                producto_data = Producto(
                    id_producto=producto.id_producto if es_edicion else None,
                    codigo=campo_codigo.value.strip(),
                    nombre=campo_nombre.value.strip(),
                    descripcion=campo_descripcion.value.strip() if campo_descripcion.value else None,
                    id_categoria=int(dropdown_categoria.value) if dropdown_categoria.value else None,
                    unidad_medida=campo_unidad.value or "unidad",
                    precio_compra=float(campo_precio_compra.value) if campo_precio_compra.value else 0.0,
                    precio_venta=float(campo_precio_venta.value) if campo_precio_venta.value else 0.0,
                    stock_actual=int(campo_stock_actual.value) if campo_stock_actual.value else 0,
                    stock_minimo=int(campo_stock_minimo.value) if campo_stock_minimo.value else 0,
                    lote=campo_lote.value.strip() if campo_lote.value else None,
                    fecha_vencimiento=fecha_venc,
                    ubicacion=campo_ubicacion.value.strip() if campo_ubicacion.value else None,
                    estado=dropdown_estado.value
                )
                
                print(f"[DEBUG] Producto creado: {producto_data}")
                
                # Validar producto (validaciones de negocio)
                es_valido, mensaje_validacion = producto_data.validar()
                if not es_valido:
                    print(f"[DEBUG] Validación fallida: {mensaje_validacion}")
                    # Solo mostrar alerta para errores de validación de negocio (precios, stocks, etc.)
                    self.mostrar_mensaje(mensaje_validacion, "error")
                    return
                
                # Guardar
                print(f"[DEBUG] Guardando... Es edición: {es_edicion}")
                if es_edicion:
                    resultado = self.producto_repo.actualizar(producto_data)
                else:
                    resultado = self.producto_repo.crear(producto_data)
                
                print(f"[DEBUG] Resultado: {resultado}")
                
                if resultado['success']:
                    self.page.close(dialog)
                    self.mostrar_mensaje(resultado['message'], "success")
                    self.cargar_productos()
                else:
                    # Error de base de datos (código duplicado, etc.)
                    self.mostrar_mensaje(resultado['message'], "error")
                    
            except ValueError as ve:
                print(f"[ERROR] ValueError: {str(ve)}")
                self.mostrar_mensaje(f"Error en los datos: {str(ve)}", "error")
            except Exception as ex:
                print(f"[ERROR] Excepción no controlada: {str(ex)}")
                import traceback
                traceback.print_exc()
                self.mostrar_mensaje(f"Error inesperado: {str(ex)}", "error")
        
        # Crear diálogo
        dialog = ft.AlertDialog(
            title=ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([campo_codigo, campo_nombre], spacing=10),
                    campo_descripcion,
                    ft.Row([dropdown_categoria, campo_unidad], spacing=10),
                    ft.Row([campo_precio_compra, campo_precio_venta], spacing=10),
                    ft.Row([campo_stock_actual, campo_stock_minimo], spacing=10),
                    ft.Row([campo_lote, campo_fecha_vencimiento], spacing=10),
                    campo_ubicacion,
                    dropdown_estado
                ], spacing=15, scroll=ft.ScrollMode.AUTO),
                width=1000,
                height=550,
                padding=10,
                bgcolor=ft.Colors.WHITE
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Guardar", on_click=guardar_producto, bgcolor=VoltTheme.PRIMARY, color=ft.Colors.WHITE)
            ]
        )
        
        self.page.open(dialog)
    
    def mostrar_dialog_categorias(self, e):
        """Muestra el diálogo de gestión de categorías"""
        categorias_list = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO, height=300)
        dialog = None  # Declarar primero
        
        def actualizar_lista_categorias():
            categorias_list.controls.clear()
            cats = self.categoria_repo.listar()
            for cat in cats:
                categorias_list.controls.append(self._crear_fila_categoria(cat, dialog))
            self.page.update()
        
        def agregar_categoria(e):
            nombre = campo_nueva_categoria.value
            if nombre:
                nueva_cat = Categoria(nombre=nombre)
                resultado = self.categoria_repo.crear(nueva_cat)
                if resultado['success']:
                    campo_nueva_categoria.value = ""
                    actualizar_lista_categorias()
                    self.cargar_categorias()
                    self.mostrar_mensaje(resultado['message'], "success")
                else:
                    self.mostrar_mensaje(resultado['message'], "error")
        
        campo_nueva_categoria = ft.TextField(
            hint_text="Nombre de nueva categoría",
            on_submit=agregar_categoria,
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        # Crear el diálogo ANTES de llamar actualizar_lista_categorias
        dialog = ft.AlertDialog(
            title=ft.Text("Gestionar Categorías"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        campo_nueva_categoria,
                        ft.IconButton(icon="add", on_click=agregar_categoria, bgcolor=VoltTheme.PRIMARY, 
                                     icon_color=ft.Colors.WHITE)
                    ], spacing=10),
                    ft.Divider(),
                    categorias_list
                ], spacing=10),
                width=500
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.page.close(dialog))
            ]
        )
        
        # Ahora sí cargar las categorías
        actualizar_lista_categorias()
        
        self.page.open(dialog)
    
    def _crear_fila_categoria(self, categoria: Categoria, dialog) -> ft.Container:
        """Crea una fila para una categoría"""
        def cambiar_estado_categoria(e):
            nuevo_estado = "inactiva" if categoria.estado == "activa" else "activa"
            accion = "desactivar" if nuevo_estado == "inactiva" else "activar"
            
            def confirmar(e):
                self.page.close(dialog_confirmacion)
                
                # Actualizar estado
                categoria.estado = nuevo_estado
                resultado = self.categoria_repo.actualizar(categoria)
                
                if resultado['success']:
                    self.mostrar_mensaje(
                        f"Categoría {accion}da exitosamente",
                        "success"
                    )
                    # Recargar lista
                    self.cargar_categorias()
                    self.page.close(dialog)
                    self.mostrar_dialog_categorias(None)
                else:
                    self.mostrar_mensaje(resultado['message'], "error")
            
            dialog_confirmacion = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"¿{accion.capitalize()} categoría?", weight=ft.FontWeight.BOLD),
                content=ft.Text(
                    f"¿Estás seguro de que deseas {accion} la categoría '{categoria.nombre}'?\n\n"
                    f"{'Las categorías inactivas no aparecerán al crear/editar productos.' if nuevo_estado == 'inactiva' else 'La categoría volverá a estar disponible.'}"
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog_confirmacion)),
                    ft.ElevatedButton(
                        accion.capitalize(),
                        on_click=confirmar,
                        bgcolor=VoltTheme.DANGER if nuevo_estado == "inactiva" else VoltTheme.SUCCESS,
                        color=ft.Colors.WHITE
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.open(dialog_confirmacion)
        
        return ft.Container(
            content=ft.Row([
                ft.Text(categoria.nombre, size=14, expand=True),
                ft.Container(
                    content=ft.Text(categoria.estado.upper(), size=10, color=ft.Colors.WHITE),
                    bgcolor=VoltTheme.SUCCESS if categoria.estado == "activa" else VoltTheme.DANGER,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    border_radius=15
                ),
                ft.IconButton(
                    icon="power_settings_new" if categoria.estado == "activa" else "check_circle",
                    icon_size=18, 
                    on_click=cambiar_estado_categoria,
                    icon_color=VoltTheme.DANGER if categoria.estado == "activa" else VoltTheme.SUCCESS,
                    tooltip="Desactivar" if categoria.estado == "activa" else "Activar"
                )
            ]),
            padding=10,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            border_radius=5
        )
    
    def confirmar_eliminar(self, producto: Producto):
        """Muestra confirmación para eliminar producto"""
        def eliminar(e):
            resultado = self.producto_repo.eliminar(producto.id_producto)
            self.page.close(dialog)
            self.mostrar_mensaje(resultado['message'], "success" if resultado['success'] else "error")
            self.cargar_productos()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar el producto '{producto.nombre}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Eliminar", on_click=eliminar, bgcolor=VoltTheme.DANGER, color=ft.Colors.WHITE)
            ]
        )
        
        self.page.open(dialog)
    
    def on_buscar(self, e):
        """Maneja el evento de búsqueda"""
        self.busqueda_actual = e.control.value
        self.cargar_productos()
    
    def on_filtrar_categoria(self, e):
        """Maneja el evento de filtro por categoría"""
        try:
            # Si el valor es None o vacío, o es texto "Todas", poner None
            if not e.control.value or e.control.value == "Todas las categorías":
                self.categoria_filtro = None
            else:
                self.categoria_filtro = int(e.control.value)
            self.cargar_productos()
        except (ValueError, TypeError) as ex:
            print(f"[ERROR] Error al filtrar categoría: {ex}")
            self.categoria_filtro = None
            self.cargar_productos()
    
    def cargar_productos(self):
        """Carga los productos desde la base de datos"""
        self.productos = self.producto_repo.listar(
            solo_activos=False,
            id_categoria=self.categoria_filtro,
            busqueda=self.busqueda_actual if self.busqueda_actual else None
        )
        
        # Resetear a página 1 cuando se busca o filtra
        self.pagina_actual = 1
        
        # Actualizar tabla y paginación si ya está construida
        if self.tabla_productos:
            self.tabla_productos = self._crear_tabla_productos()
            self.contenedor_paginacion = self._crear_paginacion()
            # Actualizar el contenedor principal
            if self.contenedor_principal:
                self.contenedor_principal.content.controls[4] = self.tabla_productos
                self.contenedor_principal.content.controls[5] = self.contenedor_paginacion
                self.page.update()
    
    def cargar_categorias(self):
        """Carga las categorías desde la base de datos"""
        self.categorias = self.categoria_repo.listar()
        
        # Actualizar dropdown si existe - Solo mostrar activas
        if self.dropdown_categoria_filtro:
            opciones = [ft.dropdown.Option(key="", text="Todas las categorías")]
            opciones.extend([
                ft.dropdown.Option(key=str(cat.id_categoria), text=cat.nombre) 
                for cat in self.categorias if cat.estado == "activa"
            ])
            self.dropdown_categoria_filtro.options = opciones
            self.page.update()
    
    def mostrar_mensaje(self, mensaje: str, tipo: str = "info", titulo: str = None):
        """
        Muestra un mensaje estilo SweetAlert compacto
        
        Args:
            mensaje: Texto del mensaje
            tipo: 'success', 'error', 'warning', 'info'
            titulo: Título opcional del mensaje
        """
        # Determinar icono y color según el tipo
        if tipo == "success":
            icono = ft.Icons.CHECK_CIRCLE
            color_icono = VoltTheme.SUCCESS
            titulo_default = "¡Éxito!"
        elif tipo == "error":
            icono = ft.Icons.ERROR
            color_icono = VoltTheme.DANGER
            titulo_default = "Error"
        elif tipo == "warning":
            icono = ft.Icons.WARNING
            color_icono = VoltTheme.WARNING
            titulo_default = "Advertencia"
        else:  # info
            icono = ft.Icons.INFO
            color_icono = VoltTheme.INFO
            titulo_default = "Información"
        
        titulo_final = titulo or titulo_default
        
        # Crear el diálogo de alerta compacto
        alerta = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(icono, color=color_icono, size=30),
                ft.Text(titulo_final, size=18, weight=ft.FontWeight.BOLD, color=color_icono)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            content=ft.Container(
                content=ft.Text(mensaje, size=13, text_align=ft.TextAlign.CENTER),
                padding=ft.padding.only(top=5, bottom=15, left=20, right=20),
                width=350
            ),
            actions=[
                ft.ElevatedButton(
                    "Aceptar",
                    on_click=lambda e: self.page.close(alerta),
                    bgcolor=color_icono,
                    color=ft.Colors.WHITE,
                    width=100,
                    height=40
                )
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            shape=ft.RoundedRectangleBorder(radius=10)
        )
        
        self.page.open(alerta)
    
    def cambiar_estado_producto(self, producto: Producto):
        """Activa o desactiva un producto"""
        nuevo_estado = "inactivo" if producto.estado == "activo" else "activo"
        accion = "desactivar" if nuevo_estado == "inactivo" else "activar"
        
        def confirmar(e):
            self.page.close(dialog_confirmacion)
            
            # Actualizar estado
            producto.estado = nuevo_estado
            resultado = self.producto_repo.actualizar(producto)
            
            if resultado['success']:
                self.mostrar_mensaje(
                    f"Producto {accion}do exitosamente",
                    "success"
                )
                self.cargar_productos()
            else:
                self.mostrar_mensaje(resultado['message'], "error")
        
        dialog_confirmacion = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"¿{accion.capitalize()} producto?", weight=ft.FontWeight.BOLD),
            content=ft.Text(
                f"¿Estás seguro de que deseas {accion} el producto '{producto.nombre}'?\n\n"
                f"{'Los productos inactivos no aparecerán en ventas.' if nuevo_estado == 'inactivo' else 'El producto volverá a estar disponible en ventas.'}"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog_confirmacion)),
                ft.ElevatedButton(
                    accion.capitalize(),
                    on_click=confirmar,
                    bgcolor=VoltTheme.DANGER if nuevo_estado == "inactivo" else VoltTheme.SUCCESS,
                    color=ft.Colors.WHITE
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.open(dialog_confirmacion)
    
    def mostrar_detalle_producto(self, producto: Producto):
        """Muestra el detalle completo de un producto"""
        # Obtener nombre de categoría
        categoria_nombre = "Sin categoría"
        if producto.id_categoria:
            for cat in self.categorias:
                if cat.id_categoria == producto.id_categoria:
                    categoria_nombre = cat.nombre
                    break
        
        # Color según estado
        if producto.estado == "activo":
            estado_color = VoltTheme.SUCCESS
        elif producto.estado == "inactivo":
            estado_color = VoltTheme.DANGER
        else:
            estado_color = VoltTheme.WARNING
        
        # Calcular margen de ganancia
        if producto.precio_compra > 0:
            margen = ((producto.precio_venta - producto.precio_compra) / producto.precio_compra) * 100
        else:
            margen = 0
        
        def crear_fila_detalle(label: str, valor: str, icono: str = None):
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icono, size=20, color=VoltTheme.TEXT_SECONDARY) if icono else ft.Container(width=0),
                    ft.Text(f"{label}:", size=14, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_SECONDARY, width=150),
                    ft.Text(valor, size=14, color=VoltTheme.TEXT_PRIMARY)
                ], spacing=10),
                padding=10,
                border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
            )
        
        contenido = ft.Container(
            content=ft.Column([
                # Header con código y estado
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(producto.nombre, size=24, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                            ft.Text(f"Código: {producto.codigo}", size=14, color=VoltTheme.TEXT_SECONDARY)
                        ], spacing=5),
                        ft.Container(
                            content=ft.Text(producto.estado.upper(), size=12, color=ft.Colors.WHITE),
                            bgcolor=estado_color,
                            padding=ft.padding.symmetric(horizontal=15, vertical=8),
                            border_radius=20
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=20,
                    bgcolor=VoltTheme.BG_SECONDARY,
                    border_radius=10
                ),
                
                ft.Container(height=20),
                
                # Información general
                ft.Text("Información General", size=16, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                crear_fila_detalle("Categoría", categoria_nombre, "category"),
                crear_fila_detalle("Unidad de Medida", producto.unidad_medida or "unidad", "straighten"),
                crear_fila_detalle("Descripción", producto.descripcion or "Sin descripción", "description"),
                crear_fila_detalle("Lote", producto.lote or "No especificado", "qr_code"),
                crear_fila_detalle("Fecha de Vencimiento", 
                                 producto.fecha_vencimiento.strftime("%d/%m/%Y") if producto.fecha_vencimiento else "Sin fecha", 
                                 "event"),
                crear_fila_detalle("Ubicación", producto.ubicacion or "No especificada", "place"),
                
                ft.Container(height=15),
                
                # Precios
                ft.Text("Precios y Margen", size=16, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                crear_fila_detalle("Precio de Compra", f"Q {producto.precio_compra:.2f}", "shopping_cart"),
                crear_fila_detalle("Precio de Venta", f"Q {producto.precio_venta:.2f}", "sell"),
                crear_fila_detalle("Margen de Ganancia", f"{margen:.2f}%", "trending_up"),
                
                ft.Container(height=15),
                
                # Stock
                ft.Text("Control de Stock", size=16, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                crear_fila_detalle("Stock Actual", str(producto.stock_actual), "inventory_2"),
                crear_fila_detalle("Stock Mínimo", str(producto.stock_minimo), "arrow_downward"),
                
                ft.Container(height=15),
                
                # Fechas
                ft.Text("Información de Registro", size=16, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                crear_fila_detalle("Fecha de Creación", 
                                 producto.fecha_creacion.strftime("%d/%m/%Y %H:%M") if producto.fecha_creacion else "N/A", 
                                 "calendar_today"),
                crear_fila_detalle("Última Actualización", 
                                 producto.fecha_actualizacion.strftime("%d/%m/%Y %H:%M") if producto.fecha_actualizacion else "N/A", 
                                 "update")
            ], scroll=ft.ScrollMode.AUTO, spacing=5),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            width=700,
            height=600
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon("info", size=28, color=VoltTheme.INFO),
                ft.Text("Detalle del Producto", size=20, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=contenido,
            actions=[
                ft.Row([
                    ft.OutlinedButton(
                        "Cerrar",
                        on_click=lambda e: self.page.close(dialog),
                        icon="close"
                    ),
                    ft.ElevatedButton(
                        "Editar",
                        on_click=lambda e: (self.page.close(dialog), self.mostrar_dialog_producto(producto)),
                        icon="edit",
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.open(dialog)

