import csv
import os

class CSVExporter:
    """
    Clase para exportar una lista de objetos Animal a un archivo CSV.
    """
    def __init__(self):
        # Mapeo de valores de calificación a estados emocionales (consistente con el generador PDF)
        self.RATING_EMOTIONAL_MAP = {
            None: "No marcado", # Asume que None o 0 significa sin calificar
            0: "No marcado",
            1: "Me gusta",
            2: "Favorito",
            3: "Me entristece",
            4: "Me enoja",
            5: "Muerto" # Usado 'Muerto' para la calificación 5 ya que se mapea al cráneo en la UI
        }

    def _get_rating_emotional_text(self, rating):
        """Función auxiliar para obtener el texto emocional de una calificación dada."""
        return self.RATING_EMOTIONAL_MAP.get(rating, "Desconocido")

    def export_animals_to_csv(self, animals, output_file_name="inventario_completo.csv"):
        """
        Exporta todos los detalles de una lista de objetos Animal a un archivo CSV.

        Args:
            animals (list): Una lista de objetos Animal.
            output_file_name (str): El nombre del archivo CSV a generar.

        Returns:
            bool: True si el archivo CSV se generó exitosamente, False en caso contrario.
        """
        if not animals:
            print("Advertencia: No hay animales para exportar a CSV.")
            return False

        # Definir los encabezados basados en los atributos del objeto Animal
        # y cualquier información adicional que se desee incluir.
        headers = [
            "ID", "Nombre Común", "Nombre Científico", "Orden", "Estado Numérico",
            "Estado Texto", "Peso (kg)", "Calificación Numérica",
            "Calificación Emocional", "URL Imagen Wiki", "Ruta Imagen Local"
        ]

        try:
            with open(output_file_name, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers) # Escribir la fila de encabezados

                for animal in animals:
                    # Obtener los atributos de forma segura usando getattr,
                    # proporcionando una cadena vacía si el atributo no existe o es None.
                    animal_id = getattr(animal, 'id', '')
                    nombre_comun = getattr(animal, 'nombre_comun', '')
                    nombre_cientifico = getattr(animal, 'nombre_cientifico', '')
                    orden = getattr(animal, 'orden', '')
                    estado_num = getattr(animal, 'estado', '')
                    
                    # Llamar a get_estado_text de forma segura
                    estado_text = animal.get_estado_text() if hasattr(animal, 'get_estado_text') else ''
                    
                    # Formatear el peso si existe, de lo contrario, cadena vacía
                    peso = f"{animal.peso:.2f}" if getattr(animal, 'peso', None) is not None else ''
                    
                    calificacion_num = getattr(animal, 'calificacion', '')
                    calificacion_emocional = self._get_rating_emotional_text(animal.calificacion) # Usar función auxiliar para el texto emocional
                    
                    wiki_image_url = getattr(animal, 'wiki_image_url', '')
                    local_image_path = getattr(animal, 'local_image_path', '')

                    writer.writerow([
                        animal_id, nombre_comun, nombre_cientifico, orden, estado_num,
                        estado_text, peso, calificacion_num,
                        calificacion_emocional, wiki_image_url, local_image_path
                    ])
            return True
        except Exception as e:
            print(f"Error al exportar a CSV: {e}")
            return False

