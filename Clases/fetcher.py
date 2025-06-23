import google.generativeai as genai
import random
import re
import requests 
from Clases.animal import Animal

class AnimalFetcher:
    """
    Descripción:
        Clase encargada de obtener información de animales utilizando la API de Google Gemini
        para generar datos y la API de Wikipedia para obtener URLs de imágenes.
        Luego, crea objetos Animal con la información obtenida.
    """

    def __init__(self, api_key):
        """
        Descripción:
            Inicializa la clase AnimalFetcher con la clave de API de Gemini.
        Entradas:
            api_key (str): La clave de API para autenticarse con Google Gemini.
        Salidas:
            None
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemma-3n-e4b-it") 
        self.animales = []

    def _get_wikipedia_image_url(self, common_name):
        """
        Descripción:
            Intenta obtener una URL de imagen principal de Wikipedia para un animal dado su nombre común.
            Prioriza la búsqueda en Wikipedia en español y utiliza una heurística robusta para seleccionar
            la página más relevante si la búsqueda directa es ambigua. Incluye un mecanismo de
            búsqueda aumentada con sufijos como "(animal)" si la búsqueda inicial falla o es ambigua.
        Entradas:
            common_name (str): El nombre común del animal.
        Salidas:
            str: La URL de la imagen principal del animal en Wikipedia, o una cadena vacía si no se encuentra.
        """
        S = requests.Session()
        WIKI_URL = "https://es.wikipedia.org/w/api.php" # API de Wikipedia en español

        # Palabras clave de exclusión que indican que la página NO es sobre el animal
        EXCLUSION_KEYWORDS = [
            ' (desambiguación)', ' (ciudad)', ' (bandera)', ' (apellido)', ' (nombre)', 
            ' (película)', ' (libro)', ' (serie de televisión)', ' (canción)', 
            ' (personaje)', ' (ficción)', ' (historia)', ' (mitología)', ' (género musical)', 
            ' (club de fútbol)', ' (equipo)', ' (pueblo)', ' (municipio)', 
            ' (departamento)', ' (provincia)', ' (estado)', ' (río)', ' (montaña)', 
            ' (geografía)', ' (distrito)', ' (comuna)', ' (isla)', ' (península)', 
            ' (estrecho)', ' (edificio)', ' (obra de arte)', ' (planta)', ' (árbol)', 
            ' (vegetal)', ' (mineral)', ' (instrumento musical)', ' (tecnología)', 
            ' (organización)', ' (empresa)', ' (marca)', ' (evento)', ' (festividad)',
            ' de ', # Si es "Libros del Zorro Rojo", "de" es una buena señal de que no es el animal.
            ' en ', # Similar a "de"
            ' y '  # Similar a "de"
        ]
        
        selected_page_title = None

        try:
            params_search = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": common_name,
                "srlimit": 5, # Intentamos hasta 5 resultados
                "srprop": "snippet"
            }
            
            response_search = S.get(url=WIKI_URL, params=params_search)
            response_search.raise_for_status() 
            data_search = response_search.json()
            
            if 'query' not in data_search:
                # print(f"Error: La respuesta de búsqueda de Wikipedia para '{common_name}' no contiene 'query'. Respuesta completa: {data_search}")
                return ""

            if not data_search["query"]["search"]:
                # print(f"No se encontró página de Wikipedia para: {common_name}")
                # Si no se encontró nada, intentar con "(animal)" directamente
                return self._get_wikipedia_image_url_augmented(common_name, S, WIKI_URL, EXCLUSION_KEYWORDS)
            
            # --- Heurística de selección de página ---
            # Priorizamos coincidencias exactas y eliminamos resultados irrelevantes.
            
            potential_titles = []
            for result in data_search["query"]["search"]:
                title = result["title"]
                # Descartar títulos que contengan palabras clave de exclusión
                if any(kw in title.lower() for kw in EXCLUSION_KEYWORDS):
                    # print(f"DEBUG: Descartando '{title}' por palabra clave de exclusión.")
                    continue
                potential_titles.append(title)
            
            # Si después de filtrar no quedan títulos, intentamos la búsqueda aumentada
            if not potential_titles:
                # print(f"DEBUG: No se encontraron títulos relevantes después del primer filtro para '{common_name}'. Intentando búsqueda aumentada.")
                return self._get_wikipedia_image_url_augmented(common_name, S, WIKI_URL, EXCLUSION_KEYWORDS)
            
            # Ordenar los títulos potenciales: primero coincidencia exacta, luego los más cortos
            potential_titles.sort(key=lambda t: (t.lower() != common_name.lower(), len(t)))

            selected_page_title = potential_titles[0] # Tomamos el mejor resultado después de filtrar y ordenar

            if len(common_name.split()) < 2 or "feroz" in selected_page_title.lower(): # Específico para "Lobo feroz"
                    # print(f"DEBUG: Título seleccionado '{selected_page_title}' es corto o sospechoso para '{common_name}'. Intentando búsqueda aumentada.")
                    augmented_url = self._get_wikipedia_image_url_augmented(common_name, S, WIKI_URL, EXCLUSION_KEYWORDS)
                    if augmented_url: # Si la búsqueda aumentada tuvo éxito, la usamos
                        # print(f"DEBUG: Búsqueda aumentada exitosa para '{common_name}'.")
                        return augmented_url


            # print(f"Página de Wikipedia seleccionada para '{common_name}': {selected_page_title}") 
            
            # Paso 2: Obtener la URL de la imagen principal (thumbnail) de la página seleccionada
            params_image = {
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "titles": selected_page_title, 
                "piprop": "thumbnail|original", 
                "pithumbsize": 500,    
                "redirects": 1         
            }

            response_image = S.get(url=WIKI_URL, params=params_image)
            response_image.raise_for_status()
            data_image = response_image.json()

            if 'query' not in data_image:
                # print(f"Error: La respuesta de imagen de Wikipedia para '{common_name}' no contiene 'query'. Respuesta completa: {data_image}")
                return ""

            page_id = list(data_image["query"]["pages"].keys())[0]

            if page_id != "-1":
                page_data = data_image["query"]["pages"][page_id]
                # Preferir la URL 'original' si existe, si no, usar 'thumbnail'
                if "original" in page_data:
                    img_url = page_data["original"]["source"]
                    # print(f"URL de imagen original obtenida para '{common_name}': {img_url}") 
                    return img_url
                elif "thumbnail" in page_data:
                    img_url = page_data["thumbnail"]["source"]
                    # print(f"URL de imagen thumbnail obtenida para '{common_name}': {img_url}") 
                    return img_url
                else:
                    # print(f"No se encontró imagen principal (original o thumbnail) para {common_name} en la página '{selected_page_title}'.")
                    return ""
            else:
                # print(f"No se encontró imagen principal para {common_name} en la página '{selected_page_title}' (page_id -1).")
                return ""

        except requests.exceptions.RequestException as e:
            # print(f"Error de red o HTTP al buscar imagen de Wikipedia para {common_name}: {e}")
            return ""
        except Exception as e:
            # print(f"Error inesperado al procesar la respuesta de Wikipedia para {common_name}: {e}")
            return ""

    def _get_wikipedia_image_url_augmented(self, common_name, session, wiki_url, exclusion_keywords):
        """
        Descripción:
            Función auxiliar para intentar la búsqueda de imágenes en Wikipedia con sufijos comunes
            como "(animal)", "(especie)", etc., cuando la búsqueda directa falla o es ambigua.
        Entradas:
            common_name (str): El nombre común del animal.
            session (requests.Session): La sesión de requests para realizar las solicitudes HTTP.
            wiki_url (str): La URL base de la API de Wikipedia.
            exclusion_keywords (list): Lista de palabras clave a excluir en los títulos de Wikipedia.
        Salidas:
            str: La URL de la imagen principal del animal en Wikipedia, o una cadena vacía si no se encuentra.
        """
        for suffix in [" (animal)", " (especie)", " (mamífero)", " (ave)", " (reptil)", " (pez)"]:
            augmented_name = common_name + suffix
            params_augmented_search = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": augmented_name,
                "srlimit": 1,
                "srprop": "snippet"
            }
            try:
                response_augmented_search = session.get(url=wiki_url, params=params_augmented_search)
                response_augmented_search.raise_for_status()
                data_augmented_search = response_augmented_search.json()
                
                if data_augmented_search["query"]["search"]:
                    potential_title = data_augmented_search["query"]["search"][0]["title"]
                    # Verificar que el título devuelto sea sobre el animal y no una exclusión
                    if common_name.lower() in potential_title.lower() and not any(kw in potential_title.lower() for kw in exclusion_keywords):
                        # print(f"DEBUG: Búsqueda aumentada '{augmented_name}' encontró '{potential_title}'.")
                        # Ahora, obtener la imagen de esta página
                        params_image = {
                            "action": "query",
                            "format": "json",
                            "prop": "pageimages",
                            "titles": potential_title,
                            "piprop": "thumbnail|original",
                            "pithumbsize": 500,
                            "redirects": 1
                        }
                        response_image = session.get(url=wiki_url, params=params_image)
                        response_image.raise_for_status()
                        data_image = response_image.json()

                        page_id = list(data_image["query"]["pages"].keys())[0]
                        if page_id != "-1":
                            page_data = data_image["query"]["pages"][page_id]
                            if "original" in page_data:
                                img_url = page_data["original"]["source"]
                                # print(f"URL de imagen original (aumentada) obtenida para '{common_name}': {img_url}") 
                                return img_url
                            elif "thumbnail" in page_data:
                                img_url = page_data["thumbnail"]["source"]
                                # print(f"URL de imagen thumbnail (aumentada) obtenida para '{common_name}': {img_url}") 
                                return img_url
            except requests.exceptions.RequestException as e:
                # print(f"DEBUG: Error de red/HTTP en búsqueda aumentada para '{augmented_name}': {e}")
                pass # Silenciar errores de búsqueda aumentada
            except Exception as e:
                # print(f"DEBUG: Error inesperado en búsqueda aumentada para '{augmented_name}': {e}")
                pass # Silenciar errores inesperados
        # print(f"DEBUG: Búsqueda aumentada no encontró una URL válida para '{common_name}'.")
        return "" # Si no se encontró nada con los sufijos

    def _parse_animal_data(self, line):
        """
        Descripción:
            Parsea una línea de texto generada por la API de Gemini para extraer
            el nombre común, nombre científico y el orden alimenticio del animal.
            También realiza una limpieza del nombre común.
        Entradas:
            line (str): Una línea de texto en el formato "Nombre Común - Nombre Científico - tipo_alimentacion".
        Salidas:
            tuple: Una tupla que contiene (nombre_comun_limpio, nombre_cientifico, orden_clasificado).
                   Retorna (None, None, None) si la línea no se puede parsear.
        """
        line = line.strip() 
        if not line: 
            return None, None, None

        match = re.match(r'^(.*?)\s*[-–]\s*(.*?)\s*[-–]\s*(.*?)\s*$', line)
        if match:
            nombre_comun = match.group(1).strip().title()
            nombre_cientifico = match.group(2).strip()
            orden_texto = match.group(3).strip().lower()

            # Limpieza de nombre común: elimina paréntesis con contenido, asteriscos y guiones bajos
            nombre_comun_limpio = re.sub(r'\s*\(.*\)', '', nombre_comun)
            nombre_comun_limpio = re.sub(r'[*_]', '', nombre_comun_limpio).strip()
            
            orden = "o" # Default a omnívoro
            if "carn" in orden_texto:
                orden = "c"
            elif "herb" in orden_texto:
                orden = "h"
            elif "omní" in orden_texto or "omni" in orden_texto:
                orden = "o"
            else:
                # print(f"Orden no reconocido para: {nombre_comun_limpio}. Saltando.") # Silenciar este print
                return None, None, None
            
            return nombre_comun_limpio, nombre_cientifico, orden
        else:
            # print(f"No se pudo parsear la línea: '{line}'") # Silenciar este print
            return None, None, None

    def obtener_animales(self, cantidad):
        """
        Descripción:
            Genera una lista de objetos Animal utilizando la API de Google Gemini para obtener
            información básica y la API de Wikipedia para obtener URLs de imágenes.
        Entradas:
            cantidad (int): El número de animales a generar.
        Salidas:
            list: Una lista de objetos Animal con sus atributos poblados.
        """
        prompt = (
            f"Genera una lista de {cantidad} animales. Para cada animal, proporciona su nombre común, "
            f"su nombre científico y su tipo de alimentación (carnívoro, herbívoro u omnívoro). "
            f"Usa nombres comunes claros y directos que probablemente tengan una página dedicada en Wikipedia en español. " 
            f"Formato estricto: Nombre Común - Nombre Científico - tipo_alimentacion. "
            f"No incluyas numeración, texto introductorio, o texto final. "
            f"Ejemplo: Oso Pardo - Ursus arctos - omnívoro"
        )
        try:
            respuesta = self.model.generate_content(prompt).text
        except Exception as e:
            print("Error al generar contenido desde Gemini:", e)
            return []

        lineas = respuesta.split("\n")
        animales_obtenidos = []
        for linea in lineas:
            nombre_comun_limpio, nombre_cientifico, orden = self._parse_animal_data(linea)
            
            if nombre_comun_limpio and nombre_cientifico and orden:
                wiki_image_url = self._get_wikipedia_image_url(nombre_comun_limpio)
                animal = Animal(nombre_comun_limpio, nombre_cientifico, orden, wiki_image_url=wiki_image_url)
                animales_obtenidos.append(animal)
            
        self.animales = animales_obtenidos
        return self.animales