import os, sys, urllib.request, tempfile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

GITHUB_BASE = "https://raw.githubusercontent.com/realzurita/sic2-presupuestos/main"

def _download(filename):
    url = f"{GITHUB_BASE}/{filename}"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
    urllib.request.urlretrieve(url, tmp.name)
    return tmp.name

_FONT_REGULAR = _download("Inter-Regular.ttf")
_FONT_MEDIUM  = _download("Inter-Medium.ttf")
_LOGO_PATH    = _download("logo_sic.png")

pdfmetrics.registerFont(TTFont("Inter",        _FONT_REGULAR))
pdfmetrics.registerFont(TTFont("Inter-Medium", _FONT_MEDIUM))

DATOS = {
    "jorge": {
        "nombre": "Jorge Correa Suárez",
        "nif": "44729044R",
        "direccion": "C/ Olof Palme 33 B P08 I",
        "ciudad": "Las Palmas de GC, 35010 – Las Palmas",
        "iban": "ES06 1465 0100 9117 3932 8359",
    },
    "alejandro": {
        "nombre": "Alejandro Zurita García",
        "nif": "44740611E",
        "direccion": "C/ El Cid 38 Portal B 8D",
        "ciudad": "Las Palmas de GC, 35010 – Las Palmas",
        "iban": "ES07 1465 0100 9917 7302 8271",
    },
}

NOMBRE_COMERCIAL = "SERVICIOS INTEGRALES PARA COMUNIDADES CANARIAS"
IGIC_NOTA = "Exento de IGIC por franquicia fiscal"

NAVY       = colors.HexColor("#1B2A6B")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MID_GRAY   = colors.HexColor("#CCCCCC")

PAGE_W, PAGE_H = A4
MARGIN_L = 2*cm
MARGIN_R = 2*cm
MARGIN_T = 2.2*cm
FOOTER_H = 1.8*cm
MARGIN_B = FOOTER_H + 0.8*cm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


def make_footer(canvas, doc, iban):
    canvas.saveState()
    y_line = FOOTER_H + 0.3*cm
    canvas.setStrokeColor(MID_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_L, y_line, PAGE_W - MARGIN_R, y_line)
    canvas.setFont("Inter", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawCentredString(PAGE_W/2, y_line - 0.45*cm,
        "Pagar por transferencia bancaria al siguiente número de cuenta:")
    canvas.setFont("Inter-Medium", 9)
    canvas.setFillColor(NAVY)
    canvas.drawCentredString(PAGE_W/2, y_line - 0.9*cm, iban)
    canvas.restoreState()


def generar_presupuesto(autor, num_presupuesto, fecha, cliente, conceptos, output_path):
    datos = DATOS[autor.lower()]

    def footer_func(canvas, doc):
        make_footer(canvas, doc, datos["iban"])

    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
    )
    frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=footer_func)])

    def st(name, font="Inter", size=8.5, color=colors.black, align=TA_LEFT, leading=None, **kw):
        return ParagraphStyle(name, fontName=font, fontSize=size, textColor=color,
                              alignment=align, leading=leading or size*1.4, **kw)

    st_nombre_com = st("NomCom",  "Inter-Medium", 11, NAVY,  spaceAfter=3)
    st_emisor     = st("Emisor",  "Inter",        8.5, colors.black, leading=15)
    st_titulo     = st("Titulo",  "Inter-Medium", 22,  NAVY,  spaceAfter=6)
    st_label      = st("Label",   "Inter-Medium", 8.5, NAVY,  spaceAfter=3)
    st_valor      = st("Valor",   "Inter",        8.5, colors.black, leading=15)
    st_col_hdr    = st("ColHdr",  "Inter-Medium", 8.5, colors.white, TA_CENTER)
    st_ctitulo    = st("CTitulo", "Inter-Medium", 8.5, colors.black, leading=14, spaceAfter=2)
    st_cdesc      = st("CDesc",   "Inter",        8.5, colors.HexColor("#444444"), leading=13)
    st_precio     = st("Precio",  "Inter",        8.5, colors.black, TA_RIGHT)
    st_tl         = st("TL",      "Inter-Medium", 9,   colors.white, TA_RIGHT)
    st_tv         = st("TV",      "Inter-Medium", 9,   colors.white, TA_RIGHT)
    st_nota       = st("Nota",    "Inter",        7.5, colors.HexColor("#555555"), TA_RIGHT)
    st_num        = st("Num",     "Inter",        8.5, colors.black, TA_RIGHT)
    st_center     = st("Center",  "Inter",        8.5, colors.black, TA_CENTER)

    story = []

    logo_img = Image(_LOGO_PATH, width=4*cm, height=2.4*cm)
    emisor_block = [
        Paragraph(NOMBRE_COMERCIAL, st_nombre_com),
        Paragraph(datos["nombre"],    st_emisor),
        Paragraph(datos["nif"],       st_emisor),
        Paragraph(datos["direccion"], st_emisor),
        Paragraph(datos["ciudad"],    st_emisor),
    ]
    hdr = Table([[logo_img, emisor_block]], colWidths=[4.2*cm, CONTENT_W - 4.2*cm])
    hdr.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (0,0),   0),
        ("RIGHTPADDING", (0,0), (0,0),   8),
        ("LEFTPADDING",  (1,0), (1,0),   4),
        ("RIGHTPADDING", (1,0), (1,0),   0),
        ("TOPPADDING",   (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",(0,0), (-1,-1), 0),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY))
    story.append(Spacer(1, 0.5*cm))

    titulo_tbl = Table([[Paragraph("PRESUPUESTO", st_titulo)]], colWidths=[CONTENT_W])
    titulo_tbl.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0), (0,0), 0),
        ("RIGHTPADDING", (0,0), (0,0), 0),
        ("TOPPADDING",   (0,0), (0,0), 0),
        ("BOTTOMPADDING",(0,0), (0,0), 0),
    ]))
    story.append(titulo_tbl)
    story.append(Spacer(1, 0.4*cm))

    cliente_lines = [Paragraph("Cliente", st_label),
                     Paragraph(cliente.get("nombre", ""), st_valor)]
    if cliente.get("nif"):
        cliente_lines.append(Paragraph(cliente["nif"], st_valor))
    if cliente.get("direccion"):
        cliente_lines.append(Paragraph(cliente["direccion"], st_valor))

    ref_lines = [
        Paragraph(f'Nº Presupuesto: <b>{num_presupuesto}</b>', st_num),
        Paragraph(f'Fecha: {fecha}', st_num),
    ]
    info = Table([[cliente_lines, ref_lines]], colWidths=[CONTENT_W*0.6, CONTENT_W*0.4])
    info.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING",   (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",(0,0), (-1,-1), 0),
    ]))
    story.append(info)
    story.append(Spacer(1, 0.6*cm))

    col_widths = [CONTENT_W - 9.5*cm, 2.2*cm, 2.2*cm, 2.5*cm, 2.6*cm]
    table_data = [[
        Paragraph("CONCEPTO",  st_col_hdr),
        Paragraph("PRECIO",    st_col_hdr),
        Paragraph("UNIDADES",  st_col_hdr),
        Paragraph("SUBTOTAL",  st_col_hdr),
        Paragraph("TOTAL",     st_col_hdr),
    ]]
    total_base = 0

    for c in conceptos:
        precio   = float(c["precio"])
        unidades = float(c.get("unidades", 1))
        subtotal = precio * unidades
        total_base += subtotal

        cell = [Paragraph(c["titulo"], st_ctitulo)]
        if c.get("descripcion"):
            cell.append(Paragraph(c["descripcion"], st_cdesc))

        table_data.append([
            cell,
            Paragraph(f"{precio:,.2f}€", st_precio),
            Paragraph(str(int(unidades)) if unidades == int(unidades) else str(unidades), st_center),
            Paragraph(f"{subtotal:,.2f}€", st_precio),
            Paragraph(f"{subtotal:,.2f}€", st_precio),
        ])

    n = len(conceptos)
    table_data.append([
        Paragraph("", st_cdesc), Paragraph("", st_cdesc), Paragraph("", st_cdesc),
        Paragraph("TOTAL", st_tl),
        Paragraph(f"{total_base:,.2f}€", st_tv),
    ])
    table_data.append([
        Paragraph("", st_cdesc), Paragraph("", st_cdesc), Paragraph("", st_cdesc),
        Paragraph(IGIC_NOTA, st_nota),
        Paragraph("", st_nota),
    ])

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),    NAVY),
        ("ROWBACKGROUNDS",(0,1),  (-1,n),    [colors.white, LIGHT_GRAY]),
        ("BACKGROUND",    (3,n+1),(-1,n+1),  NAVY),
        ("GRID",          (0,0),  (-1,n),    0.5, MID_GRAY),
        ("LINEBELOW",     (0,n),  (-1,n),    1,   NAVY),
        ("VALIGN",        (0,0),  (-1,n+1),  "MIDDLE"),
        ("VALIGN",        (0,n+2),(-1,n+2),  "TOP"),
        ("TOPPADDING",    (0,0),  (-1,n+1),  8),
        ("BOTTOMPADDING", (0,0),  (-1,n+1),  8),
        ("LEFTPADDING",   (0,0),  (-1,-1),   7),
        ("RIGHTPADDING",  (0,0),  (-1,-1),   7),
        ("TOPPADDING",    (0,n+2),(-1,n+2),  5),
        ("BOTTOMPADDING", (0,n+2),(-1,n+2),  0),
        ("SPAN",          (3,n+2),(4,n+2)),
    ]))
    story.append(tbl)
    doc.build(story)
    print(f"✅ {output_path}")
