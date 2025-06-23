import os
from collections import defaultdict

# Helper mapping for animal order types (assuming 'h', 'c', 'o' for Herbívoro, Carnívoro, Omnívoro)
ORDER_TYPES_MAP = {
    "h": "Herbívoro",
    "c": "Carnívoro",
    "o": "Omnívoro"
}

class HTMLReportGenerator:
    """
    Clase para generar informes HTML a partir de listas de objetos Animal.
    """
    def __init__(self):
        # Mapeo de valores de calificación a estados emocionales (consistente con el generador PDF y CSV)
        self.RATING_EMOTIONAL_MAP = {
            None: "No marcado",
            0: "No marcado",
            1: "Me gusta",
            2: "Favorito",
            3: "Me entristece",
            4: "Me enoja",
            5: "Muerto"
        }

    def _get_rating_emotional_text(self, rating):
        """Función auxiliar para obtener el texto emocional de una calificación dada."""
        return self.RATING_EMOTIONAL_MAP.get(rating, "Desconocido")

    def generate_html_content_string(self, animals, title="Resumen de Inventario de Animales"):
        """
        Genera el contenido HTML para una tabla de animales con peso, ordenado de mayor a menor.
        Este método no guarda el archivo, solo retorna el string HTML.
        """
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f4f9; color: #333; }}
                h1 {{ text-align: center; color: #2c3e50; margin-bottom: 30px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                table {{ width: 80%; border-collapse: collapse; margin: 25px auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #34495e; color: white; font-weight: bold; text-transform: uppercase; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #e9ecef; cursor: pointer; }}
                .no-data {{ text-align: center; color: #777; padding: 20px; font-style: italic; }}
                .animal-image {{ width: 80px; height: 80px; object-fit: cover; border-radius: 5px; border: 1px solid #ccc; }}
                .header-container {{ display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }}
                .zoo-icon {{ font-size: 2em; margin-right: 10px; }}
            </style>
        </head>
        <body>
            <div class="header-container">
                <span class="zoo-icon">🐾</span>
                <h1>{title}</h1>
                <span class="zoo-icon">🌍</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Número</th>
                        <th>Código</th>
                        <th>Nombre Común</th>
                        <th>Nombre Científico</th>
                        <th>Peso (kg)</th>
                        <th>Estado</th>
                        <th>Calificación</th>
                        <th>Foto</th>
                    </tr>
                </thead>
                <tbody>
        """

        if not animals:
            html_content += """
                    <tr>
                        <td colspan="8" class="no-data">No hay animales para mostrar en este reporte.</td>
                    </tr>
            """
        else:
            for i, animal in enumerate(animals):
                # Usar getattr para acceder a los atributos de forma segura
                animal_id = getattr(animal, 'id', 'N/A')
                nombre_comun = getattr(animal, 'nombre_comun', 'N/A')
                nombre_cientifico = getattr(animal, 'nombre_cientifico', 'N/A')
                peso = f"{animal.peso:.2f}" if getattr(animal, 'peso', None) is not None else 'N/A'
                estado_text = animal.get_estado_text() if hasattr(animal, 'get_estado_text') else 'N/A'
                calificacion_text = self._get_rating_emotional_text(getattr(animal, 'calificacion', None))

                image_url = getattr(animal, 'wiki_image_url', '')
                local_image_path = getattr(animal, 'local_image_path', '')

                # Priorizar imagen local si existe, de lo contrario usar URL de Wikipedia
                img_src = ""
                if local_image_path and os.path.exists(local_image_path):
                    img_src = f"file:///{os.path.abspath(local_image_path)}" # Esto funciona en la mayoría de navegadores locales
                elif image_url:
                    img_src = image_url
                else:
                    img_src = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png"


                html_content += f"""
                    <tr>
                        <td>{i + 1}</td>
                        <td>{animal_id}</td>
                        <td>{nombre_comun}</td>
                        <td>{nombre_cientifico}</td>
                        <td>{peso}</td>
                        <td>{estado_text}</td>
                        <td>{calificacion_text}</td>
                        <td><img src="{img_src}" alt="{nombre_comun}" class="animal-image"></td>
                    </tr>
                """
        
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        return html_content

    def generate_html_report(self, animals, output_file_name="inventario_resumen.html", title="Resumen de Inventario de Animales"):
        """
        Genera un archivo HTML con una tabla de animales.
        """
        html_content = self.generate_html_content_string(animals, title)
        
        try:
            with open(output_file_name, "w", encoding="utf-8") as f:
                f.write(html_content)
            return True
        except Exception as e:
            print(f"Error al generar el archivo HTML: {e}")
            return False

    def generate_order_report_html(self, animals, order_type_display_name, output_file_name="reporte_orden_alimenticio.html"):
        """
        Genera un archivo HTML con una tabla de animales de un orden alimenticio específico.
        Incluye numeración de filas y estilos específicos.
        
        Args:
            animals (list): Lista de objetos Animal a incluir en el reporte.
            order_type_display_name (str): El nombre del orden a mostrar en el título (e.g., "Carnívoros").
            output_file_name (str): El nombre del archivo HTML a generar.
        """
        title = f"Animales {order_type_display_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f4f9; color: #333; }}
                h1 {{ text-align: center; color: #e74c3c; margin-bottom: 30px; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }} /* Título resaltado */
                table {{ width: 80%; border-collapse: collapse; margin: 25px auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #34495e; color: white; font-weight: bold; text-transform: uppercase; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }} /* Filas pares */
                tr:nth-child(odd) {{ background-color: #ffffff; }} /* Filas impares (para alternar bien) */
                tr:hover {{ background-color: #e9ecef; cursor: pointer; }}
                .no-data {{ text-align: center; color: #777; padding: 20px; font-style: italic; }}
                .animal-image {{ width: 80px; height: 80px; object-fit: cover; border-radius: 5px; border: 1px solid #ccc; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <table>
                <thead>
                    <tr>
                        <th>Número</th>
                        <th>Código</th>
                        <th>Nombre Común</th>
                        <th>Nombre Científico</th>
                        <th>Foto</th>
                    </tr>
                </thead>
                <tbody>
        """

        if not animals:
            html_content += """
                    <tr>
                        <td colspan="5" class="no-data">No hay animales de este orden para mostrar.</td>
                    </tr>
            """
        else:
            for i, animal in enumerate(animals):
                animal_id = getattr(animal, 'id', 'N/A')
                nombre_comun = getattr(animal, 'nombre_comun', 'N/A')
                nombre_cientifico = getattr(animal, 'nombre_cientifico', 'N/A')
                
                image_url = getattr(animal, 'wiki_image_url', '')
                local_image_path = getattr(animal, 'local_image_path', '')

                img_src = ""
                if local_image_path and os.path.exists(local_image_path):
                    img_src = f"file:///{os.path.abspath(local_image_path)}"
                elif image_url:
                    img_src = image_url
                else:
                    img_src = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png"

                html_content += f"""
                    <tr>
                        <td>{i + 1}</td>
                        <td>{animal_id}</td>
                        <td>{nombre_comun}</td>
                        <td>{nombre_cientifico}</td>
                        <td><img src="{img_src}" alt="{nombre_comun}" class="animal-image"></td>
                    </tr>
                """
        
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        try:
            with open(output_file_name, "w", encoding="utf-8") as f:
                f.write(html_content)
            return True
        except Exception as e:
            print(f"Error al generar el archivo HTML para el reporte de orden: {e}")
            return False

