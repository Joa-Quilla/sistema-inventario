import flet as ft
from datetime import datetime
import math
from services.caja_service import CajaService
from models.caja import Caja, MovimientoCaja
from utils.theme import VoltTheme


class CajasView:
    """Vista para gestión de Cajas (apertura, cierre, movimientos)"""
    
    def __init__(self, page: ft.Page, empleado):
        self.page = page
        self.empleado = empleado
        self.caja_service = CajaService()
        
        # Estado
        self.caja_actual = None
        self.movimientos = []
        self.historial = []
        
        # Paginación
        self.pagina_actual = 1
        self.items_por_pagina = 5
        
        # Referencias a controles
        self.tabla_historial = None
        self.paginacion_container = None
        self.modal = None
        self.info_caja_actual = None
        
        # Para nueva caja/cierre
        self.campo_monto_inicial = None
        self.campo_observaciones_apertura = None
        self.campo_monto_final = None
        self.campo_observaciones_cierre = None
    
    def build(self):
        # Verificar caja actual
        self.verificar_caja_actual()
        
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
                    "Gestión de Cajas",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        # Info de caja actual
        self.info_caja_actual = ft.Container(
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        self.actualizar_info_caja_actual()
        
        # Tabla de historial
        self.tabla_historial = ft.Column(
            spacing=0,
            scroll=ft.ScrollMode.AUTO
        )
        
        tabla_container = ft.Container(
            content=ft.Column([
                ft.Text("Historial de Cajas", size=18, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                self.tabla_historial
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=20,
            expand=True
        )
        
        # Paginación
        self.paginacion_container = ft.Container(
            content=ft.Row([], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        
        # Layout principal
        contenido = ft.Column([
            header,
            self.info_caja_actual,
            tabla_container,
            self.paginacion_container
        ], spacing=0, expand=True)
        
        # Cargar historial
        self.cargar_historial()
        
        return contenido
    
    def verificar_caja_actual(self):
        """Verifica si hay una caja abierta"""
        resultado = self.caja_service.verificar_caja_abierta(self.empleado['id_empleado'])
        if resultado['success']:
            self.caja_actual = resultado['caja']
        else:
            self.caja_actual = None
    
    def actualizar_info_caja_actual(self):
        """Actualiza la información de la caja actual"""
        self.info_caja_actual.content = None
        
        if self.caja_actual:
            # Hay caja abierta - mostrar info y botones
            fecha_apertura = self.caja_actual['fecha_apertura']
            if isinstance(fecha_apertura, str):
                try:
                    fecha_apertura = datetime.fromisoformat(fecha_apertura.replace('Z', '+00:00'))
                except:
                    pass
            
            fecha_str = fecha_apertura.strftime("%d/%m/%Y %H:%M") if isinstance(fecha_apertura, datetime) else str(fecha_apertura)
            
            self.info_caja_actual.content = ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=VoltTheme.SUCCESS, size=40),
                        ft.Column([
                            ft.Text("CAJA ABIERTA", size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.SUCCESS),
                            ft.Text(f"Apertura: {fecha_str}", size=14, color=VoltTheme.TEXT_SECONDARY),
                            ft.Text(f"Monto Inicial: Q {self.caja_actual['monto_inicial']:.2f}", size=16, weight=ft.FontWeight.BOLD),
                        ], spacing=2),
                        ft.Container(expand=True),
                        ft.Column([
                            ft.ElevatedButton(
                                "Registrar Movimiento",
                                icon=ft.Icons.ADD_CIRCLE,
                                bgcolor=VoltTheme.INFO,
                                color=ft.Colors.WHITE,
                                on_click=lambda _: self.abrir_modal_movimiento()
                            ),
                            ft.ElevatedButton(
                                "Cerrar Caja",
                                icon=ft.Icons.LOCK,
                                bgcolor=VoltTheme.DANGER,
                                color=ft.Colors.WHITE,
                                on_click=lambda _: self.abrir_modal_cerrar_caja()
                            ),
                        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.END)
                    ], spacing=20),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=20,
                    border_radius=10,
                    border=ft.border.all(2, VoltTheme.SUCCESS)
                )
            ])
        else:
            # No hay caja abierta
            self.info_caja_actual.content = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=VoltTheme.WARNING, size=40),
                    ft.Column([
                        ft.Text("NO HAY CAJA ABIERTA", size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.WARNING),
                        ft.Text("Debe abrir una caja para poder realizar ventas", size=14, color=VoltTheme.TEXT_SECONDARY),
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Abrir Caja",
                        icon=ft.Icons.LOCK_OPEN,
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: self.abrir_modal_abrir_caja()
                    ),
                ], spacing=20),
                bgcolor=ft.Colors.ORANGE_50,
                padding=20,
                border_radius=10,
                border=ft.border.all(2, VoltTheme.WARNING)
            )
        
        self.page.update()
    
    def cargar_historial(self):
        """Carga el historial de cajas"""
        try:
            # Obtener todas las cajas del empleado
            todas_cajas = self.caja_service.obtener_historial_cajas(
                id_empleado=self.empleado['id_empleado'],
                limit=100
            )
            
            # Filtrar solo cerradas para el historial
            self.historial = [c for c in todas_cajas if c['estado'] == 'cerrada']
            
            total = len(self.historial)
            total_paginas = math.ceil(total / self.items_por_pagina) if total > 0 else 1
            
            self.actualizar_tabla_historial()
            self.actualizar_paginacion(total_paginas)
        except Exception as e:
            print(f"Error al cargar historial: {e}")
            self.mostrar_alerta("Error", f"No se pudo cargar el historial: {str(e)}", VoltTheme.DANGER)
    
    def actualizar_tabla_historial(self):
        """Actualiza la tabla de historial"""
        self.tabla_historial.controls.clear()
        
        # Header de la tabla
        header = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text("Fecha Apertura", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=2),
                ft.Container(ft.Text("Fecha Cierre", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=2),
                ft.Container(ft.Text("Monto Inicial", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Monto Final", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Diferencia", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
            ]),
            bgcolor=VoltTheme.SECONDARY,
            padding=10,
            border_radius=ft.border_radius.only(top_left=5, top_right=5)
        )
        self.tabla_historial.controls.append(header)
        
        # Calcular índices para paginación
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        cajas_pagina = self.historial[inicio:fin]
        
        # Filas de datos
        for caja in cajas_pagina:
            fila = self._crear_fila_caja(caja)
            self.tabla_historial.controls.append(fila)
        
        if not self.historial:
            mensaje_vacio = ft.Container(
                content=ft.Text(
                    "No hay cajas cerradas en el historial",
                    size=14,
                    color=VoltTheme.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=40,
                alignment=ft.alignment.center
            )
            self.tabla_historial.controls.append(mensaje_vacio)
        
        self.page.update()
    
    def _crear_fila_caja(self, caja):
        """Crea una fila para una caja"""
        # Formato de fechas
        fecha_apertura = caja['fecha_apertura']
        if isinstance(fecha_apertura, str):
            try:
                fecha_apertura = datetime.fromisoformat(fecha_apertura.replace('Z', '+00:00'))
            except:
                pass
        apertura_str = fecha_apertura.strftime("%d/%m/%Y %H:%M") if isinstance(fecha_apertura, datetime) else str(fecha_apertura)
        
        fecha_cierre = caja['fecha_cierre']
        if isinstance(fecha_cierre, str):
            try:
                fecha_cierre = datetime.fromisoformat(fecha_cierre.replace('Z', '+00:00'))
            except:
                pass
        cierre_str = fecha_cierre.strftime("%d/%m/%Y %H:%M") if isinstance(fecha_cierre, datetime) else "No cerrada"
        
        # Color de diferencia
        diferencia = caja.get('diferencia', 0) or 0
        if diferencia > 0:
            diff_color = VoltTheme.SUCCESS
            diff_text = f"+Q {diferencia:.2f}"
        elif diferencia < 0:
            diff_color = VoltTheme.DANGER
            diff_text = f"-Q {abs(diferencia):.2f}"
        else:
            diff_color = VoltTheme.TEXT_SECONDARY
            diff_text = "Q 0.00"
        
        fila = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text(apertura_str, size=12, text_align=ft.TextAlign.CENTER), expand=2, alignment=ft.alignment.center),
                ft.Container(ft.Text(cierre_str, size=12, text_align=ft.TextAlign.CENTER), expand=2, alignment=ft.alignment.center),
                ft.Container(ft.Text(f"Q {caja['monto_inicial']:.2f}", size=12, text_align=ft.TextAlign.CENTER), expand=1, alignment=ft.alignment.center),
                ft.Container(ft.Text(f"Q {caja.get('monto_final', 0):.2f}", size=12, text_align=ft.TextAlign.CENTER), expand=1, alignment=ft.alignment.center),
                ft.Container(
                    ft.Text(diff_text, size=12, weight=ft.FontWeight.BOLD, color=diff_color, text_align=ft.TextAlign.CENTER),
                    expand=1,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.IconButton(
                        icon="visibility",
                        icon_size=18,
                        icon_color=VoltTheme.INFO,
                        tooltip="Ver detalle",
                        on_click=lambda _, c=caja: self.ver_detalle_caja(c['id_caja'])
                    ),
                    expand=1,
                    alignment=ft.alignment.center
                ),
            ]),
            padding=10,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        return fila
    
    def actualizar_paginacion(self, total_paginas):
        """Actualiza los controles de paginación"""
        botones = []
        
        if total_paginas <= 1:
            self.paginacion_container.content = ft.Row([], alignment=ft.MainAxisAlignment.CENTER)
            self.page.update()
            return
        
        # Botón anterior
        botones.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual - 1),
                disabled=self.pagina_actual == 1,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual > 1 else VoltTheme.TEXT_SECONDARY
            )
        )
        
        # Números de página (mostrar máximo 5)
        inicio = max(1, self.pagina_actual - 2)
        fin = min(total_paginas, inicio + 4)
        
        if fin - inicio < 4:
            inicio = max(1, fin - 4)
        
        for i in range(inicio, fin + 1):
            if i == self.pagina_actual:
                botones.append(
                    ft.Container(
                        content=ft.Text(str(i), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=VoltTheme.PRIMARY,
                        width=35,
                        height=35,
                        border_radius=5,
                        alignment=ft.alignment.center
                    )
                )
            else:
                botones.append(
                    ft.TextButton(
                        text=str(i),
                        on_click=lambda _, p=i: self.cambiar_pagina(p)
                    )
                )
        
        # Botón siguiente
        botones.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual + 1),
                disabled=self.pagina_actual == total_paginas,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual < total_paginas else VoltTheme.TEXT_SECONDARY
            )
        )
        
        self.paginacion_container.content = ft.Row(botones, alignment=ft.MainAxisAlignment.CENTER)
        self.page.update()
    
    def cambiar_pagina(self, nueva_pagina):
        """Cambia a una página específica"""
        self.pagina_actual = nueva_pagina
        self.actualizar_tabla_historial()
        total = len(self.historial)
        total_paginas = math.ceil(total / self.items_por_pagina) if total > 0 else 1
        self.actualizar_paginacion(total_paginas)
    
    def abrir_modal_abrir_caja(self):
        """Abre el modal para abrir una caja"""
        self.campo_monto_inicial = ft.TextField(
            label="Monto Inicial *",
            hint_text="Ej: 500.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=VoltTheme.BORDER_COLOR,
            width=200
        )
        
        self.campo_observaciones_apertura = ft.TextField(
            label="Observaciones",
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=VoltTheme.BORDER_COLOR
        )
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOCK_OPEN, color=VoltTheme.PRIMARY, size=30),
                    ft.Text("Abrir Caja", size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Text("Ingrese el monto inicial con el que abre la caja:", size=14),
                self.campo_monto_inicial,
                self.campo_observaciones_apertura,
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Abrir Caja",
                        icon=ft.Icons.CHECK,
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: self.abrir_caja()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=400,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def abrir_caja(self):
        """Abre una nueva caja"""
        try:
            if not self.campo_monto_inicial.value or float(self.campo_monto_inicial.value) < 0:
                self.mostrar_alerta("Error", "Ingrese un monto inicial válido", VoltTheme.WARNING)
                return
            
            resultado = self.caja_service.abrir_caja(
                id_empleado=self.empleado['id_empleado'],
                monto_inicial=float(self.campo_monto_inicial.value),
                observaciones=self.campo_observaciones_apertura.value or ""
            )
            
            if resultado['success']:
                self.mostrar_alerta("Éxito", "Caja abierta exitosamente", VoltTheme.SUCCESS)
                self.cerrar_modal()
                self.verificar_caja_actual()
                self.actualizar_info_caja_actual()
            else:
                self.mostrar_alerta("Error", resultado['message'], VoltTheme.DANGER)
        except ValueError:
            self.mostrar_alerta("Error", "Monto inválido", VoltTheme.WARNING)
        except Exception as e:
            print(f"Error al abrir caja: {e}")
            self.mostrar_alerta("Error", f"No se pudo abrir la caja: {str(e)}", VoltTheme.DANGER)
    
    def abrir_modal_cerrar_caja(self):
        """Abre el modal para cerrar la caja"""
        if not self.caja_actual:
            self.mostrar_alerta("Error", "No hay caja abierta", VoltTheme.WARNING)
            return
        
        # Obtener resumen de la caja
        resumen = self.caja_service.obtener_resumen_caja(self.caja_actual['id_caja'])
        
        monto_esperado = (
            self.caja_actual['monto_inicial'] +
            resumen.get('total_ingresos', 0) -
            resumen.get('total_egresos', 0)
        )
        
        self.campo_monto_final = ft.TextField(
            label="Monto Final Real *",
            hint_text=f"Esperado: Q {monto_esperado:.2f}",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=VoltTheme.BORDER_COLOR,
            width=200
        )
        
        self.campo_observaciones_cierre = ft.TextField(
            label="Observaciones de Cierre",
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=VoltTheme.BORDER_COLOR
        )
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOCK, color=VoltTheme.DANGER, size=30),
                    ft.Text("Cerrar Caja", size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.DANGER)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("Resumen de Caja", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Row([
                            ft.Text("Monto Inicial:", size=14, color=ft.Colors.WHITE),
                            ft.Container(expand=True),
                            ft.Text(f"Q {self.caja_actual['monto_inicial']:.2f}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]),
                        ft.Row([
                            ft.Text("Total Ingresos:", size=14, color=ft.Colors.WHITE),
                            ft.Container(expand=True),
                            ft.Text(f"Q {resumen.get('total_ingresos', 0):.2f}", size=14, color=VoltTheme.SUCCESS)
                        ]),
                        ft.Row([
                            ft.Text("Total Egresos:", size=14, color=ft.Colors.WHITE),
                            ft.Container(expand=True),
                            ft.Text(f"Q {resumen.get('total_egresos', 0):.2f}", size=14, color=VoltTheme.DANGER)
                        ]),
                        ft.Divider(height=1, color=ft.Colors.WHITE24),
                        ft.Row([
                            ft.Text("Monto Esperado:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Container(expand=True),
                            ft.Text(f"Q {monto_esperado:.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]),
                    ], spacing=8),
                    bgcolor=VoltTheme.SECONDARY,
                    padding=15,
                    border_radius=5
                ),
                
                ft.Text("Ingrese el monto real contado en la caja:", size=14),
                self.campo_monto_final,
                self.campo_observaciones_cierre,
                
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Cerrar Caja",
                        icon=ft.Icons.CHECK,
                        bgcolor=VoltTheme.DANGER,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: self.cerrar_caja()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=500,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def cerrar_caja(self):
        """Cierra la caja actual"""
        try:
            if not self.campo_monto_final.value:
                self.mostrar_alerta("Error", "Ingrese el monto final", VoltTheme.WARNING)
                return
            
            monto_final = float(self.campo_monto_final.value)
            
            resultado = self.caja_service.cerrar_caja(
                id_caja=self.caja_actual['id_caja'],
                monto_final=monto_final,
                observaciones=self.campo_observaciones_cierre.value or ""
            )
            
            if resultado['success']:
                diferencia = resultado.get('diferencia', 0)
                mensaje = f"Caja cerrada exitosamente.\nDiferencia: Q {diferencia:.2f}"
                self.mostrar_alerta("Éxito", mensaje, VoltTheme.SUCCESS)
                self.cerrar_modal()
                self.verificar_caja_actual()
                self.actualizar_info_caja_actual()
                self.cargar_historial()
            else:
                self.mostrar_alerta("Error", resultado['message'], VoltTheme.DANGER)
        except ValueError:
            self.mostrar_alerta("Error", "Monto inválido", VoltTheme.WARNING)
        except Exception as e:
            print(f"Error al cerrar caja: {e}")
            self.mostrar_alerta("Error", f"No se pudo cerrar la caja: {str(e)}", VoltTheme.DANGER)
    
    def abrir_modal_movimiento(self):
        """Abre el modal para registrar un movimiento"""
        if not self.caja_actual:
            self.mostrar_alerta("Error", "No hay caja abierta", VoltTheme.WARNING)
            return
        
        tipo_dropdown = ft.Dropdown(
            label="Tipo de Movimiento *",
            options=[
                ft.dropdown.Option(key="ingreso", text="Ingreso"),
                ft.dropdown.Option(key="egreso", text="Egreso")
            ],
            border_color=VoltTheme.BORDER_COLOR,
            width=200
        )
        
        campo_concepto = ft.TextField(
            label="Concepto *",
            hint_text="Ej: Retiro de efectivo",
            border_color=VoltTheme.BORDER_COLOR
        )
        
        campo_monto = ft.TextField(
            label="Monto *",
            hint_text="Ej: 100.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=VoltTheme.BORDER_COLOR,
            width=150
        )
        
        campo_obs = ft.TextField(
            label="Observaciones",
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=VoltTheme.BORDER_COLOR
        )
        
        def guardar_movimiento():
            try:
                if not tipo_dropdown.value or not campo_concepto.value or not campo_monto.value:
                    self.mostrar_alerta("Error", "Complete todos los campos requeridos", VoltTheme.WARNING)
                    return
                
                # Validar monto
                try:
                    monto = float(campo_monto.value.strip())
                    if monto <= 0:
                        self.mostrar_alerta("Error", "El monto debe ser mayor a cero", VoltTheme.WARNING)
                        return
                except ValueError:
                    self.mostrar_alerta("Error", "Ingrese un monto válido", VoltTheme.WARNING)
                    return
                
                # Registrar el movimiento
                resultado = self.caja_service.registrar_movimiento(
                    id_caja=self.caja_actual['id_caja'],
                    tipo=tipo_dropdown.value,
                    monto=monto,
                    concepto=campo_concepto.value.strip(),
                    id_empleado=self.empleado['id_empleado']
                )
                
                if resultado['success']:
                    self.mostrar_alerta("Éxito", "Movimiento registrado correctamente", VoltTheme.SUCCESS)
                    self.cerrar_modal()
                    self.actualizar_info_caja_actual()  # Recargar para ver el nuevo movimiento
                else:
                    self.mostrar_alerta("Error", resultado.get('message', 'Error al registrar'), VoltTheme.DANGER)
            except Exception as e:
                self.mostrar_alerta("Error", f"Error: {str(e)}", VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE, color=VoltTheme.INFO, size=30),
                    ft.Text("Registrar Movimiento", size=20, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                tipo_dropdown,
                campo_concepto,
                campo_monto,
                campo_obs,
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Guardar",
                        icon=ft.Icons.SAVE,
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: guardar_movimiento()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=450,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def ver_detalle_caja(self, id_caja):
        """Muestra el detalle de una caja cerrada"""
        try:
            resumen = self.caja_service.obtener_resumen_caja(id_caja)
            if not resumen:
                self.mostrar_alerta("Error", "No se encontró la caja", VoltTheme.DANGER)
                return
            
            # Formato fechas
            fecha_apertura = resumen['fecha_apertura']
            if isinstance(fecha_apertura, str):
                try:
                    fecha_apertura = datetime.fromisoformat(fecha_apertura.replace('Z', '+00:00'))
                except:
                    pass
            apertura_str = fecha_apertura.strftime("%d/%m/%Y %H:%M") if isinstance(fecha_apertura, datetime) else str(fecha_apertura)
            
            fecha_cierre = resumen.get('fecha_cierre')
            if isinstance(fecha_cierre, str):
                try:
                    fecha_cierre = datetime.fromisoformat(fecha_cierre.replace('Z', '+00:00'))
                except:
                    pass
            cierre_str = fecha_cierre.strftime("%d/%m/%Y %H:%M") if isinstance(fecha_cierre, datetime) else "No cerrada"
            
            diferencia = resumen.get('diferencia', 0) or 0
            if diferencia > 0:
                diff_color = VoltTheme.SUCCESS
                diff_icon = ft.Icons.ARROW_UPWARD
            elif diferencia < 0:
                diff_color = VoltTheme.DANGER
                diff_icon = ft.Icons.ARROW_DOWNWARD
            else:
                diff_color = VoltTheme.TEXT_SECONDARY
                diff_icon = ft.Icons.CHECK
            
            contenido = ft.Container(
                content=ft.Column([
                    ft.Text("Detalle de Caja", size=20, weight=ft.FontWeight.BOLD, color=VoltTheme.PRIMARY),
                    ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                    
                    ft.Column([
                        ft.Row([
                            ft.Text("Empleado:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(resumen.get('nombre_empleado', 'N/A'), size=14)
                        ]),
                        ft.Row([
                            ft.Text("Apertura:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(apertura_str, size=14)
                        ]),
                        ft.Row([
                            ft.Text("Cierre:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(cierre_str, size=14)
                        ]),
                    ], spacing=8),
                    
                    ft.Divider(height=1),
                    
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Monto Inicial:", size=14, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                ft.Text(f"Q {resumen['monto_inicial']:.2f}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                            ]),
                            ft.Row([
                                ft.Text("Ingresos:", size=14, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                ft.Text(f"Q {resumen.get('total_ingresos', 0):.2f}", size=14, color=VoltTheme.SUCCESS, weight=ft.FontWeight.BOLD)
                            ]),
                            ft.Row([
                                ft.Text("Egresos:", size=14, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                ft.Text(f"Q {resumen.get('total_egresos', 0):.2f}", size=14, color=VoltTheme.DANGER, weight=ft.FontWeight.BOLD)
                            ]),
                            ft.Row([
                                ft.Text("Monto Final:", size=14, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                ft.Text(f"Q {resumen.get('monto_final', 0):.2f}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                            ]),
                            ft.Divider(height=1, color=ft.Colors.WHITE24),
                            ft.Row([
                                ft.Icon(diff_icon, color=diff_color, size=20),
                                ft.Text("Diferencia:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Container(expand=True),
                                ft.Text(f"Q {diferencia:.2f}", size=16, weight=ft.FontWeight.BOLD, color=diff_color)
                            ]),
                        ], spacing=8),
                        bgcolor=VoltTheme.SECONDARY,
                        padding=15,
                        border_radius=5,
                        alignment=ft.alignment.center
                    ),
                    
                    ft.Row([
                        ft.ElevatedButton(
                            "Cerrar",
                            on_click=lambda _: self.cerrar_modal(),
                            bgcolor=VoltTheme.PRIMARY,
                            color=ft.Colors.WHITE
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=15, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                width=550
            )
            
            self.modal = ft.AlertDialog(modal=True, content=contenido)
            self.page.open(self.modal)
            
        except Exception as e:
            print(f"Error al ver detalle: {e}")
            self.mostrar_alerta("Error", f"No se pudo cargar el detalle: {str(e)}", VoltTheme.DANGER)
    
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
        elif tipo == VoltTheme.DANGER:
            icono = ft.Icons.ERROR
        elif tipo == VoltTheme.WARNING:
            icono = ft.Icons.WARNING
        else:
            icono = ft.Icons.INFO
        
        alerta = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(icono, color=tipo, size=30),
                ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Text(mensaje, size=14),
            actions=[
                ft.TextButton("Aceptar", on_click=lambda _: self.page.close(alerta))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.open(alerta)
