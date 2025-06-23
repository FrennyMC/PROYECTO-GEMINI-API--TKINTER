from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from collections import defaultdict
from datetime import datetime # Importar datetime para la fecha de generación

# Mapping for rating values to emotional states
RATING_EMOTIONAL_MAP = {
    None: "No marcado", # Assuming None or 0 means not rated
    0: "No marcado",
    1: "Me gusta",
    2: "Favorito",
    3: "Me entristece",
    4: "Me enoja",
    5: "Muerto" # Using 'Muerto' for rating 5 as it maps to skull in UI
}

# Mapping for animal order types (assuming 'h', 'c', 'o' for Herbívoro, Carnívoro, Omnívoro)
ORDER_TYPES_MAP = {
    "h": "Herbívoro",
    "c": "Carnívoro",
    "o": "Omnívoro"
}


class PDFReportGenerator:
    """
    Clase para generar reportes PDF con estadísticas de calificación de animales.
    """
    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Custom style for section titles
        self.styles.add(ParagraphStyle(name='SectionTitle',
                                       parent=self.styles['h2'],
                                       fontSize=14,
                                       spaceAfter=12,
                                       textColor=colors.darkblue))
        # Custom style for table headers
        self.styles.add(ParagraphStyle(name='TableHeader',
                                       parent=self.styles['Normal'],
                                       fontName='Helvetica-Bold',
                                       fontSize=10,
                                       textColor=colors.white,
                                       alignment=1)) # Center alignment
        # Custom style for summary text
        self.styles.add(ParagraphStyle(name='SummaryText',
                                       parent=self.styles['Normal'],
                                       fontSize=11,
                                       spaceBefore=6,
                                       textColor=colors.black))

    def _get_rating_emotional_text(self, rating):
        """Helper to get the emotional text for a given rating."""
        return RATING_EMOTIONAL_MAP.get(rating, "Desconocido")

    def _create_section(self, title, data_rows, summary_text):
        """
        Crea una sección reutilizable para el PDF (título, tabla y resumen).
        
        Args:
            title (str): Título de la sección (e.g., "Calificación: Me gusta").
            data_rows (list): Lista de listas con los datos de la tabla para esta sección.
            summary_text (str): Texto de resumen para esta sección.

        Returns:
            list: Elementos de Story para ReportLab para esta sección.
        """
        story_elements = []
        
        # Add section title
        story_elements.append(Paragraph(title, self.styles['SectionTitle']))
        story_elements.append(Spacer(1, 0.1 * inch))

        # Table headers
        table_headers = [
            Paragraph("Orden", self.styles['TableHeader']),
            Paragraph("Código", self.styles['TableHeader']),
            Paragraph("Nombre Común", self.styles['TableHeader']),
            Paragraph("Estado", self.styles['TableHeader'])
        ]
        
        # Combine headers with data rows
        table_data = [table_headers] + data_rows

        # Define table style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), # Header background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey), # Grid lines
        ])

        # Apply alternating row colors programmatically for better control
        for i in range(len(data_rows)):
            if i % 2 == 0: # For even indices (first data row is index 0)
                table_style.add('BACKGROUND', (0, i + 1), (-1, i + 1), colors.white)
            else: # For odd indices
                table_style.add('BACKGROUND', (0, i + 1), (-1, i + 1), colors.lightgrey)

        animal_table = Table(table_data, colWidths=[1.0*inch, 1.2*inch, 2.0*inch, 1.5*inch])
        animal_table.setStyle(table_style)
        
        story_elements.append(animal_table)
        story_elements.append(Spacer(1, 0.2 * inch))
        
        # Add summary text
        story_elements.append(Paragraph(summary_text, self.styles['SummaryText']))
        story_elements.append(Spacer(1, 0.4 * inch)) # Space after section

        return story_elements

    def generate_rating_statistics_pdf(self, animals, output_file_name):
        """
        Genera un reporte PDF con estadísticas de animales por calificación.

        Args:
            animals (list): Una lista de objetos Animal.
            output_file_name (str): El nombre del archivo PDF a generar.

        Returns:
            bool: True si el PDF se generó exitosamente, False en caso contrario.
        """
        doc = SimpleDocTemplate(output_file_name, pagesize=letter)
        story = []

        # Title Page / Main Title
        story.append(Paragraph("Reporte de Estadísticas de Animales por Calificación", self.styles['h1']))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        story.append(Spacer(1, 0.5 * inch))
        story.append(PageBreak()) # Start content on a new page

        # Group animals by rating
        animals_by_rating = defaultdict(list)
        for animal in animals:
            rating_text = self._get_rating_emotional_text(animal.calificacion)
            animals_by_rating[rating_text].append(animal)

        # Order the rating categories for consistent display
        ordered_rating_categories = [
            "No marcado", "Me gusta", "Favorito", "Me entristece", "Me enoja", "Muerto"
        ]

        total_animals_overall = len(animals)
        overall_summary_counts = defaultdict(int)

        # Add sections for each rating category
        for category in ordered_rating_categories:
            current_category_animals = animals_by_rating.get(category, [])
            count = len(current_category_animals)
            overall_summary_counts[category] = count

            if current_category_animals: # Only create section if there are animals
                data_rows = []
                for i, animal in enumerate(current_category_animals):
                    # Ensure state is handled, assuming animal.get_estado_text() exists
                    estado_text = animal.get_estado_text() if hasattr(animal, 'get_estado_text') else 'N/A'
                    orden_text = ORDER_TYPES_MAP.get(animal.orden.lower(), animal.orden if animal.orden else 'N/A')
                    data_rows.append([
                        f"{i+1}.", # Sequential order number within the group
                        animal.id if animal.id else 'N/A',
                        animal.nombre_comun if animal.nombre_comun else 'N/A',
                        estado_text
                    ])
                
                summary_text = (f"Total de animales en esta categoría: {count}. "
                                f"Representa el {count / total_animals_overall * 100:.2f}% del total."
                                if total_animals_overall > 0 else "No hay animales.")
                
                story.extend(self._create_section(f"Calificación: {category}", data_rows, summary_text))
                story.append(PageBreak()) # New page for each major category

        # Final Summary Section
        story.append(Paragraph("Resumen General de Calificaciones", self.styles['h2']))
        story.append(Spacer(1, 0.2 * inch))

        summary_data = [["Calificación", "Cantidad", "Porcentaje"]]
        for category in ordered_rating_categories:
            count = overall_summary_counts[category]
            percentage = (count / total_animals_overall * 100) if total_animals_overall > 0 else 0
            summary_data.append([category, count, f"{percentage:.2f}%"])

        summary_table = Table(summary_data, colWidths=[2.0*inch, 1.0*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightskyblue), # Overall summary background
            ('GRID', (0, 0), (-1, -1), 1, colors.darkblue),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(f"Total general de animales en el inventario: {total_animals_overall}", self.styles['Normal']))


        try:
            doc.build(story)
            return True
        except Exception as e:
            print(f"Error al generar el PDF: {e}")
            return False

