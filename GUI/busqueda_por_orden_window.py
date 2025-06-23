import tkinter as tk
from tkinter import messagebox, ttk
import os
import webbrowser

class BusquedaPorOrdenWindow:
    """
    Descripción:
        Esta clase gestiona la ventana de interfaz gráfica (Tkinter) para permitir a los usuarios
        buscar animales en el inventario por su orden alimenticio (Carnívoro, Herbívoro, Omnívoro).
        Una vez seleccionado un orden, genera un reporte HTML con los animales correspondientes
        y lo abre en el navegador web predeterminado.
    """

    def __init__(self, master, animales, html_generator, html_order_search_file):
        """
        Descripción:
            Inicializa la ventana de búsqueda por orden alimenticio.
        Entradas:
            master (tk.Tk or tk.Toplevel): La ventana padre de esta nueva ventana.
            animales (list): Una lista de objetos Animal que conforman el inventario.
            html_generator (object): Una instancia de una clase que puede generar archivos HTML de reportes.
            html_order_search_file (str): La ruta del archivo HTML donde se guardará el reporte.
        Salidas:
            None
        """
        self.master = master
        self.animales = animales
        self.html_generator = html_generator
        self.html_order_search_file = html_order_search_file
        self.selected_order = tk.StringVar(master)
        self.order_options = {
            "Carnívoro": "c",
            "Herbívoro": "h",
            "Omnívoro": "o"
        }
        self.selected_order.set("Carnívoro")

        self.root = tk.Toplevel(master)
        self.root.title("Búsqueda por Orden Alimenticio 🔍")
        self.root.geometry("350x200")
        self.root.transient(master)
        self.root.grab_set()  # Hace que esta ventana sea modal

        self._create_widgets() # Llama a la función para construir la interfaz
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """
        Descripción:
            Crea y organiza los widgets de la interfaz gráfica de la ventana de búsqueda.
        Entradas:
            None
        Salidas:
            None
        """
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        tk.Label(main_frame, text="Selecciona el orden:", font=("Arial", 12)).pack(pady=10)

        self.order_combobox = ttk.Combobox(
            main_frame,
            textvariable=self.selected_order,
            values=list(self.order_options.keys()),
            state="readonly"
        )
        self.order_combobox.pack(pady=5)
        self.order_combobox.set("Carnívoro")

        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Mostrar", command=self._mostrar_animales_por_orden_action,
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), relief=tk.RAISED).pack(side="left", padx=10)

        tk.Button(button_frame, text="Limpiar", command=self._limpiar_seleccion_action,
                  bg="#f44336", fg="white", font=("Arial", 10, "bold"), relief=tk.RAISED).pack(side="right", padx=10)

    def _mostrar_animales_por_orden_action(self):
        """
        Descripción:
            Esta función se ejecuta cuando el usuario hace clic en el botón "Mostrar".
            Filtra los animales según el orden seleccionado, genera un reporte HTML
            y lo abre en el navegador web. Muestra mensajes de éxito o error al usuario.
        Entradas:
            None
        Salidas:
            None: Muestra mensajes al usuario a través de `messagebox` y abre una URL en el navegador.
        """
        selected_display_name = self.selected_order.get()
        selected_code = self.order_options.get(selected_display_name)

        if not selected_code:
            messagebox.showwarning("Selección Inválida", "Por favor, selecciona un orden alimenticio válido.", parent=self.root)
            return

        if not self.animales:
            messagebox.showwarning("Inventario Vacío", "No hay animales en el inventario para buscar.", parent=self.root)
            return

        filtered_animals = self._filter_animals_by_order(selected_code)

        self._generate_and_open_report(filtered_animals, selected_display_name)

    def _filter_animals_by_order(self, order_code):
        """
        Descripción:
            Filtra la lista de animales para incluir solo aquellos que coinciden con el código de orden especificado.
        Entradas:
            order_code (str): El código de orden alimenticio a filtrar ('c', 'h', 'o').
        Salidas:
            list: Una lista de objetos Animal que pertenecen al orden especificado.
        """
        return [
            animal for animal in self.animales
            if hasattr(animal, 'orden') and animal.orden and animal.orden.lower() == order_code.lower()
        ]

    def _generate_and_open_report(self, animals_to_report, order_display_name):
        """
        Descripción:
            Genera el archivo HTML del reporte de animales y intenta abrirlo en el navegador web.
            Maneja los mensajes de éxito o error al usuario.
        Entradas:
            animals_to_report (list): La lista de objetos Animal a incluir en el reporte.
            order_display_name (str): El nombre de visualización del orden (ej. "Carnívoro").
        Salidas:
            None: Muestra mensajes al usuario y abre una URL en el navegador.
        """
        success = self.html_generator.generate_order_report_html(
            animals_to_report,
            order_display_name,
            self.html_order_search_file
        )

        if success:
            messagebox.showinfo("Reporte Generado", f"El reporte HTML para {order_display_name} se ha generado exitosamente en: {os.path.abspath(self.html_order_search_file)}", parent=self.root)
            try:
                webbrowser.open(os.path.abspath(self.html_order_search_file))
            except Exception as e:
                print(f"Error al abrir el archivo HTML: {e}")
                messagebox.showwarning("Advertencia", "No se pudo abrir el archivo HTML automáticamente. Por favor, ábrelo manualmente.", parent=self.root)
        else:
            messagebox.showerror("Error", f"No se pudo generar el reporte HTML para {order_display_name}.", parent=self.root)

    def _limpiar_seleccion_action(self):
        """
        Descripción:
            Restablece la selección del ComboBox al valor predeterminado ("Carnívoro").
            Muestra un mensaje informativo al usuario.
        Entradas:
            None
        Salidas:
            None: Muestra un mensaje al usuario a través de `messagebox`.
        """
        self.selected_order.set("Carnívoro")
        messagebox.showinfo("Limpiar", "Selección restablecida.", parent=self.root)

    def _on_close(self):
        """
        Descripción:
            Gestiona el cierre de la ventana de búsqueda. Libera el "grab" de la ventana
            (permitiendo la interacción con la ventana padre) y destruye la ventana.
        Entradas:
            None
        Salidas:
            None
        """
        self.root.grab_release()
        self.root.destroy()