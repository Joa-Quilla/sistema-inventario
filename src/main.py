"""
Sistema de Inventario
Punto de entrada principal de la aplicación
"""
import flet as ft
import os
from database import DatabaseConnection
from services import AuthService
from views import LoginView, DashboardView


class SistemaInventarioApp:
    """Clase principal de la aplicación"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Sistema de Inventario"
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_min_width = 800
        self.page.window_min_height = 600
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        
        # Configurar ícono de la ventana
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.page.window_icon = icon_path
        
        # Inicializar servicios
        try:
            self.db = DatabaseConnection()
            if not self.db.test_connection():
                self.mostrar_error_conexion()
                return
            
            self.auth_service = AuthService(self.db)
            
            # Mostrar login
            self.mostrar_login()
            
        except Exception as e:
            print(f"❌ Error iniciando aplicación: {e}")
            self.mostrar_error_conexion()

    def mostrar_login(self):
        """Muestra la pantalla de login"""
        self.page.clean()
        login_view = LoginView(
            auth_service=self.auth_service,
            on_login_success=self.on_login_exitoso
        )
        
        # Crear funciones lambda que pasen page
        def on_submit_usuario(e):
            login_view.txt_password.focus()
        
        def on_submit_password(e):
            login_view.iniciar_sesion(e, self.page)
        
        def on_click_login(e):
            login_view.iniciar_sesion(e, self.page)
        
        # Construir la vista
        login_container = login_view.build()
        
        # Asignar los callbacks con page
        login_view.txt_usuario.on_submit = on_submit_usuario
        login_view.txt_password.on_submit = on_submit_password
        login_view.btn_login.on_click = on_click_login
        
        self.page.add(login_container)
        self.page.update()

    def on_login_exitoso(self, empleado):
        """Callback cuando el login es exitoso"""
        print(f"✅ Login exitoso: {empleado['nombre']} {empleado['apellido']}")
        print(f"Rol: {empleado['nombre_rol']}")
        
        # TODO: Mostrar menú principal
        self.mostrar_dashboard(empleado)

    def mostrar_dashboard(self, empleado):
        """Muestra el dashboard principal"""
        self.page.clean()
        
        dashboard = DashboardView(
            page=self.page,
            auth_service=self.auth_service,
            empleado=empleado,
            on_logout=self.cerrar_sesion
        )
        
        dashboard_container = dashboard.build()
        
        self.page.add(dashboard_container)
        self.page.update()

    def cerrar_sesion(self):
        """Cierra la sesión actual"""
        self.auth_service.logout()
        self.mostrar_login()

    def mostrar_error_conexion(self):
        """Muestra un error de conexión a la BD"""
        self.page.clean()
        
        error_view = ft.Container(
            content=ft.Column([
                ft.Icon(
                    "error_outline",
                    size=100,
                    color=ft.Colors.RED_700
                ),
                ft.Text(
                    "Error de Conexión",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_700
                ),
                ft.Text(
                    "No se pudo conectar a la base de datos",
                    size=18,
                    color=ft.Colors.GREY_700
                ),
                ft.Container(height=20),
                ft.Text(
                    "Verifique:",
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Column([
                    ft.Text("• PostgreSQL está ejecutándose"),
                    ft.Text("• Las credenciales en .env son correctas"),
                    ft.Text("• La base de datos 'sistema_inventario' existe"),
                ],
                spacing=5
                ),
                ft.Container(height=30),
                ft.ElevatedButton(
                    "Reintentar",
                    icon="refresh",
                    on_click=lambda _: self.__init__(self.page)
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        
        self.page.add(error_view)
        self.page.update()


def main(page: ft.Page):
    """Función principal"""
    SistemaInventarioApp(page)


if __name__ == "__main__":
    ft.app(target=main)
