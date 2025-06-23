import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import webbrowser
import re 
import requests # Importar requests para la descarga de imágenes

# Importar las clases de los módulos de generación de reportes
from Reportes.html_generator import HTMLReportGenerator
from Reportes.pdf_generator import PDFReportGenerator
from Reportes.csv_exporter import CSVExporter

# Asumiendo que animal.py, fetcher.py y inventario.py están en el mismo directorio
from Clases.animal import Animal
from Clases.fetcher import AnimalFetcher
from Clases.inventario import InventarioManager

# Importar las clases de la subcarpeta GUI
#from GUI.interfaz_animal import InterfazAnimal
from GUI.inventario_display import InventarioDisplay
from GUI.estadistica_estado_display import EstadisticaEstadoDisplay
from GUI.busqueda_por_orden_window import BusquedaPorOrdenWindow

INVENTARIO_FILE = "inventario.pkl"
TXT_ANIMALES = "lista_animales.txt"
HTML_OUTPUT_FILE = "inventario_resumen.html"
PDF_OUTPUT_FILE = "Estadistica_por_Calificacion.pdf"
CSV_OUTPUT_FILE = "inventario_completo.csv"
HTML_ORDER_SEARCH_FILE = "reporte_orden_alimenticio.html"

# --- Rutas a las imágenes locales para los estados de los animales ---
AMBULANCE_IMG_PATH = "IMG/Ambulancia.png"
MUSEUM_IMG_PATH = "IMG/Museo.png"
SKULL_IMG_PATH = "IMG/skull.png"
DEFAULT_ANIMAL_IMG_PATH = "IMG/default_animal.png" # Ruta a tu imagen de placeholder local

class ZooInventarioApp:
    def __init__(self, root, api_key=None):
        self.root = root
        self.root.title("ZooInventario")
        self.root.geometry("250x350")
        self.root.resizable(False, False)
        self.api_key = api_key
        # Initialize InventarioManager
        self.inventario_manager = InventarioManager(INVENTARIO_FILE, TXT_ANIMALES)

        self.buttons = []
        self.create_widgets()
        self.check_db_status()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """
        Descripción: Crea y organiza los widgets principales de la interfaz de usuario.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        header_frame = tk.Frame(self.root, bd=2, relief="groove")
        header_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(header_frame, text="✨", font=("Arial", 20)).pack(side="left", padx=5)
        tk.Label(header_frame, text="ZooInventario", font=("Arial", 14, "bold")).pack(side="left", padx=5)
        tk.Label(header_frame, text="🌐", font=("Arial", 20)).pack(side="right", padx=5)

        button_texts = [
            "1. Obtener lista",
            "2. Crear inventario",
            "3. Mostrar inventario",
            "4. Estadística * estado",
            "5. Crear HTML",
            "6. Generar PDF",
            "7. Generar .csv",
            "8. Búsqueda por orden"
        ]

        button_commands = [
            self.obtener_lista,
            self.crear_inventario,
            self.mostrar_inventario,
            self.estadistica_estado,
            self.crear_html,
            self.generar_pdf,
            self.generar_csv,
            self.busqueda_por_orden
        ]

        for i, text in enumerate(button_texts):
            btn = tk.Button(self.root, text=text, command=button_commands[i], anchor="w", width=25)
            btn.pack(pady=2, padx=10)
            self.buttons.append(btn)

    def set_button_states(self, enabled_indices, disabled_indices):
        """
        Descripción: Establece el estado (habilitado/deshabilitado) de los botones de la interfaz.
        Entradas:
            enabled_indices (list): Una lista de índices de botones a habilitar (basado en 1).
            disabled_indices (list): Una lista de índices de botones a deshabilitar (basado en 1).
        Salidas: Ninguna.
        """
        for i, btn in enumerate(self.buttons):
            if (i + 1) in enabled_indices:
                btn.config(state=tk.NORMAL)
            elif (i + 1) in disabled_indices:
                btn.config(state=tk.DISABLED)

    def check_db_status(self):
        """
        Descripción: Verifica la existencia y el tamaño de los archivos de la base de datos
                     (lista de nombres y archivo de inventario) y ajusta el estado de los botones
                     de la interfaz de usuario en consecuencia. Muestra mensajes informativos al usuario.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        names_file_exists = os.path.exists(TXT_ANIMALES) and os.path.getsize(TXT_ANIMALES) > 0
        inventory_file_exists = os.path.exists(INVENTARIO_FILE) and os.path.getsize(INVENTARIO_FILE) > 0

        if not names_file_exists:
            self.set_button_states([1], [2, 3, 4, 5, 6, 7, 8])
            messagebox.showinfo("Estado", "No se encontró el archivo de nombres de animales. Solo 'Obtener lista' habilitado.", parent=self.root)
        elif not inventory_file_exists:
            self.set_button_states([1, 2], [3, 4, 5, 6, 7, 8])
            messagebox.showinfo("Estado", "Archivo de nombres encontrado, pero inventario no creado. 'Obtener lista' y 'Crear inventario' habilitados.", parent=self.root)
        else:
            self.set_button_states([1, 2, 3, 4, 5, 6, 7, 8], [])
            messagebox.showinfo("Estado", "Archivo de nombres e inventario encontrados. Funcionalidades habilitadas.", parent=self.root)

    def _get_animal_quantity(self):
        """
        Descripción: Solicita al usuario la cantidad de animales a obtener mediante un cuadro de diálogo.
        Entradas: Ninguna.
        Salidas:
            int: La cantidad de animales ingresada por el usuario, o None si el usuario cancela.
        """
        return simpledialog.askinteger("Cantidad de animales", "¿Cuántos animales deseas obtener?", parent=self.root, minvalue=1, maxvalue=100)

    def _fetch_and_process_animals(self, quantity):
        """
        Descripción: Obtiene animales de la API, les asigna imágenes locales si es necesario
                     según su estado, y los agrega al archivo de texto de nombres de animales.
        Entradas:
            quantity (int): La cantidad de animales a obtener.
        Salidas:
            list: Una lista de objetos Animal que fueron agregados exitosamente al archivo de nombres.
        """
        fetcher = AnimalFetcher(api_key=self.api_key)
        Animal.reset_id_counter()
        animales_obtenidos = fetcher.obtener_animales(quantity)

        if not animales_obtenidos:
            messagebox.showerror("Error", "No se pudo obtener la lista de animales. Verifica tu API Key y conexión.", parent=self.root)
            return []

        animals_to_qualify = []
        for animal in animales_obtenidos:
            self._assign_animal_image_paths(animal)
            if self.inventario_manager.add_animal_to_txt(animal):
                animals_to_qualify.append(animal)
        return animals_to_qualify

    def _assign_animal_image_paths(self, animal):
        """
        Descripción: Asigna rutas de imágenes locales a un objeto Animal basándose en su estado y si tiene una URL de Wikipedia.
        Entradas:
            animal (Animal): El objeto Animal al que se le asignarán las rutas de imagen.
        Salidas: Ninguna. Modifica el objeto 'animal' directamente.
        """
        if not animal.wiki_image_url:
            animal.local_image_path = DEFAULT_ANIMAL_IMG_PATH
        
        if animal.estado == 2: # Enfermo
            animal.local_image_path = AMBULANCE_IMG_PATH
            animal.wiki_image_url = "" 
        elif animal.estado == 3: # Muerto en museo
            animal.local_image_path = MUSEUM_IMG_PATH
            animal.wiki_image_url = ""
        elif animal.estado == 4 or animal.estado == 5: # Muerto o Muerto en exhibicion
            animal.local_image_path = SKULL_IMG_PATH
            animal.wiki_image_url = ""

    def obtener_lista(self):
        """
        Descripción: Inicia el proceso de obtener una lista de animales de una API, les asigna imágenes
                     locales según su estado y los guarda en el archivo de nombres.
                     Luego actualiza el estado de los botones.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        quantity = self._get_animal_quantity()
        if quantity is None:
            return

        animals_added = self._fetch_and_process_animals(quantity)
        
        if animals_added:
            messagebox.showinfo("Información", f"Se han agregado {len(animals_added)} nuevos animales al archivo de nombres.", parent=self.root)
        else:
            messagebox.showinfo("Información", "No se agregaron nuevos animales al archivo de nombres (posiblemente ya existen).", parent=self.root)
        self.check_db_status() 

    def _create_and_load_inventory(self):
        """
        Descripción: Intenta crear el inventario inicial a partir del archivo de texto de nombres de animales.
        Entradas: Ninguna.
        Salidas:
            bool: True si el inventario se creó exitosamente, False en caso contrario.
        """
        return self.inventario_manager.create_initial_inventory_from_txt()

    def crear_inventario(self):
        """
        Descripción: Maneja la creación del inventario de animales. Muestra un mensaje de éxito o error
                     y actualiza el estado de los botones.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        success = self._create_and_load_inventory()
        if success:
            messagebox.showinfo("Inventario creado", f"Se ha creado un inventario con {len(self.inventario_manager.get_all_animals())} animales.", parent=self.root)
            print("Inventario de animales creado:")
            for animal in self.inventario_manager.get_all_animals():
                print(f"   - ID: {animal.id}, Nombre: {animal.nombre_comun} (Orden: {animal.orden}, Peso: {animal.peso} kg, Estado: {animal.get_estado_text()})")
        else:
            messagebox.showerror("Error", "No se pudo crear el inventario. Revisa los mensajes en la consola.", parent=self.root)
        self.check_db_status() 

    def _display_inventory_check(self):
        """
        Descripción: Verifica si el inventario está cargado antes de intentar mostrarlo.
        Entradas: Ninguna.
        Salidas:
            bool: True si el inventario existe y no está vacío, False en caso contrario.
        """
        if not self.inventario_manager.get_all_animals():
            messagebox.showerror("Error", "No se ha creado o cargado el inventario. Por favor, crea uno primero.", parent=self.root)
            return False
        return True

    def mostrar_inventario(self):
        """
        Descripción: Muestra la interfaz gráfica del inventario de animales si este ha sido creado.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        if not self._display_inventory_check():
            return
        InventarioDisplay(self.root, self.inventario_manager)

    def estadistica_estado(self):
        """
        Descripción: Muestra la interfaz gráfica de estadísticas por estado de los animales.
                     Requiere que el inventario esté cargado.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        animals = self.inventario_manager.get_all_animals()
        if not animals:
            messagebox.showerror("Error", "No se ha creado o cargado el inventario. Por favor, crea uno primero.", parent=self.root)
            return
        EstadisticaEstadoDisplay(self.root, animals)

    def _get_sorted_animals_for_html(self):
        """
        Descripción: Obtiene todos los animales del inventario, filtra aquellos con peso definido,
                     y los ordena por peso de forma descendente, seleccionando los 20 primeros.
        Entradas: Ninguna.
        Salidas:
            list: Una lista de los 20 animales más pesados del inventario.
        """
        all_animals = self.inventario_manager.get_all_animals()
        if not all_animals:
            return []
        animals_with_weight = [animal for animal in all_animals if animal.peso is not None]
        sorted_animals = sorted(animals_with_weight, key=lambda a: float(a.peso), reverse=True)
        return sorted_animals[:20]

    def _generate_and_open_html_report(self, selected_animals):
        """
        Descripción: Genera un reporte HTML con los animales seleccionados y lo intenta abrir en el navegador.
        Entradas:
            selected_animals (list): La lista de objetos Animal a incluir en el reporte HTML.
        Salidas:
            bool: True si el reporte se generó y se intentó abrir exitosamente, False en caso contrario.
        """
        html_generator = HTMLReportGenerator()
        success = html_generator.generate_html_report(selected_animals, HTML_OUTPUT_FILE)

        if success:
            messagebox.showinfo("HTML Generado", f"Archivo HTML generado exitosamente: {HTML_OUTPUT_FILE}", parent=self.root)
            try:
                webbrowser.open(os.path.abspath(HTML_OUTPUT_FILE))
            except Exception as web_e:
                print(f"Error al intentar abrir el navegador web: {web_e}")
                messagebox.showwarning("Advertencia", "No se pudo abrir el archivo HTML automáticamente en el navegador. Por favor, ábrelo manualmente.", parent=self.root)
        else:
            messagebox.showerror("Error al Generar HTML", "No se pudo generar el archivo HTML.", parent=self.root)
        return success

    def crear_html(self):
        """
        Descripción: Genera un reporte HTML de los 20 animales más pesados del inventario.
                     Muestra mensajes de éxito o error y abre el archivo HTML si es posible.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        selected_animals = self._get_sorted_animals_for_html()
        if not selected_animals:
            messagebox.showwarning("Advertencia", "El inventario está vacío o no contiene animales con peso. No se puede generar el HTML.", parent=self.root)
            return

        self._generate_and_open_html_report(selected_animals)

    def _generate_and_open_pdf_report(self, animals):
        """
        Descripción: Genera un reporte PDF de estadísticas por calificación de los animales y lo intenta abrir.
        Entradas:
            animals (list): La lista de objetos Animal a incluir en el reporte PDF.
        Salidas:
            bool: True si el PDF se generó y se intentó abrir exitosamente, False en caso contrario.
        """
        pdf_generator = PDFReportGenerator()
        success = pdf_generator.generate_rating_statistics_pdf(animals, PDF_OUTPUT_FILE)

        if success:
            messagebox.showinfo("PDF Generado", f"El reporte PDF 'Estadística por Calificación' se ha generado exitosamente en: {os.path.abspath(PDF_OUTPUT_FILE)}", parent=self.root)
            try:
                webbrowser.open(os.path.abspath(PDF_OUTPUT_FILE))
            except Exception as web_e:
                print(f"Error al intentar abrir el PDF en el navegador/visor: {web_e}")
                messagebox.showwarning("Advertencia", "No se pudo abrir el PDF automáticamente. Por favor, ábrelo manualmente.", parent=self.root)
        else:
            messagebox.showerror("Error al Generar PDF", "Hubo un error al generar el reporte PDF.", parent=self.root)
        return success

    def generar_pdf(self):
        """
        Descripción: Genera un reporte PDF con estadísticas de animales por calificación.
                     Requiere que el inventario esté cargado.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        animals = self.inventario_manager.get_all_animals()
        if not animals:
            messagebox.showwarning("Advertencia", "El inventario está vacío. No se puede generar el PDF.", parent=self.root)
            return
        self._generate_and_open_pdf_report(animals)

    def _export_animals_to_csv(self, animals):
        """
        Descripción: Exporta la lista de animales a un archivo CSV.
        Entradas:
            animals (list): La lista de objetos Animal a exportar.
        Salidas:
            bool: True si el archivo CSV se generó exitosamente, False en caso contrario.
        """
        csv_exporter = CSVExporter()
        return csv_exporter.export_animals_to_csv(animals, CSV_OUTPUT_FILE)

    def generar_csv(self):
        """
        Descripción: Genera un archivo CSV con el inventario completo de animales.
                     Requiere que el inventario esté cargado.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        animals = self.inventario_manager.get_all_animals()
        if not animals:
            messagebox.showwarning("Advertencia", "El inventario está vacío. No se puede generar el CSV.", parent=self.root)
            return

        success = self._export_animals_to_csv(animals)
        if success:
            messagebox.showinfo("CSV Generado", f"El archivo CSV 'inventario_completo.csv' se ha generado exitosamente en: {os.path.abspath(CSV_OUTPUT_FILE)}", parent=self.root)
        else:
            messagebox.showerror("Error al Generar CSV", "Hubo un error al generar el archivo CSV.", parent=self.root)

    def busqueda_por_orden(self):
        """
        Descripción: Abre una nueva ventana para realizar una búsqueda de animales por orden alimenticio
                     y generar un reporte HTML.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        animals = self.inventario_manager.get_all_animals()
        if not animals:
            messagebox.showwarning("Advertencia", "El inventario está vacío. No se puede realizar la búsqueda.", parent=self.root)
            return

        html_generator = HTMLReportGenerator()
        BusquedaPorOrdenWindow(self.root, animals, html_generator, HTML_ORDER_SEARCH_FILE)

    def on_closing(self):
        """
        Descripción: Guarda el inventario actual cuando la aplicación se cierra y luego destruye la ventana principal.
        Entradas: Ninguna.
        Salidas: Ninguna.
        """
        self.inventario_manager.save_inventario()
        self.root.destroy()