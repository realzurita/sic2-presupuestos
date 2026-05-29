"""
generar_proyecto.py — SIC² / Presupuestos
Genera las 3 páginas de PROYECTO (portada + memoria + planificación)
y opcionalmente las fusiona con el presupuesto en un único PDF.

Uso:
    python generar_proyecto.py          # solo proyecto (3 páginas)
    python generar_proyecto.py --full   # proyecto + presupuesto fusionados

Todos los assets se descargan de GitHub. No usar archivos locales.
"""

import os, sys, urllib.request, tempfile, io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
                                 HRFlowable, Image, PageBreak,
                                 BaseDocTemplate, Frame, PageTemplate)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfWriter, PdfReader

# ── GITHUB ────────────────────────────────────────────────────────────────────
GITHUB_BASE = "https://raw.githubusercontent.com/realzurita/sic2-presupuestos/main"

def _download(filename):
    url = f"{GITHUB_BASE}/{filename}"
    tmp = tempfile.NamedTemporaryFile(delete=False,
                                      suffix=os.path.splitext(filename)[1])
    urllib.request.urlretrieve(url, tmp.name)
    return tmp.name

print("Descargando assets de GitHub...")
_FONT_REGULAR = _download("Inter-Regular.ttf")
_FONT_MEDIUM  = _download("Inter-Medium.ttf")
_LOGO_PATH    = _download("logo_sic.png")
_PORTADA_PATH = _download("portada.jpg")
print("Assets OK")

pdfmetrics.registerFont(TTFont("Inter",        _FONT_REGULAR))
pdfmetrics.registerFont(TTFont("Inter-Medium", _FONT_MEDIUM))

# ── CONSTANTES ────────────────────────────────────────────────────────────────
NAVY      = colors.HexColor("#1B2A6B")
MID_GRAY  = colors.HexColor("#CCCCCC")
PAGE_W, PAGE_H = A4
MARGIN_L  = 2 * cm
MARGIN_R  = 2 * cm
MARGIN_T  = 2.2 * cm
FOOTER_H  = 1.8 * cm
MARGIN_B  = 2 * cm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# ── DATOS — editar según emisor y obra ───────────────────────────────────────
EMISOR = {
    "nombre":    "Jorge Correa Suárez",
    "nif":       "44729044R",
    "direccion": "C/ Olof Palme 33 B P08 I",
    "ciudad":    "Las Palmas de GC, 35010 – Las Palmas",
    "iban":      "ES06 1465 0100 9117 3932 8359",
    "tel":       "614 944 458",
}
NOMBRE_COMERCIAL = "SERVICIOS INTEGRALES PARA COMUNIDADES CANARIAS"

NUM_PRESUPUESTO = "P260121"
FECHA           = "27/05/2026"
TITULO_L1       = "DESAMIANTADO, IMPERMEABILIZACIÓN"
TITULO_L2       = "Y TRABAJOS COMPLEMENTARIOS"
CLIENTE_L1      = "COMUNIDAD DE PROPIETARIOS GOBERNADOR MARÍN ACUÑA"
CLIENTE_L2      = "LAS PALMAS DE GC"

MEMORIA_ITEMS = [
    "El presente presupuesto corresponde a los trabajos de retirada de elementos de fibrocemento con contenido en amianto, impermeabilización de azotea, enfoscado y saneado de pretiles, sustitución de instalación de fontanería y trabajos complementarios de retirada de escombros en el edificio de la Comunidad de Propietarios Gobernador Marín Acuña.",
    "Debido a la presencia de materiales con amianto, los trabajos de desamiantado serán ejecutados por empresa especializada y debidamente autorizada, previa elaboración y aprobación del correspondiente Plan de Trabajo por parte de la autoridad laboral competente. Los residuos generados serán gestionados a través de empresa gestora autorizada con traslado a vertedero homologado, incluyendo toda la documentación acreditativa exigida por la normativa vigente.",
    "Los trabajos de impermeabilización y saneado de la azotea incluirán el picado y eliminación de zonas con mortero en mal estado, reparación mediante morteros estructurales, aplicación de imprimación y colocación de malla de fibra de vidrio con pintura impermeabilizante elástica. Adicionalmente se ejecutará la sustitución de la instalación de fontanería existente en fibrocemento por tubería de polipropileno reticulado (PPR), conforme a normativa vigente.",
]

PLANIFICACION_INTRO = (
    "Los trabajos se ejecutarán de forma coordinada y secuencial, atendiendo en primer lugar "
    "al desamiantado, que condiciona el inicio del resto de actuaciones. Se estima un plazo "
    "total de dos a tres semanas en función del estado real de los elementos a intervenir y "
    "de las condiciones de acceso, salvo imprevistos derivados de la tramitación administrativa "
    "del Plan de Trabajo."
)

FASES = [
    ("1) ACCESO Y PREPARACIÓN", [
        "Tramitación y aprobación del Plan de Trabajo específico para trabajos con amianto ante la autoridad laboral competente.",
        "Coordinación de accesos con la comunidad y vecinos afectados.",
        "Instalación de medios auxiliares, protecciones colectivas y señalización de zonas de trabajo.",
        "Protección de suelos, elementos sensibles y zonas de paso.",
    ]),
    ("2) FASE DE DESAMIANTADO", [
        "Retirada manual de bidones de fibrocemento con las protecciones y equipos específicos reglamentarios.",
        "Paletizado, embalado y etiquetado de residuos según las indicaciones de la Delegación de Trabajo.",
        "Toma de muestras ambientales durante la ejecución y tras la finalización de los trabajos.",
        "Gestión de residuos con empresa gestora autorizada y traslado a vertedero homologado.",
        "Retirada y gestión de elementos no contaminados (bloques de hormigón y bidones de plástico).",
    ]),
    ("3) FASE DE OBRAS COMPLEMENTARIAS", [
        "Picado y saneado de zonas con mortero deteriorado en pretiles y paramentos verticales de azotea.",
        "Enfoscado maestreado con mortero de cemento para regularización de superficies.",
        "Aplicación de imprimación, colocación de malla de fibra de vidrio y pintura impermeabilizante elástica.",
        "Sustitución de instalación de fontanería de fibrocemento por tubería PPR vista, con todos sus accesorios.",
        "Instalación de camión grúa para la retirada de materiales y gestión de ocupación de vía pública.",
    ]),
    ("4) FINALIZACIÓN Y ENTREGA", [
        "Desmontaje de medios auxiliares y retirada de protecciones.",
        "Recogida, carga y transporte de escombros a vertedero autorizado, con documentación acreditativa.",
        "Limpieza completa de todas las zonas de trabajo.",
        "Entrega de documentación: certificados de gestión de residuos de amianto y demás acreditaciones.",
    ]),
]

OUTPUT = f"{NUM_PRESUPUESTO}_PROYECTO_JORGE.pdf"

# ══════════════════════════════════════════════════════════════════════════════
#  PÁGINA 1 — PORTADA (canvas directo)
# ══════════════════════════════════════════════════════════════════════════════
def build_portada():
    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=A4)
    W, H = PAGE_W, PAGE_H

    # Fondo portada.jpg a página completa
    fondo = ImageReader(_PORTADA_PATH)
    c.drawImage(fondo, 0, 0, width=W, height=H, preserveAspectRatio=False)

    # Logo — preserveAspectRatio=True, ancla en esquina superior izquierda
    logo = ImageReader(_LOGO_PATH)
    logo_w = 3.2 * cm
    logo_h = 2.0 * cm
    logo_x = MARGIN_L
    logo_y = H - 1.8 * cm - logo_h
    c.drawImage(logo, logo_x, logo_y, width=logo_w, height=logo_h,
                mask='auto', preserveAspectRatio=True)

    # Sin texto junto al logo

    # Etiqueta PRESUPUESTO
    c.setFont("Inter-Medium", 18)
    c.setFillColor(NAVY)
    y_label = H - 6.5 * cm
    c.drawString(MARGIN_L, y_label, "PRESUPUESTO")

    # Número grande
    c.setFont("Inter-Medium", 58)
    y_num = y_label - 2.4 * cm
    c.drawString(MARGIN_L, y_num, NUM_PRESUPUESTO)

    # Título de la obra
    c.setFont("Inter", 18)
    c.setFillColor(NAVY)
    y_titulo = y_num - 1.6 * cm
    c.drawString(MARGIN_L, y_titulo,            TITULO_L1)
    c.drawString(MARGIN_L, y_titulo - 0.75 * cm, TITULO_L2)

    # Cliente
    c.setFont("Inter-Medium", 11)
    y_cliente = y_titulo - 2.1 * cm
    c.drawString(MARGIN_L, y_cliente,             CLIENTE_L1)
    c.setFont("Inter", 10.5)
    c.drawString(MARGIN_L, y_cliente - 0.58 * cm, CLIENTE_L2)

    # Datos emisor — abajo a la derecha, 5 líneas
    emisor_lines = [
        EMISOR["nombre"],
        EMISOR["nif"],
        EMISOR["direccion"],
        EMISOR["ciudad"],
        f"Tel / WhatsApp {EMISOR['tel']}",
    ]
    c.setFont("Inter", 8)
    c.setFillColor(colors.HexColor("#444444"))
    y_pie = 2.5 * cm
    for linea in reversed(emisor_lines):
        c.drawRightString(W - MARGIN_R, y_pie, linea)
        y_pie += 0.38 * cm

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# ══════════════════════════════════════════════════════════════════════════════
#  PÁGINAS 2-3 — MEMORIA + PLANIFICACIÓN (Platypus)
# ══════════════════════════════════════════════════════════════════════════════
def build_interior():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_path = tmp.name
    tmp.close()

    def footer_func(canvas, doc):
        pass  # Sin footer en páginas de proyecto

    doc = BaseDocTemplate(
        tmp_path, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
    )
    frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W,
                  PAGE_H - MARGIN_T - MARGIN_B,
                  leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=frame,
                                       onPage=footer_func)])

    def st(name, font="Inter", size=9, color=colors.black,
           align=TA_LEFT, leading=None, **kw):
        return ParagraphStyle(name, fontName=font, fontSize=size,
                              textColor=color, alignment=align,
                              leading=leading or size * 1.45, **kw)

    s_hc   = st("HC", "Inter-Medium", 11,  NAVY)
    s_em   = st("EM", "Inter",        8.5, colors.black, leading=14)
    s_val  = st("VL", "Inter",        8.5, colors.black, leading=14)
    s_ref  = st("RF", "Inter-Medium", 8.5, NAVY, TA_RIGHT)
    s_sec  = st("SC", "Inter-Medium", 13,  colors.white)
    s_body = st("BD", "Inter",        9,   colors.HexColor("#222222"),
                leading=15, spaceAfter=6)
    s_sub  = st("SU", "Inter-Medium", 9,   NAVY, leading=14, spaceAfter=4)
    s_bul  = st("BU", "Inter",        9,   colors.HexColor("#333333"),
                leading=14, leftIndent=12, spaceAfter=3)

    def cabecera():
        logo_img = Image(_LOGO_PATH, width=3.8 * cm, height=2.3 * cm)
        eb = [
            Paragraph(NOMBRE_COMERCIAL, s_hc),
            Paragraph(EMISOR["nombre"],    s_em),
            Paragraph(EMISOR["nif"],       s_em),
            Paragraph(EMISOR["direccion"], s_em),
            Paragraph(EMISOR["ciudad"],    s_em),
        ]
        hdr = Table([[logo_img, eb]],
                    colWidths=[4.2 * cm, CONTENT_W - 4.2 * cm])
        hdr.setStyle(TableStyle([
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",   (0,0), (0,0),   0),
            ("RIGHTPADDING",  (0,0), (0,0),   8),
            ("LEFTPADDING",   (1,0), (1,0),   4),
            ("RIGHTPADDING",  (1,0), (1,0),   0),
            ("TOPPADDING",    (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        return hdr

    def banner(texto):
        t = Table([[Paragraph(texto, s_sec)]], colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), NAVY),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING",   (0,0), (-1,-1), 12),
            ("RIGHTPADDING",  (0,0), (-1,-1), 12),
        ]))
        return t

    story = []

    # ── MEMORIA ──────────────────────────────────────────────────────────────
    story.append(cabecera())
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY))
    story.append(Spacer(1, 0.3 * cm))

    ref_txt     = (f"<b>REF: OBRA EN COMUNIDAD</b><br/>"
                   f"{NUM_PRESUPUESTO}<br/>FECHA: {FECHA}")
    cliente_txt = (f"<b>CLIENTE</b><br/>{CLIENTE_L1}<br/>{CLIENTE_L2}")
    info = Table([[Paragraph(cliente_txt, s_val),
                   Paragraph(ref_txt, s_ref)]],
                 colWidths=[CONTENT_W * 0.6, CONTENT_W * 0.4])
    info.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(info)
    story.append(Spacer(1, 0.5 * cm))
    story.append(banner("MEMORIA"))
    story.append(Spacer(1, 0.5 * cm))

    # Ítems numerados: número grande gris (#DDD 28pt) + texto body
    for i, texto in enumerate(MEMORIA_ITEMS, 1):
        s_num = st(f"NB{i}", "Inter-Medium", 28,
                   colors.HexColor("#DDDDDD"), TA_LEFT)
        row = Table([[Paragraph(str(i), s_num),
                      Paragraph(texto, s_body)]],
                    colWidths=[1.4 * cm, CONTENT_W - 1.4 * cm])
        row.setStyle(TableStyle([
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",   (0,0), (-1,-1), 0),
            ("RIGHTPADDING",  (0,0), (-1,-1), 0),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(row)
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY))
        story.append(Spacer(1, 0.3 * cm))

    # ── PLANIFICACIÓN ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(cabecera())
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY))
    story.append(Spacer(1, 0.3 * cm))
    story.append(banner("PLANIFICACIÓN Y EJECUCIÓN"))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(PLANIFICACION_INTRO, s_body))
    story.append(Spacer(1, 0.3 * cm))

    for titulo_fase, bullets in FASES:
        story.append(Paragraph(titulo_fase, s_sub))
        for b in bullets:
            story.append(Paragraph(f"• {b}", s_bul))
        story.append(Spacer(1, 0.25 * cm))

    doc.build(story)
    return tmp_path

# ══════════════════════════════════════════════════════════════════════════════
#  MERGE FINAL
# ══════════════════════════════════════════════════════════════════════════════
def generar(with_presupuesto=False, presupuesto_path=None):
    print("Generando portada...")
    portada_buf = build_portada()

    print("Generando memoria y planificación...")
    interior_path = build_interior()

    writer = PdfWriter()

    for page in PdfReader(portada_buf).pages:
        writer.add_page(page)
    for page in PdfReader(interior_path).pages:
        writer.add_page(page)

    if with_presupuesto and presupuesto_path:
        print("Añadiendo presupuesto...")
        for page in PdfReader(presupuesto_path).pages:
            writer.add_page(page)

    with open(OUTPUT, "wb") as f:
        writer.write(f)

    os.remove(interior_path)
    print(f"✅ PDF generado: {OUTPUT}")

if __name__ == "__main__":
    full = "--full" in sys.argv
    ppto = sys.argv[2] if full and len(sys.argv) > 2 else None
    generar(with_presupuesto=full, presupuesto_path=ppto)
