import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from io import BytesIO
import requests

# Importar la clase Animal si no está en el mismo archivo
# Si Animal está en 'Clases/animal.py', asegúrate de que esa ruta sea correcta
from Clases.animal import Animal 

# Rutas a las imágenes locales para los estados de los animales
AMBULANCE_IMG_PATH = "IMG/Ambulancia.png"
MUSEUM_IMG_PATH = "IMG/Museo.png"
SKULL_IMG_PATH = "IMG/skull.png"
DEFAULT_ANIMAL_IMG_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png"

HEADERS = {
    'User-Agent': 'ZooInventarioApp/1.0 (contact@example.com) requests'
}

class InventarioDisplay:
    def __init__(self, master, inventario_manager):
        self.master = master
        self.inventario_manager = inventario_manager
        
        # Aunque se inicializa aquí, display_current_page lo recargará siempre.
        self.animales = [] 
        self.current_page = 0
        self.animals_per_page = 4
        # total_pages se recalcula en display_current_page
        self.total_pages = 1 

        self.root = tk.Toplevel(master)
        self.root.title("Inventario de Animales 📊")
        self.root.geometry("800x700")
        self.root.transient(master)
        self.root.grab_set()

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.animal_frames = []
        # No necesitamos listas globales para los botones o labels de emoji,
        # los manejamos accediendo a los hijos de cada animal_frame.

        for i in range(self.animals_per_page):
            row_idx = i // 2
            col_idx = i % 2

            frame = tk.LabelFrame(self.main_frame, text=f"Animal {i+1}", padx=5, pady=5, relief="groove")
            frame.grid(row=row_idx, column=col_idx, padx=5, pady=5, sticky="nsew")
            self.animal_frames.append(frame)

            info_label = tk.Label(frame, text="", wraplength=150, justify=tk.LEFT)
            info_label.pack(pady=2)

            image_label = tk.Label(frame)
            image_label.pack(pady=5)

            rating_frame = tk.Frame(frame)
            rating_frame.pack(pady=5)

            emojis = ["⚪", "👍", "⭐", "😢", "😠"]
            
            # Etiqueta para mostrar la calificación seleccionada (específica de cada animal)
            selected_emoji_label = tk.Label(rating_frame, text="", font=("Arial", 10), fg="blue")
            selected_emoji_label.pack(side="right", padx=5)

            for j, emoji in enumerate(emojis):
                # Usar lambda con default arguments para capturar los valores correctos de i y j
                # 'idx' se refiere al índice de visualización del animal en la página
                btn = tk.Button(rating_frame, text=emoji, command=lambda idx=i, val=j+1: self.calificar_inventario_animal(idx, val))
                btn.pack(side="left", padx=2)
        
        self.nav_frame = tk.Frame(self.root)
        self.nav_frame.pack(pady=10)

        self.prev_btn = tk.Button(self.nav_frame, text="⬅️ Anterior", command=self.show_prev_page)
        self.prev_btn.pack(side="left", padx=10)

        self.page_label = tk.Label(self.nav_frame, text="")
        self.page_label.pack(side="left", padx=10)

        self.next_btn = tk.Button(self.nav_frame, text="Siguiente ➡️", command=self.show_next_page)
        self.next_btn.pack(side="left", padx=10)

        # Carga inicial de la página
        self.display_current_page()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_image_from_url(self, url, size=(100, 100)):
        if not url:
            url = DEFAULT_ANIMAL_IMG_URL
        try:
            response = requests.get(url, stream=True, timeout=5, headers=HEADERS)
            response.raise_for_status()
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img = img.resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            return photo
        except requests.exceptions.RequestException as e:
            print(f"Error cargando imagen desde {url}: {e}")
            try:
                response = requests.get(DEFAULT_ANIMAL_IMG_URL, stream=True, timeout=5, headers=HEADERS)
                response.raise_for_status()
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize(size, Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                return photo
            except Exception as e:
                print(f"Error al cargar la imagen por defecto: {e}")
                return None
        except Exception as e:
            print(f"Error inesperado al procesar imagen desde {url}: {e}")
            try:
                response = requests.get(DEFAULT_ANIMAL_IMG_URL, stream=True, timeout=5, headers=HEADERS)
                response.raise_for_status()
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize(size, Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                return photo
            except Exception as e:
                print(f"Error al cargar la imagen por defecto: {e}")
                return None

    def load_image_from_local(self, path, size=(100, 100)):
        try:
            img = Image.open(path)
            img = img.resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            return photo
        except FileNotFoundError:
            print(f"Error: Imagen local no encontrada en {path}")
            return None
        except Exception as e:
            print(f"Error al cargar imagen local desde {path}: {e}")
            return None

    def display_current_page(self):
        # Siempre recargar la lista completa de animales desde el manager.
        # Esto asegura que cualquier cambio persistido (como una calificación) esté presente.
        self.animales = self.inventario_manager.get_all_animals() 
        self.total_pages = (len(self.animales) + self.animals_per_page - 1) // self.animals_per_page if self.animales else 1

        start_index = self.current_page * self.animals_per_page
        end_index = min(start_index + self.animals_per_page, len(self.animales))

        for i in range(self.animals_per_page):
            frame = self.animal_frames[i]
            # Acceso a los widgets dentro del frame por su orden de creación
            info_label = frame.winfo_children()[0]
            image_label = frame.winfo_children()[1]
            rating_frame = frame.winfo_children()[2]
            
            # Obtener la etiqueta de emoji seleccionado y los botones de calificación
            selected_emoji_label = [child for child in rating_frame.winfo_children() if isinstance(child, tk.Label)][0]
            rating_buttons = [child for child in rating_frame.winfo_children() if isinstance(child, tk.Button)]

            if start_index + i < len(self.animales):
                animal = self.animales[start_index + i]
                frame.config(text=f"Animal {start_index + i + 1}")
                info_label.config(
                    text=f"Nombre: {animal.nombre_comun}\n"
                         f"Científico: {animal.nombre_cientifico}\n"
                         f"ID: {animal.id}\n"
                         f"Estado: {animal.get_estado_text()}\n"
                         f"Orden: {animal.orden}, Peso: {animal.peso} kg"
                )

                image_to_display = None
                if animal.local_image_path:
                    image_to_display = self.load_image_from_local(animal.local_image_path)
                elif animal.wiki_image_url:
                    image_to_display = self.load_image_from_url(animal.wiki_image_url)
                else:
                    image_to_display = self.load_image_from_url(DEFAULT_ANIMAL_IMG_URL)

                if image_to_display:
                    image_label.config(image=image_to_display)
                    # CRUCIAL: Mantiene una referencia fuerte a la imagen
                    image_label.image = image_to_display 
                else:
                    image_label.config(image="")
                    image_label.image = None

                # Determinar si el animal ya tiene una calificación definitiva (2, 3, 4, o 5)
                has_definitive_rating = (animal.calificacion is not None and animal.calificacion != 1)

                for j, btn in enumerate(rating_buttons):
                    if has_definitive_rating:
                        btn.config(state=tk.DISABLED)
                    else:
                        rating_value_for_btn = j + 1
                        if rating_value_for_btn == 1: # Botón "⚪" (Por omisión)
                            btn.config(state=tk.NORMAL) 
                        elif rating_value_for_btn in [2, 3]: # Me gusta, Favorito
                            btn.config(state=tk.NORMAL)
                        elif rating_value_for_btn == 4: # Me entristece (valide estado 2 o 5 únicamente)
                            btn.config(state=tk.NORMAL if animal.estado in [2, 5] else tk.DISABLED)
                        elif rating_value_for_btn == 5: # Me enoja (3 por sus implicaciones)
                            btn.config(state=tk.NORMAL if animal.estado == 3 else tk.DISABLED)
                
                # Actualizar la etiqueta de calificación con el valor actual del animal
                emojis_map = {1: "Por omisión ⚪", 2: "Me gusta 👍", 3: "Favorito ⭐", 4: "Me entristece 😢", 5: "Me enoja 😠"}
                if animal.calificacion is not None:
                    selected_emoji_label.config(text=f"Calificado: {emojis_map.get(animal.calificacion, 'Desconocido')}")
                else:
                    selected_emoji_label.config(text="No calificado")

                row_idx = i // 2
                col_idx = i % 2
                frame.grid(row=row_idx, column=col_idx, padx=5, pady=5, sticky="nsew")
            else:
                frame.grid_remove() # Ocultar frames no utilizados
                frame.config(text="")
                info_label.config(text="")
                image_label.config(image="")
                image_label.image = None
                # Asegúrate de deshabilitar los botones de calificación en los frames ocultos
                for btn in rating_buttons: # Acceder a los botones del frame actual
                    btn.config(state=tk.DISABLED)
                selected_emoji_label.config(text="")

        self.update_navigation_buttons()
        self.page_label.config(text=f"Página {self.current_page + 1} de {self.total_pages}")

    def are_all_animals_on_current_page_rated(self):
        # Esta función usa la lista `self.animales` que ya fue recargada por `display_current_page`.
        start_index = self.current_page * self.animals_per_page
        end_index = min(start_index + self.animals_per_page, len(self.animales))

        animals_to_check = self.animales[start_index:end_index]

        if not animals_to_check:
            return True

        for animal in animals_to_check:
            # Un animal se considera calificado si su calificación no es None
            if animal.calificacion is None: 
                return False
        
        return True

    def calificar_inventario_animal(self, animal_display_index, rating_value):
        actual_animal_index = self.current_page * self.animals_per_page + animal_display_index
        if actual_animal_index < len(self.animales):
            # Obtener el animal directamente de la lista actualizada de self.animales
            animal = self.animales[actual_animal_index]

            # Si el animal ya tiene una calificación DEFINITIVA (2-5), no permitir NINGÚN cambio.
            # La calificación "Por omisión" (1) sí se puede sobrescribir.
            if animal.calificacion is not None and animal.calificacion != 1:
                messagebox.showwarning(
                    "Ya Calificado",
                    f"'{animal.nombre_comun}' ya tiene una calificación definitiva y no se puede modificar.",
                    parent=self.root
                )
                return 

            can_qualify = False
            message = ""
            
            if rating_value == 1: # "Por omisión"
                can_qualify = True
            elif rating_value in [2, 3]: # Me gusta, Favorito
                can_qualify = True
            elif rating_value == 4: # Me entristece (valide estado 2 o 5 únicamente)
                if animal.estado in [2, 5]: # Estado 2: Enfermo, Estado 5: Muerto
                    can_qualify = True
                else:
                    message = f"'{animal.nombre_comun}' no puede ser calificado como 'Me entristece'. Solo si está 'enfermo' ({animal.get_estado_text()}) o 'muerto'."
            elif rating_value == 5: # Me enoja (3 por sus implicaciones)
                if animal.estado == 3: # Estado 3: Trasladado
                    can_qualify = True
                else:
                    message = f"'{animal.nombre_comun}' no puede ser calificado como 'Me enoja'. Solo si ha sido 'trasladado' ({animal.get_estado_text()})."
            
            if can_qualify:
                animal.calificar(rating_value)
                # El InventarioManager actualiza su copia interna del animal Y lo guarda en el archivo.
                self.inventario_manager.update_animal(animal) 
                
                emojis_map = {1: "Por omisión ⚪", 2: "Me gusta 👍", 3: "Favorito ⭐", 4: "Me entristece 😢", 5: "Me enoja 😠"}
                # Accedemos a la etiqueta del emoji seleccionado a través del frame actual
                frame = self.animal_frames[animal_display_index]
                rating_frame = frame.winfo_children()[2]
                selected_emoji_label = [child for child in rating_frame.winfo_children() if isinstance(child, tk.Label)][0]
                selected_emoji_label.config(text=f"Calificado: {emojis_map.get(rating_value, '')}")
                
                messagebox.showinfo("Calificación Exitosa", f"'{animal.nombre_comun}' ha sido calificado como '{emojis_map.get(rating_value, '')}'.", parent=self.root)

                # Volver a cargar y mostrar la página para reflejar todos los estados y deshabilitar botones.
                self.display_current_page() 
            else:
                if not message:
                    message = f"La calificación no es válida para '{animal.nombre_comun}' en su estado actual ({animal.get_estado_text()})."
                messagebox.showwarning("No Calificable", message, parent=self.root)

    def show_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()

    def show_next_page(self):
        # Habilitar el botón "Siguiente" solo si todos los animales de la página actual están calificados.
        if self.current_page < self.total_pages - 1:
            if self.are_all_animals_on_current_page_rated():
                self.current_page += 1
                self.display_current_page()
            else:
                messagebox.showwarning("Calificaciones Pendientes", "Por favor, califica todos los animales de la página actual antes de avanzar.", parent=self.root)
        else:
             messagebox.showinfo("Fin del Inventario", "Ya estás en la última página del inventario.", parent=self.root)


    def update_navigation_buttons(self):
        self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)

        # El botón "Siguiente" se habilita si no es la última página Y todos los animales de la página actual están calificados.
        if self.current_page < self.total_pages - 1 and self.are_all_animals_on_current_page_rated():
            self.next_btn.config(state=tk.NORMAL)
        else:
            self.next_btn.config(state=tk.DISABLED)

    def on_close(self):
        self.root.grab_release()
        self.root.destroy()