import tkinter as tk
from tkinter import ttk

class EstadisticaEstadoDisplay:
    """
    Descripción:
        Esta clase gestiona una ventana de interfaz gráfica (Tkinter) para mostrar
        estadísticas del inventario de animales, específicamente la cantidad y el porcentaje
        de animales en cada estado (Vivo, Enfermo, Traslado, Muerto en museo, Muerto).
    """

    def __init__(self, master, animales):
        """
        Descripción:
            Inicializa la ventana de visualización de estadísticas por estado.
        Entradas:
            master (tk.Tk or tk.Toplevel): La ventana padre de esta nueva ventana.
            animales (list): Una lista de objetos Animal de los cuales se extraerán las estadísticas.
        Salidas:
            None
        """
        self.master = master
        self.animales = animales

        self.root = tk.Toplevel(master)
        self.root.title("Estadísticas por Estado 📊")
        self.root.geometry("400x300")
        self.root.transient(master)
        self.root.grab_set() # Hace que esta ventana sea modal

        self._create_widgets() # Llama a la función para construir la interfaz
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """
        Descripción:
            Crea y organiza los widgets de la interfaz gráfica de la ventana de estadísticas.
            Esto incluye un título y un Treeview para mostrar los datos tabulados.
        Entradas:
            None
        Salidas:
            None
        """
        title_frame = tk.Frame(self.root, bd=2, relief="groove")
        title_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(title_frame, text="Estadísticas de Animales por Estado", font=("Arial", 12, "bold")).pack(pady=5)

        self.tree = ttk.Treeview(self.root, columns=("Estado", "Cant", "Porc"), show="headings")
        self.tree.heading("Estado", text="Estado")
        self.tree.heading("Cant", text="Cant")
        self.tree.heading("Porc", text="Porc (%)")

        self.tree.column("Estado", width=150, anchor="center")
        self.tree.column("Cant", width=80, anchor="center")
        self.tree.column("Porc", width=80, anchor="center")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        self._populate_table() # Llama a la función para llenar la tabla con datos

    def _calculate_state_counts(self):
        """
        Descripción:
            Calcula la cantidad de animales en cada estado y el total de animales.
        Entradas:
            None
        Salidas:
            tuple: Una tupla que contiene:
                   - estado_counts (dict): Un diccionario con el recuento de animales por cada estado.
                   - total_animals (int): El número total de animales en el inventario.
        """
        estado_counts = {
            "Vivo": 0,
            "Enfermo": 0,
            "Traslado": 0,
            "Muerto en museo": 0,
            "Muerto": 0
        }
        total_animals = len(self.animales)

        for animal in self.animales:
            estado_text = animal.get_estado_text() # Obtiene la descripción textual del estado
            
            # Asegurar que el estado textual se mapee correctamente a las claves del diccionario
            # Aunque animal.get_estado_text() ya hace esto, es una doble verificación o por si hay variaciones.
            if animal.estado == 2:
                estado_text = "Enfermo"
            elif animal.estado == 3:
                estado_text = "Traslado"
            elif animal.estado == 4:
                estado_text = "Muerto en museo"
            elif animal.estado == 5:
                estado_text = "Muerto"
            elif animal.estado == 1:
                estado_text = "Vivo"

            # Incrementar el contador para el estado correspondiente
            if estado_text in estado_counts:
                estado_counts[estado_text] += 1
            else:
                # Si hay un estado "Desconocido" u otro no mapeado, se añade dinámicamente
                estado_counts[estado_text] = estado_counts.get(estado_text, 0) + 1
        
        return estado_counts, total_animals

    def _populate_table(self):
        """
        Descripción:
            Llena la tabla (Treeview) con las estadísticas de animales por estado.
            Primero, borra cualquier contenido existente en la tabla. Luego, calcula
            las estadísticas y las inserta como nuevas filas.
        Entradas:
            None
        Salidas:
            None: Actualiza el contenido del `self.tree` Treeview.
        """
        # Limpiar cualquier contenido existente en la tabla
        for i in self.tree.get_children():
            self.tree.delete(i)

        estado_counts, total_animals = self._calculate_state_counts()

        # Insertar los datos en la tabla
        for estado, count in estado_counts.items():
            percentage = (count / total_animals * 100) if total_animals > 0 else 0
            self.tree.insert("", "end", values=(estado, count, f"{percentage:.2f}%"))

    def _on_close(self):
        """
        Descripción:
            Gestiona el cierre de la ventana de estadísticas. Libera el "grab" de la ventana
            (permitiendo la interacción con la ventana padre) y destruye la ventana.
        Entradas:
            None
        Salidas:
            None
        """
        self.root.grab_release()
        self.root.destroy()