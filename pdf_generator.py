"""
Gerador de PDF - Plano de Implantação (GMUD)
Utiliza ReportLab Platypus com Padding de Linhas para manter o visual Excel 
mas suportar perfeitamente paginação infinita.
"""

import os
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas

# ── Cores (Excel theme colors) ──────────────────────────────────────────
HEADER_BG = colors.HexColor("#44546A")
LABEL_BG = colors.HexColor("#B4C6E7")
VALUE_BG = colors.HexColor("#D6E4F0")
WHITE = colors.white
BLACK = colors.black
BORDER_COLOR = colors.HexColor("#333F50")

def _register_fonts():
    try:
        c_path = r"C:\Windows\Fonts\calibri.ttf"
        cb_path = r"C:\Windows\Fonts\calibrib.ttf"
        if os.path.exists(c_path) and os.path.exists(cb_path):
            pdfmetrics.registerFont(TTFont("Calibri", c_path))
            pdfmetrics.registerFont(TTFont("Calibri-Bold", cb_path))
            return "Calibri", "Calibri-Bold"
    except Exception:
        pass
    return "Helvetica", "Helvetica-Bold"

def _get_wrapped_lines(c, text, font, size, max_width):
    c.setFont(font, size)
    lines = []
    for paragraph in str(text).split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current_line = words[0]
        for word in words[1:]:
            test = current_line + " " + word
            if c.stringWidth(test, font, size) <= max_width:
                current_line = test
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
    return lines

def generate_pdf(data: dict, output_dir: str = None) -> tuple:
    font_regular, font_bold = _register_fonts()

    id_interna = data.get("id_interna", "SEM_ID").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GMUD_{id_interna}_{timestamp}.pdf"

    buffer = io.BytesIO()
    
    # Margens
    MARGIN_L = 12 * mm
    MARGIN_R = 12 * mm
    MARGIN_T = 8 * mm
    MARGIN_B = 8 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGIN_R,
        leftMargin=MARGIN_L,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B
    )

    FULL_W = A4[0] - MARGIN_L - MARGIN_R
    COL_A_W = FULL_W * 0.34
    COL_B_W = FULL_W - COL_A_W

    styles = getSampleStyleSheet()
    
    style_header = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=10,
        textColor=WHITE,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=0,
    )

    style_label = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=7.5,
        textColor=BLACK,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
    )

    style_value = ParagraphStyle(
        'ValueStyle',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=7.5,
        textColor=BLACK,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
    )

    def _format_date_br(date_str: str) -> str:
        if not date_str:
            return ""
        for fmt_in, fmt_out in [("%Y-%m-%d", "%d/%m/%Y"), ("%d/%m/%Y", "%d/%m/%Y"), ("%d-%m-%Y", "%d/%m/%Y")]:
            try:
                return datetime.strptime(date_str, fmt_in).strftime(fmt_out)
            except ValueError:
                continue
        return date_str

    # Dummy canvas to measure text lines accurately
    temp_canvas = canvas.Canvas(io.BytesIO())
    
    def get_padded_text(key, min_lines, width, is_label=False):
        """Busca o texto e preenche com <br/> para atingir o min_lines garantindo o tamanho da caixa"""
        val = data.get(key, "") if key else ""
        if key == "data_documentacao":
            val = _format_date_br(val)
            
        val = str(val)
        font = font_bold if is_label else font_regular
        size = 7.5
        
        # O padding de cada lado na tabela é 3. Então width real = width - 6
        real_w = width - 6
        lines = _get_wrapped_lines(temp_canvas, val, font, size, real_w)
        num_lines = len(lines)
        
        val_html = val.replace('\n', '<br/>')
        if num_lines < min_lines:
            extra = min_lines - num_lines
            # Adicionamos espaços em branco (br)
            val_html += "<br/>" * extra
            
        return val_html

    def make_paragraph(text, style):
        if not text:
            return Paragraph("", style)
        return Paragraph(text, style)

    elements = []
    
    def add_section_header(title):
        data_table = [[Paragraph(title, style_header)]]
        t = Table(data_table, colWidths=[FULL_W])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), HEADER_BG),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('BOX', (0, 0), (0, 0), 1, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (0, 0), 3),
            ('BOTTOMPADDING', (0, 0), (0, 0), 3),
        ]))
        elements.append(t)

    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO 1: Identificação da Mudança
    # ═══════════════════════════════════════════════════════════════════
    add_section_header("1. Identificação da Mudança")

    sec1_fields = [
        ("ID - Interna", "id_interna"),
        ("Data documentação", "data_documentacao"),
        ("Descrição Mudança", "descricao_mudanca"),
        ("Solicitante", "solicitante"),
        ("Responsável pelo Documento", "responsavel_documento"),
        ("Responsável Técnico (Desenvolvedor)", "responsavel_tecnico"),
        ("Responsável pela Aplicação da Mudança", "responsavel_aplicacao"),
        ("Card(s) Jira", "cards_jira"),
        ("Versão anterior", "versao_anterior"),
        ("Versão atualizada", "versao_atualizada"),
        ("Tipo da Mudança", "tipo_mudanca"),
        ("Classificação dos Riscos", "classificacao_riscos"),
        ("PR", "pr"),
        ("Interdependência de Merges", "interdependencia_merges"),
    ]
    
    sec1_data = []
    for label, key in sec1_fields:
        val = get_padded_text(key, min_lines=1, width=COL_B_W)
        # Para os labels da seçao 1 mantemos originais pois nao tem padding fixo superior a 1
        sec1_data.append([make_paragraph(label, style_label), make_paragraph(val, style_value)])
        
    t1 = Table(sec1_data, colWidths=[COL_A_W, COL_B_W])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LABEL_BG),
        ('BACKGROUND', (1, 0), (1, -1), VALUE_BG),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 4))

    def add_field_row(label, value_key, min_lines):
        val = get_padded_text(value_key, min_lines, width=COL_B_W)
        # We pad the label side so the row itself forces the height
        lbl_html = label + ("<br/>" * max(0, min_lines - 1))
        return [make_paragraph(lbl_html, style_label), make_paragraph(val, style_value)]

    def draw_table(table_data):
        t = Table(table_data, colWidths=[COL_A_W, COL_B_W])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LABEL_BG),
            ('BACKGROUND', (1, 0), (1, -1), VALUE_BG),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4))

    def draw_full_width_table(value_key, min_lines):
        val = get_padded_text(value_key, min_lines, width=FULL_W)
        t = Table([[make_paragraph(val, style_value)]], colWidths=[FULL_W])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), VALUE_BG),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4))

    add_section_header("2. Descrição da Mudança")
    draw_table([add_field_row("Objetivo da Alteração", "objetivo_alteracao", 5)])

    add_section_header("3. Ambiente e Impactos")
    draw_table([
        add_field_row("Sistemas e Servidores Envolvidos", "sistemas_servidores", 4),
        add_field_row("Impactos Previstos", "impactos_previstos", 3),
        add_field_row("Tempo de Indisponibilidade", "tempo_indisponibilidade", 2)
    ])

    add_section_header("4. Escopo Técnico")
    draw_table([
        add_field_row("Escopo técnico Aplicado", "escopo_tecnico", 5),
        add_field_row("Regras aplicadas", "regras_aplicadas", 2),
        add_field_row("Alterações em estruturas", "alteracoes_estruturas", 5)
    ])

    add_section_header("5. Plano de Implementação")
    draw_full_width_table("plano_implementacao", 12)

    add_section_header("6. Plano de Rollback")
    draw_full_width_table("plano_rollback", 12)

    add_section_header("7. Validação após mudança")
    draw_full_width_table("validacao_pos_mudanca", 14)

    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return filename, pdf_bytes
