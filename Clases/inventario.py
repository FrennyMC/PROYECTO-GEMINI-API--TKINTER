import pickle
import os
import random 
import re 
from Clases.animal import Animal # Asegúrate de que esta ruta sea correcta para tu clase Animal

class InventarioManager:
    """
    Descripción:
        Gestiona el inventario de animales del zoológico, incluyendo la carga, guardado,
        actualización y adición de animales, tanto en un archivo binario (pickle)
        para el inventario principal como en un archivo de texto plano para registro histórico/inicial.
    """

    def __init__(self, inventario_file, txt_animales_file):
        """
        Descripción:
            Inicializa el InventarioManager.
        Entradas:
            inventario_file (str): La ruta al archivo .pkl donde se guarda el inventario de objetos Animal.
            txt_animales_file (str): La ruta al archivo .txt que contiene la lista inicial/histórica de animales.
        Salidas:
            None
        """
        self.inventario_file = inventario_file
        self.txt_animales_file = txt_animales_file
        # No cargamos el inventario aquí directamente; get_all_animals lo hará cuando se necesite.
        self.inventario_animales = [] # Inicializa como lista vacía.
        self._max_txt_animal_id = self._get_max_txt_animal_id()

    def _get_max_txt_animal_id(self):
        """
        Descripción:
            Determina el número secuencial más alto en los IDs de animales guardados en el archivo TXT_ANIMALES.
            Esto se utiliza para asegurar que los nuevos IDs generados para el archivo TXT sean únicos y crecientes,
            siguiendo el formato 'xyNN' donde NN son dos dígitos.
        Entradas:
            None
        Salidas:
            int: El número secuencial más alto encontrado en los IDs del archivo de texto. Retorna 0 si no hay IDs.
        """
        max_num = 0
        if os.path.exists(self.txt_animales_file):
            try:
                with open(self.txt_animales_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split(', ')
                            if len(parts) > 0:
                                match = re.match(r'^[a-z]{2}(\d{2})$', parts[0])
                                if match:
                                    num = int(match.group(1))
                                    if num > max_num:
                                        max_num = num
            except Exception as e:
                print(f"Error al leer {self.txt_animales_file} para obtener el ID máximo: {e}")
        return max_num

    def _load_inventario_from_file(self):
        """
        Descripción:
            Carga el inventario de animales desde el archivo pickle.
            Si el archivo no existe o hay un error al cargarlo, retorna
            una lista vacía. Esta función ahora solo retorna la lista cargada,
            no la asigna a self.inventario_animales.
        Entradas:
            None
        Salidas:
            list: Una lista de objetos Animal.
        """
        if os.path.exists(self.inventario_file):
            try:
                with open(self.inventario_file, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error al cargar el inventario desde {self.inventario_file}: {e}")
                return []
        return []

    def save_inventario(self):
        """
        Descripción:
            Guarda el inventario actual de animales en el archivo pickle.
            Utiliza el atributo `self.inventario_animales`.
        Entradas:
            None
        Salidas:
            bool: True si el inventario se guardó exitosamente, False en caso contrario.
        """
        if self.inventario_animales: 
            try:
                with open(self.inventario_file, "wb") as f:
                    pickle.dump(self.inventario_animales, f)
                print("Inventario guardado exitosamente.")
                return True
            except Exception as e:
                print(f"Error al guardar el inventario en {self.inventario_file}: {e}")
                return False
        return False

    def get_all_animals(self):
        """
        Descripción:
            Retorna la lista completa de todos los objetos Animal en el inventario actual.
            **CAMBIO CLAVE:** Siempre recarga desde el archivo pickle para asegurar la frescura de los datos.
        Entradas:
            None
        Salidas:
            list: Una lista de objetos Animal.
        """
        # Carga el estado más reciente del archivo cada vez que se llama a get_all_animals
        self.inventario_animales = self._load_inventario_from_file()
        return list(self.inventario_animales) # Retorna una copia para evitar modificaciones directas

    def get_animal_by_id(self, animal_id):
        """
        Descripción:
            Busca y retorna un objeto Animal del inventario por su ID único.
        Entradas:
            animal_id (str): El ID del animal a buscar.
        Salidas:
            Animal or None: El objeto Animal si se encuentra, o None si no existe un animal con ese ID.
        """
        current_animals = self.get_all_animals() # Obtiene la lista más fresca
        for animal in current_animals:
            if animal.id == animal_id:
                return animal
        return None

    def update_animal(self, updated_animal):
        """
        Descripción:
            Actualiza un animal existente en el inventario con los datos de un objeto Animal modificado.
            El animal se identifica por su ID. Después de la actualización, el inventario se guarda.
            **Asegúrate de que self.inventario_animales esté actualizado antes de modificarlo.**
        Entradas:
            updated_animal (Animal): El objeto Animal con los datos actualizados.
        Salidas:
            bool: True si el animal fue encontrado y actualizado exitosamente, False en caso contrario.
        """
        # Aseguramos que estamos trabajando con la última lista antes de actualizar
        self.inventario_animales = self._load_inventario_from_file() 

        for i, animal in enumerate(self.inventario_animales):
            if animal.id == updated_animal.id:
                self.inventario_animales[i] = updated_animal
                self.save_inventario() # Guarda el self.inventario_animales actualizado
                return True
        return False

    def create_initial_inventory_from_txt(self, num_animals=20):
        """
        Descripción:
            Carga animales desde el archivo TXT_ANIMALES, crea objetos Animal a partir de ellos,
            y luego selecciona los primeros 'num_animals' de esa lista para formar el inventario
            inicial del zoológico, manteniendo el orden original.
            Finalmente, guarda este nuevo inventario en el archivo pickle.
        Entradas:
            num_animals (int, opcional): El número máximo de animales a seleccionar
                                        del archivo de texto para el inventario inicial.
                                        Por defecto es 20.
        Salidas:
            bool: True si el inventario inicial fue creado y guardado exitosamente, False en caso de error.
        """
        if not os.path.exists(self.txt_animales_file):
            print(f"Error: No se encuentra el archivo {self.txt_animales_file}")
            return False

        animales_cargados = self._load_animals_from_txt_file()

        if not animales_cargados:
            print("El archivo de nombres de animales está vacío o el formato es incorrecto.")
            return False

        # Seleccionar los primeros 'num_animals' animales, manteniendo el orden original
        self.inventario_animales = animales_cargados[:min(num_animals, len(animales_cargados))]
        print(f"Se seleccionaron {len(self.inventario_animales)} animales para el inventario, manteniendo el orden original del TXT.")
        return self.save_inventario()

    def _load_animals_from_txt_file(self):
        """
        Descripción:
            Función auxiliar para cargar y parsear animales desde el archivo TXT_ANIMALES.
        Entradas:
            None
        Salidas:
            list: Una lista de objetos Animal creados a partir de las líneas del archivo de texto.
        """
        animales_cargados = []
        try:
            with open(self.txt_animales_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(', ')
                    # Ajuste aquí si tu constructor de Animal espera los parámetros en un orden diferente
                    # Asegúrate de que el orden de los argumentos aquí coincida con tu constructor de Animal.
                    if len(parts) >= 4: # Esperamos al menos ID, nombre común, nombre científico, orden
                        animal_id = parts[0]
                        nombre_comun = parts[1]
                        nombre_cientifico = parts[2]
                        orden = parts[3]
                        estado = None
                        peso = None
                        wiki_image_url = ""
                        local_image_path = ""
                        calificacion = None # Asegurarse de que la calificación inicial sea None

                        # Parsear atributos opcionales
                        for part in parts[4:]:
                            if part.startswith("estado="):
                                try:
                                    estado = int(part.split("=")[1])
                                except ValueError:
                                    estado = None
                            elif part.startswith("peso="):
                                try:
                                    peso = float(part.split("=")[1])
                                except ValueError:
                                    peso = None
                            elif part.startswith("wiki_image_url="):
                                wiki_image_url = part.split("=")[1]
                            elif part.startswith("local_image_path="):
                                local_image_path = part.split("=")[1]

                        # Crea la instancia de Animal con los parámetros adecuados
                        # El orden aquí debe coincidir con el __init__ de tu clase Animal
                        animal = Animal(animal_id=animal_id, nombre_comun=nombre_comun, 
                                        nombre_cientifico=nombre_cientifico, estado=estado, 
                                        orden=orden, peso=peso, wiki_image_url=wiki_image_url, 
                                        local_image_path=local_image_path, calificacion=calificacion)
                        animales_cargados.append(animal)
        except Exception as e:
            print(f"Error al leer {self.txt_animales_file}: {e}")
            return []
        return animales_cargados

    def add_animal_to_txt(self, animal):
        """
        Descripción:
            Añade un nuevo animal al archivo TXT_ANIMALES. Antes de añadir, verifica si el animal
            (por nombre común) ya existe en el archivo. Si no existe, genera un nuevo ID secuencial
            para el animal, lo asigna al objeto y lo guarda en una nueva línea en el archivo de texto.
        Entradas:
            animal (Animal): El objeto Animal a añadir al archivo de texto.
        Salidas:
            bool: True si el animal fue añadido exitosamente, False si ya existía o hubo un error.
        """
        existing_common_names = self._get_existing_common_names_from_txt()

        # Si el animal ya existe por nombre común, no lo agregamos
        if animal.nombre_comun in existing_common_names:
            print(f"El animal '{animal.nombre_comun}' ya existe en {self.txt_animales_file}.")
            return False

        # Generar un nuevo ID secuencial y único para el archivo TXT
        self._max_txt_animal_id += 1
        nuevo_numero = f"{self._max_txt_animal_id:02d}"

        # Asegurarse de que el nombre común tenga al menos una letra inicial y final
        if len(animal.nombre_comun) >= 1:
            primera_letra = animal.nombre_comun[0].lower()
            ultima_letra = animal.nombre_comun[-1].lower()
        else:
            primera_letra = 'x' # Valor por defecto si el nombre es vacío
            ultima_letra = 'x'

        # Construir el nuevo ID con el patrón correcto
        nuevo_id_animal = f"{primera_letra}{ultima_letra}{nuevo_numero}"

        # Asignar este nuevo ID al objeto animal antes de guardarlo en el .txt
        animal.id = nuevo_id_animal

        # Preparar la línea para escribir en el archivo
        line_data = [
            animal.id, # El ID único y secuencial que acabamos de generar
            animal.nombre_comun,
            animal.nombre_cientifico,
            animal.orden,
            f"estado={animal.estado}",
            f"peso={animal.peso}",
            f"wiki_image_url={animal.wiki_image_url}",
            f"local_image_path={animal.local_image_path}"
        ]

        try:
            # Escribir el nuevo animal al final del archivo
            with open(self.txt_animales_file, "a", encoding="utf-8") as f:
                f.write(", ".join(line_data) + "\n")
            return True
        except Exception as e:
            print(f"Error al escribir en {self.txt_animales_file}: {e}")
            return False

    def _get_existing_common_names_from_txt(self):
        """
        Descripción:
            Función auxiliar para obtener un conjunto de nombres comunes ya existentes en el archivo TXT_ANIMALES.
            Esto ayuda a evitar la duplicación de animales por nombre común al añadir nuevos.
        Entradas:
            None
        Salidas:
            set: Un conjunto de cadenas de nombres comunes existentes en el archivo.
        """
        existing_common_names = set()
        if os.path.exists(self.txt_animales_file):
            try:
                with open(self.txt_animales_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split(', ')
                            if len(parts) > 1: # Asegurarse de que haya al menos ID y nombre común
                                existing_common_names.add(parts[1]) # Nombre común
            except Exception as e:
                print(f"Error al leer {self.txt_animales_file} para verificar nombres existentes: {e}")
        return existing_common_names