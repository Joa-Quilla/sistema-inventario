import flet as ft
from datetime import datetime
from repositories.cliente_repository import ClienteRepository
from models.cliente import Cliente
from models.persona import Persona
from utils.theme import VoltTheme

class ClientesView:
    def __init__(self, page: ft.Page, on_back):
        self.page = page
        self.on_back = on_back
        self.cliente_repo = ClienteRepository()
        
        # Estado
        self.clientes = []
        self.clientes_filtrados = []
        self.cliente_seleccionado = None
        self.mostrar_inactivos = False
        
        # Paginación
        self.pagina_actual = 1
        self.items_por_pagina = 5
        
        # Referencias a controles
        self.tabla_clientes = None
        self.search_field = None
        self.paginacion_container = None
        self.estado_filtro_check = None
        
        # Modal
        self.modal = None
        self.form_nombre = None
        self.form_apellido = None
        self.form_dpi_nit = None
        self.form_telefono = None
        self.form_email = None
        self.form_direccion = None
        self.form_tipo_cliente = None
        self.form_limite_credito = None
        self.form_descuento_habitual = None
    
    def build(self):
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=VoltTheme.PRIMARY,
                    on_click=lambda _: self.on_back(),
                    tooltip="Volver al Dashboard"
                ),
                ft.Text(
                    "Gestión de Clientes",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        # Barra de búsqueda y acciones
        self.search_field = ft.TextField(
            hint_text="Buscar por nombre, apellido, NIT o teléfono...",
            prefix_icon=ft.Icons.SEARCH,
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            expand=True,
            on_change=self.buscar_clientes
        )
        
        self.estado_filtro_check = ft.Checkbox(
            label="Mostrar inactivos",
            value=False,
            on_change=self.cambiar_filtro_estado
        )
        
        barra_acciones = ft.Container(
            content=ft.Row([
                self.search_field,
                self.estado_filtro_check,
                ft.ElevatedButton(
                    "Nuevo Cliente",
                    icon=ft.Icons.ADD,
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.abrir_modal_cliente()
                ),
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        
        # Tabla de clientes
        self.tabla_clientes = ft.Column(
            spacing=0,
            scroll=ft.ScrollMode.AUTO
        )
        
        tabla_container = ft.Container(
            content=self.tabla_clientes,
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
            barra_acciones,
            tabla_container,
            paginacion_wrapper
        ], spacing=0, expand=True)
        
        # Cargar datos iniciales
        self.cargar_clientes()
        
        return content
    
    def cargar_clientes(self):
        """Carga la lista de clientes desde la base de datos"""
        try:
            solo_activos = not self.mostrar_inactivos
            self.clientes = self.cliente_repo.listar(solo_activos=solo_activos)
            self.clientes_filtrados = self.clientes.copy()
            self.pagina_actual = 1
            self.actualizar_tabla()
            self.actualizar_paginacion()
        except Exception as e:
            self.mostrar_mensaje("Error", f"Error al cargar clientes: {str(e)}", "error")
    
    def buscar_clientes(self, e):
        """Filtra clientes por el texto de búsqueda"""
        termino = self.search_field.value.lower().strip()
        
        if not termino:
            self.clientes_filtrados = self.clientes.copy()
        else:
            solo_activos = not self.mostrar_inactivos
            self.clientes_filtrados = self.cliente_repo.listar(
                busqueda=termino,
                solo_activos=solo_activos
            )
        
        self.pagina_actual = 1
        self.actualizar_tabla()
        self.actualizar_paginacion()
    
    def cambiar_filtro_estado(self, e):
        """Cambia el filtro de estado activo/inactivo"""
        self.mostrar_inactivos = self.estado_filtro_check.value
        self.cargar_clientes()
    
    def actualizar_tabla(self):
        """Actualiza la tabla de clientes con los datos filtrados y paginados"""
        self.tabla_clientes.controls.clear()
        
        # Header de la tabla
        header = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text("Nombre Completo", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=2),
                ft.Container(ft.Text("NIT", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Teléfono", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Tipo", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=2),
            ]),
            bgcolor=VoltTheme.PRIMARY,
            padding=15,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        self.tabla_clientes.controls.append(header)
        
        # Calcular índices de paginación
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        clientes_pagina = self.clientes_filtrados[inicio:fin]
        
        # Filas de clientes
        if not clientes_pagina:
            self.tabla_clientes.controls.append(
                ft.Container(
                    content=ft.Text("No hay clientes para mostrar", size=14, color=ft.Colors.GREY_600),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        else:
            for cliente in clientes_pagina:
                fila = self.crear_fila_cliente(cliente)
                self.tabla_clientes.controls.append(fila)
        
        self.page.update()
    
    def crear_fila_cliente(self, cliente: Cliente):
        """Crea una fila de la tabla para un cliente"""
        # Color de estado
        estado_color = VoltTheme.SUCCESS if cliente.estado else VoltTheme.DANGER
        estado_texto = "Activo" if cliente.estado else "Inactivo"
        
        # Tipo cliente capitalizado
        tipo_texto = cliente.tipo_cliente.capitalize() if cliente.tipo_cliente else "N/A"
        
        fila = ft.Container(
            content=ft.Row([
                ft.Container(
                    ft.Text(cliente.persona.nombre_completo, size=13),
                    expand=2
                ),
                ft.Container(
                    ft.Text(cliente.persona.dpi_nit or "N/A", size=13),
                    expand=1
                ),
                ft.Container(
                    ft.Text(cliente.persona.telefono or "N/A", size=13),
                    expand=1
                ),
                ft.Container(
                    ft.Text(tipo_texto, size=13),
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
                            on_click=lambda _, c=cliente: self.ver_detalle_cliente(c)
                        ),
                        ft.IconButton(
                            icon="edit",
                            icon_size=18,
                            icon_color=VoltTheme.WARNING,
                            tooltip="Editar",
                            on_click=lambda _, c=cliente: self.abrir_modal_cliente(c)
                        ),
                        ft.IconButton(
                            icon="power_settings_new" if cliente.estado else "check_circle",
                            icon_size=18,
                            icon_color=VoltTheme.DANGER if cliente.estado else VoltTheme.SUCCESS,
                            tooltip="Desactivar" if cliente.estado else "Activar",
                            on_click=lambda _, c=cliente: self.confirmar_cambio_estado(c)
                        ),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    expand=2,
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
        
        total_paginas = (len(self.clientes_filtrados) + self.items_por_pagina - 1) // self.items_por_pagina
        
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
    
    def abrir_modal_cliente(self, cliente: Cliente = None):
        """Abre el modal para crear o editar un cliente"""
        self.cliente_seleccionado = cliente
        es_edicion = cliente is not None
        
        # Resetear errores
        def limpiar_errores():
            self.form_nombre.error_text = None
            self.form_apellido.error_text = None
            self.form_dpi_nit.error_text = None
            self.form_telefono.error_text = None
            self.form_email.error_text = None
            self.form_direccion.error_text = None
            self.form_tipo_cliente.error_text = None
            self.form_limite_credito.error_text = None
            self.form_descuento_habitual.error_text = None
        
        # Campos del formulario
        self.form_nombre = ft.TextField(
            label="Nombre *",
            value=cliente.persona.nombre if es_edicion else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        self.form_apellido = ft.TextField(
            label="Apellido *",
            value=cliente.persona.apellido if es_edicion else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY
        )
        
        self.form_dpi_nit = ft.TextField(
            label="DPI/NIT",
            value=cliente.persona.dpi_nit if es_edicion and cliente.persona.dpi_nit else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Opcional"
        )
        
        self.form_telefono = ft.TextField(
            label="Teléfono",
            value=cliente.persona.telefono if es_edicion and cliente.persona.telefono else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Opcional"
        )
        
        self.form_email = ft.TextField(
            label="Email",
            value=cliente.persona.email if es_edicion and cliente.persona.email else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Opcional"
        )
        
        self.form_direccion = ft.TextField(
            label="Dirección",
            value=cliente.persona.direccion if es_edicion and cliente.persona.direccion else "",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            multiline=True,
            min_lines=2,
            max_lines=3,
            hint_text="Opcional"
        )
        
        self.form_tipo_cliente = ft.Dropdown(
            label="Tipo de Cliente *",
            value=cliente.tipo_cliente if es_edicion else "minorista",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            options=[
                ft.dropdown.Option("minorista", "Minorista"),
                ft.dropdown.Option("mayorista", "Mayorista"),
            ]
        )
        
        self.form_limite_credito = ft.TextField(
            label="Límite de Crédito",
            value=str(cliente.limite_credito) if es_edicion and cliente.limite_credito else "0.00",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="0.00"
        )
        
        self.form_descuento_habitual = ft.TextField(
            label="Descuento Habitual (%)",
            value=str(cliente.descuento_habitual) if es_edicion and cliente.descuento_habitual else "0.00",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="0.00 - 100.00"
        )
        
        # Contenido del modal
        modal_content = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Editar Cliente" if es_edicion else "Nuevo Cliente",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                ft.Row([
                    ft.Column([self.form_nombre], expand=1),
                    ft.Column([self.form_apellido], expand=1),
                ], spacing=20),
                ft.Row([
                    ft.Column([self.form_dpi_nit], expand=1),
                    ft.Column([self.form_telefono], expand=1),
                ], spacing=20),
                self.form_email,
                self.form_direccion,
                ft.Row([
                    ft.Column([self.form_tipo_cliente], expand=1),
                    ft.Column([self.form_limite_credito], expand=1),
                ], spacing=20),
                self.form_descuento_habitual,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            width=1000,
            height=450,
            border_radius=10
        )
        
        # Contenedor de botones (fuera del scroll)
        botones = ft.Container(
            content=ft.Row([
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda _: self.cerrar_modal()
                ),
                ft.ElevatedButton(
                    "Guardar",
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.guardar_cliente()
                ),
            ], alignment=ft.MainAxisAlignment.END, spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.only(left=30, right=30, bottom=20),
            width=1000
        )
        
        # Contenedor principal con scroll y botones
        contenedor_principal = ft.Column([
            modal_content,
            botones
        ], spacing=0)
        
        self.modal = ft.AlertDialog(
            modal=True,
            content=contenedor_principal
        )
        
        self.page.open(self.modal)
    
    def guardar_cliente(self):
        """Valida y guarda el cliente (crear o actualizar)"""
        # Limpiar errores previos
        self.form_nombre.error_text = None
        self.form_apellido.error_text = None
        self.form_dpi_nit.error_text = None
        self.form_telefono.error_text = None
        self.form_email.error_text = None
        self.form_direccion.error_text = None
        self.form_tipo_cliente.error_text = None
        self.form_limite_credito.error_text = None
        self.form_descuento_habitual.error_text = None
        
        # Validaciones inline
        tiene_errores = False
        
        # Validar nombre (requerido)
        if not self.form_nombre.value or not self.form_nombre.value.strip():
            self.form_nombre.error_text = "El nombre es requerido"
            tiene_errores = True
        
        # Validar apellido (requerido)
        if not self.form_apellido.value or not self.form_apellido.value.strip():
            self.form_apellido.error_text = "El apellido es requerido"
            tiene_errores = True
        
        # Validar email (formato si se proporciona)
        if self.form_email.value and self.form_email.value.strip():
            if "@" not in self.form_email.value or "." not in self.form_email.value:
                self.form_email.error_text = "Formato de email inválido"
                tiene_errores = True
        
        # Validar tipo_cliente (requerido)
        if not self.form_tipo_cliente.value:
            self.form_tipo_cliente.error_text = "Seleccione un tipo de cliente"
            tiene_errores = True
        
        # Validar límite_credito (numérico)
        try:
            limite_credito = float(self.form_limite_credito.value or "0")
            if limite_credito < 0:
                self.form_limite_credito.error_text = "El límite no puede ser negativo"
                tiene_errores = True
        except ValueError:
            self.form_limite_credito.error_text = "Ingrese un número válido"
            tiene_errores = True
        
        # Validar descuento_habitual (0-100)
        try:
            descuento = float(self.form_descuento_habitual.value or "0")
            if descuento < 0 or descuento > 100:
                self.form_descuento_habitual.error_text = "El descuento debe estar entre 0 y 100"
                tiene_errores = True
        except ValueError:
            self.form_descuento_habitual.error_text = "Ingrese un número válido"
            tiene_errores = True
        
        if tiene_errores:
            self.page.update()
            return
        
        # Crear objetos Persona y Cliente
        try:
            persona = Persona(
                nombre=self.form_nombre.value.strip(),
                apellido=self.form_apellido.value.strip(),
                dpi_nit=self.form_dpi_nit.value.strip() if self.form_dpi_nit.value else None,
                telefono=self.form_telefono.value.strip() if self.form_telefono.value else None,
                email=self.form_email.value.strip() if self.form_email.value else None,
                direccion=self.form_direccion.value.strip() if self.form_direccion.value else None,
                estado=True
            )
            
            cliente = Cliente(
                persona=persona,
                tipo_cliente=self.form_tipo_cliente.value,
                limite_credito=float(self.form_limite_credito.value or "0"),
                descuento_habitual=float(self.form_descuento_habitual.value or "0")
            )
            
            # Validar con el modelo
            es_valido, mensaje_error = cliente.validar()
            if not es_valido:
                self.mostrar_mensaje("Error de Validación", mensaje_error, "error")
                return
            
            # Guardar en base de datos
            if self.cliente_seleccionado:
                # Actualizar
                cliente.id_cliente = self.cliente_seleccionado.id_cliente
                persona.id_persona = self.cliente_seleccionado.persona.id_persona
                cliente.estado = self.cliente_seleccionado.estado  # Mantener el estado actual
                resultado = self.cliente_repo.actualizar(cliente)
                if resultado.get('success'):
                    self.mostrar_mensaje("Éxito", "Cliente actualizado correctamente", "success")
                else:
                    mensaje_error = resultado.get('message', 'Error desconocido')
                    
                    # Detectar error de DPI/NIT duplicado
                    if 'duplicate' in mensaje_error.lower() or 'unique' in mensaje_error.lower() or 'dpi_nit' in mensaje_error.lower():
                        self.mostrar_mensaje("DPI/NIT Duplicado", 
                            "El DPI/NIT ingresado ya está registrado para otro cliente. Por favor ingrese un DPI/NIT diferente.", 
                            "warning")
                    else:
                        self.mostrar_mensaje("Error", mensaje_error, "error")
                    return
            else:
                # Crear nuevo
                cliente.estado = True  # Los nuevos clientes siempre están activos
                resultado = self.cliente_repo.crear(cliente)
                if resultado.get('success'):
                    self.mostrar_mensaje("Éxito", "Cliente creado correctamente", "success")
                else:
                    mensaje_error = resultado.get('message', 'Error desconocido')
                    
                    # Detectar error de DPI/NIT duplicado
                    if 'duplicate' in mensaje_error.lower() or 'unique' in mensaje_error.lower() or 'dpi_nit' in mensaje_error.lower():
                        self.mostrar_mensaje("DPI/NIT Duplicado", 
                            "El DPI/NIT ingresado ya está registrado para otro cliente. Por favor ingrese un DPI/NIT diferente.", 
                            "warning")
                    else:
                        self.mostrar_mensaje("Error", mensaje_error, "error")
                    return
            
            self.cerrar_modal()
            self.cargar_clientes()
            
        except Exception as e:
            error_msg = str(e)
            
            # Detectar error de DPI/NIT duplicado en la excepción
            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower() or 'dpi_nit' in error_msg.lower():
                self.mostrar_mensaje("DPI/NIT Duplicado", 
                    "El DPI/NIT ingresado ya está registrado para otro cliente. Por favor ingrese un DPI/NIT diferente.", 
                    "warning")
            else:
                self.mostrar_mensaje("Error", f"Error al guardar el cliente: {error_msg}", "error")
    
    def ver_detalle_cliente(self, cliente: Cliente):
        """Muestra el detalle completo del cliente"""
        # Formatear fechas
        fecha_registro = "N/A"
        if cliente.persona.fecha_registro:
            if isinstance(cliente.persona.fecha_registro, str):
                fecha_registro = cliente.persona.fecha_registro
            else:
                fecha_registro = cliente.persona.fecha_registro.strftime("%d/%m/%Y")
        
        fecha_primera_compra = "N/A"
        if cliente.fecha_primera_compra:
            if isinstance(cliente.fecha_primera_compra, str):
                fecha_primera_compra = cliente.fecha_primera_compra
            else:
                fecha_primera_compra = cliente.fecha_primera_compra.strftime("%d/%m/%Y")
        
        fecha_actualizacion = "N/A"
        if cliente.fecha_actualizacion:
            if isinstance(cliente.fecha_actualizacion, str):
                fecha_actualizacion = cliente.fecha_actualizacion
            else:
                fecha_actualizacion = cliente.fecha_actualizacion.strftime("%d/%m/%Y %H:%M")
        
        # Contenido del detalle
        detalle_content = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Detalle del Cliente",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                
                # Información Personal
                ft.Text("Información Personal", size=16, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                ft.Row([
                    ft.Column([
                        ft.Text("Nombre Completo:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(cliente.persona.nombre_completo, size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("DPI/NIT:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(cliente.persona.dpi_nit or "N/A", size=13),
                    ], expand=1),
                ]),
                ft.Row([
                    ft.Column([
                        ft.Text("Teléfono:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(cliente.persona.telefono or "N/A", size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Email:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(cliente.persona.email or "N/A", size=13),
                    ], expand=1),
                ]),
                ft.Column([
                    ft.Text("Dirección:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(cliente.persona.direccion or "N/A", size=13),
                ]),
                
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                
                # Información Comercial
                ft.Text("Información Comercial", size=16, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                ft.Row([
                    ft.Column([
                        ft.Text("Tipo de Cliente:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(cliente.tipo_cliente.capitalize() if cliente.tipo_cliente else "N/A", size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Estado:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Container(
                            content=ft.Text(
                                "Activo" if cliente.estado else "Inactivo",
                                size=11,
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD
                            ),
                            bgcolor=VoltTheme.SUCCESS if cliente.estado else VoltTheme.DANGER,
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            border_radius=12
                        ),
                    ], expand=1),
                ]),
                ft.Row([
                    ft.Column([
                        ft.Text("Límite de Crédito:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(f"Q {cliente.limite_credito:.2f}" if cliente.limite_credito else "Q 0.00", size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Descuento Habitual:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(f"{cliente.descuento_habitual:.2f}%" if cliente.descuento_habitual else "0.00%", size=13),
                    ], expand=1),
                ]),
                ft.Row([
                    ft.Column([
                        ft.Text("Total Compras:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(f"Q {cliente.total_compras:.2f}" if cliente.total_compras else "Q 0.00", size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Primera Compra:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(fecha_primera_compra, size=13),
                    ], expand=1),
                ]),
                
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                
                # Fechas
                ft.Text("Registro y Actualización", size=16, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                ft.Row([
                    ft.Column([
                        ft.Text("Fecha de Registro:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(fecha_registro, size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Última Actualización:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(fecha_actualizacion, size=13),
                    ], expand=1),
                ]),
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
    
    def confirmar_cambio_estado(self, cliente: Cliente):
        """Muestra diálogo de confirmación para cambiar el estado del cliente"""
        accion = "desactivar" if cliente.estado else "activar"
        
        def cambiar_estado(_):
            try:
                if cliente.estado:
                    # Desactivar
                    self.cliente_repo.eliminar(cliente.id_cliente)
                    self.mostrar_mensaje("Éxito", "Cliente desactivado correctamente", "success")
                else:
                    # Activar
                    cliente.estado = True
                    self.cliente_repo.actualizar(cliente)
                    self.mostrar_mensaje("Éxito", "Cliente activado correctamente", "success")
                
                self.cerrar_modal()
                self.cargar_clientes()
            except Exception as e:
                self.mostrar_mensaje("Error", f"Error al cambiar estado: {str(e)}", "error")
        
        confirmacion = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Confirmar {accion}"),
            content=ft.Text(f"¿Está seguro que desea {accion} al cliente {cliente.persona.nombre_completo}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                ft.ElevatedButton(
                    "Confirmar",
                    bgcolor=VoltTheme.DANGER if cliente.estado else VoltTheme.SUCCESS,
                    color=ft.Colors.WHITE,
                    on_click=cambiar_estado
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
