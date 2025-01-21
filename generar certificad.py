# Crear nuevo documento PDF con la información proporcionada
import datetime
import fpdf

pdf = fpdf.FPDF(format="letter")
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Arial", size=12)

# Fecha actual
fecha_actual = datetime.datetime.today().strftime("%d de %B de %Y")

# Título
pdf.set_font("Arial", style='B', size=14)
pdf.cell(200, 10, "SOLICITUD DE CERTIFICADO", ln=True, align="C")
pdf.ln(10)

# Contenido con datos del usuario
pdf.set_font("Arial", size=12)
contenido = f"""
Medellín, Colombia, {fecha_actual}

A quien corresponda,

Por medio de la presente, yo Juan José García Urrea, identificado con el 
documento de identidad 1037647586, solicito el Certificado de Antigüedad, 
Preexistencias y Utilizaciones, requerido para fines administrativos.

Datos de contacto:
- Correo electrónico: jjgu95@gmail.com
- Teléfono: 3007970175

Agradezco la emisión del documento en el menor tiempo posible y quedo atento 
a cualquier requerimiento adicional para procesar esta solicitud.

Atentamente,

Juan José García Urrea
"""

pdf.multi_cell(0, 10, contenido)

# Espacio para la firma
pdf.ln(20)
pdf.cell(0, 10, "Firma electrónica:", ln=True)
pdf.cell(0, 10, "_________________________", ln=True)

# Guardar PDF
pdf_filename = "Solicitud_Certificado_JJGU.pdf"
pdf.output(pdf_filename)

pdf_filename
