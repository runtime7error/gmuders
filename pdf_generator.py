"""
Gerador de PDF - Plano de Implantação (GMUD)
Reproduz EXATAMENTE o layout do Excel em 1 única página A4 vertical.
Usa ReportLab canvas para controle pixel-perfect.
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ── Cores (Excel theme colors) ──────────────────────────────────────────
HEADER_BG = colors.HexColor("#44546A")      # theme=3, tint=-0.25 → azul escuro
LABEL_BG = colors.HexColor("#B4C6E7")       # theme=4, tint=0.60 → azul médio
VALUE_BG = colors.HexColor("#D6E4F0")       # theme=4, tint=0.80 → azul claro
WHITE = colors.white
BLACK = colors.black
BORDER_COLOR = colors.HexColor("#333F50")

PAGE_W, PAGE_H = A4  # 595.27 x 841.89 pts


def _register_fonts():
    """Registra Calibri se disponível, senão usa Helvetica."""
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


def _draw_rect(c, x, y, w, h, fill_color, border=True, border_weight=0.6):
    """Desenha retângulo preenchido com borda opcional."""
    c.setFillColor(fill_color)
    c.rect(x, y, w, h, fill=1, stroke=0)
    if border:
        c.setStrokeColor(BORDER_COLOR)
        c.setLineWidth(border_weight)
        c.rect(x, y, w, h, fill=0, stroke=1)


def _draw_text(c, text, x, y, font, size, color=BLACK, max_width=None):
    """Desenha texto simples. Retorna a largura usada."""
    c.setFont(font, size)
    c.setFillColor(color)
    if max_width:
        # Trunca se necessário
        while c.stringWidth(text, font, size) > max_width and len(text) > 1:
            text = text[:-1]
        if c.stringWidth(text + "...", font, size) <= max_width or len(text) < 3:
            pass
        else:
            text = text + "..."
    c.drawString(x, y, text)


def _draw_wrapped_text(c, text, x, y, font, size, max_width, line_height, max_lines=50):
    """Desenha texto com quebra de linha. Retorna y final."""
    c.setFont(font, size)
    c.setFillColor(BLACK)

    lines = []
    for paragraph in text.split("\n"):
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

    cur_y = y
    for i, line in enumerate(lines[:max_lines]):
        c.drawString(x, cur_y, line)
        cur_y -= line_height
    return cur_y


def generate_pdf(data: dict, output_dir: str = "output") -> str:
    """Gera PDF do Plano de Implantação — 1 página A4 vertical, layout idêntico ao Excel."""
    os.makedirs(output_dir, exist_ok=True)

    font_regular, font_bold = _register_fonts()

    id_interna = data.get("id_interna", "SEM_ID").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GMUD_{id_interna}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    c = canvas.Canvas(filepath, pagesize=A4)

    # ── Margens e dimensões ──────────────────────────────────────────
    MARGIN_L = 12 * mm
    MARGIN_R = 12 * mm
    MARGIN_T = 8 * mm
    MARGIN_B = 8 * mm

    FULL_W = PAGE_W - MARGIN_L - MARGIN_R     # largura total do conteúdo
    COL_A_W = FULL_W * 0.34                     # coluna label (~34%)
    COL_B_W = FULL_W - COL_A_W                  # coluna valor (~66%)

    HEADER_H = 14                               # altura cabeçalho de seção
    ROW_H = 11                                  # altura de linha label/valor
    TEXTAREA_ROW_H = 9.5                        # altura linha em textarea
    SECTION_GAP = 2                             # espaço entre seções
    TEXT_OFFSET_X = 3                            # padding horizontal do texto
    TEXT_OFFSET_Y = 3                            # padding vertical do texto (de baixo)
    HEADER_FONT_SIZE = 10
    LABEL_FONT_SIZE = 7
    VALUE_FONT_SIZE = 7
    LINE_H = 8                                  # line height para wrapped text

    x0 = MARGIN_L
    y = PAGE_H - MARGIN_T  # topo da página

    def _format_date_br(date_str: str) -> str:
        """Converte data de yyyy-mm-dd para dd/mm/yyyy (padrão brasileiro)."""
        if not date_str:
            return ""
        # Tenta vários formatos comuns
        for fmt_in, fmt_out in [
            ("%Y-%m-%d", "%d/%m/%Y"),
            ("%d/%m/%Y", "%d/%m/%Y"),   # já no formato correto
            ("%d-%m-%Y", "%d/%m/%Y"),
        ]:
            try:
                return datetime.strptime(date_str, fmt_in).strftime(fmt_out)
            except ValueError:
                continue
        return date_str  # retorna como está se não conseguir converter

    def get(key, default=""):
        val = data.get(key, default) or ""
        if key == "data_documentacao":
            val = _format_date_br(val)
        return val

    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO 1: Identificação da Mudança
    # ═══════════════════════════════════════════════════════════════════
    # Header (merged A:B)
    y -= HEADER_H
    _draw_rect(c, x0, y, FULL_W, HEADER_H, HEADER_BG, border=True, border_weight=1)
    c.setFont(font_bold, HEADER_FONT_SIZE)
    c.setFillColor(WHITE)
    text_w = c.stringWidth("1. Identificação da Mudança", font_bold, HEADER_FONT_SIZE)
    c.drawString(x0 + (FULL_W - text_w) / 2, y + TEXT_OFFSET_Y, "1. Identificação da Mudança")

    # 14 linhas de label/valor
    sec1_fields = [
        ("ID - Interna", get("id_interna")),
        ("Data documentação", get("data_documentacao")),
        ("Descrição Mudança", get("descricao_mudanca")),
        ("Solicitante", get("solicitante")),
        ("Responsável pelo Documento", get("responsavel_documento")),
        ("Responsável Técnico (Desenvolvedor)", get("responsavel_tecnico")),
        ("Responsável pela Aplicação da Mudança", get("responsavel_aplicacao")),
        ("Card(s) Jira", get("cards_jira")),
        ("Versão anterior", get("versao_anterior")),
        ("Versão atualizada", get("versao_atualizada")),
        ("Tipo da Mudança", get("tipo_mudanca")),
        ("Classificação dos Riscos", get("classificacao_riscos")),
        ("PR", get("pr")),
        ("Interdependência de Merges", get("interdependencia_merges")),
    ]

    for label, value in sec1_fields:
        y -= ROW_H
        # Label cell
        _draw_rect(c, x0, y, COL_A_W, ROW_H, LABEL_BG)
        _draw_text(c, label, x0 + TEXT_OFFSET_X, y + TEXT_OFFSET_Y,
                   font_bold, LABEL_FONT_SIZE, BLACK, COL_A_W - 2 * TEXT_OFFSET_X)
        # Value cell
        _draw_rect(c, x0 + COL_A_W, y, COL_B_W, ROW_H, VALUE_BG)
        _draw_text(c, value, x0 + COL_A_W + TEXT_OFFSET_X, y + TEXT_OFFSET_Y,
                   font_regular, VALUE_FONT_SIZE, BLACK, COL_B_W - 2 * TEXT_OFFSET_X)

    y -= SECTION_GAP

    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO 2: Descrição da Mudança
    # ═══════════════════════════════════════════════════════════════════
    y -= HEADER_H
    _draw_rect(c, x0, y, FULL_W, HEADER_H, HEADER_BG, border=True, border_weight=1)
    c.setFont(font_bold, HEADER_FONT_SIZE)
    c.setFillColor(WHITE)
    text_w = c.stringWidth("2. Descrição da Mudança", font_bold, HEADER_FONT_SIZE)
    c.drawString(x0 + (FULL_W - text_w) / 2, y + TEXT_OFFSET_Y, "2. Descrição da Mudança")

    # Label row (merged A:B no Excel, mas aqui Label na A, Valor na B)
    # No Excel: A18:A23 merged (label), B18:B23 são linhas de valor
    # Vamos reproduzir: label na esquerda (merged verticalmente), valor à direita
    sec2_rows = 5
    block_h = sec2_rows * TEXTAREA_ROW_H
    y -= block_h

    # Label cell (col A, altura total do bloco)
    _draw_rect(c, x0, y, COL_A_W, block_h, LABEL_BG)
    c.setFont(font_bold, LABEL_FONT_SIZE)
    c.setFillColor(BLACK)
    label_y = y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y
    c.drawString(x0 + TEXT_OFFSET_X, label_y, "Objetivo da Alteração")

    # Value cell (col B, altura total do bloco)
    _draw_rect(c, x0 + COL_A_W, y, COL_B_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("objetivo_alteracao"),
                       x0 + COL_A_W + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       COL_B_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec2_rows)

    y -= SECTION_GAP

    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO 3: Ambiente e Impactos
    # ═══════════════════════════════════════════════════════════════════
    y -= HEADER_H
    _draw_rect(c, x0, y, FULL_W, HEADER_H, HEADER_BG, border=True, border_weight=1)
    c.setFont(font_bold, HEADER_FONT_SIZE)
    c.setFillColor(WHITE)
    text_w = c.stringWidth("3. Ambiente e Impactos", font_bold, HEADER_FONT_SIZE)
    c.drawString(x0 + (FULL_W - text_w) / 2, y + TEXT_OFFSET_Y, "3. Ambiente e Impactos")

    # Sistemas e Servidores Envolvidos (A27:A31 merged label, B27:B31 values)
    sec3a_rows = 4
    block_h = sec3a_rows * TEXTAREA_ROW_H
    y -= block_h
    _draw_rect(c, x0, y, COL_A_W, block_h, LABEL_BG)
    c.setFont(font_bold, LABEL_FONT_SIZE)
    c.setFillColor(BLACK)
    c.drawString(x0 + TEXT_OFFSET_X, y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                 "Sistemas e Servidores Envolvidos")
    _draw_rect(c, x0 + COL_A_W, y, COL_B_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("sistemas_servidores"),
                       x0 + COL_A_W + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       COL_B_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec3a_rows)

    # Impactos Previstos (A32:A35 merged label)
    sec3b_rows = 3
    block_h = sec3b_rows * TEXTAREA_ROW_H
    y -= block_h
    _draw_rect(c, x0, y, COL_A_W, block_h, LABEL_BG)
    c.setFont(font_bold, LABEL_FONT_SIZE)
    c.setFillColor(BLACK)
    c.drawString(x0 + TEXT_OFFSET_X, y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                 "Impactos Previstos")
    _draw_rect(c, x0 + COL_A_W, y, COL_B_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("impactos_previstos"),
                       x0 + COL_A_W + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       COL_B_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec3b_rows)

    # Tempo de Indisponibilidade (A36:A38 merged label, 3 rows)
    sec3c_rows = 2
    block_h = sec3c_rows * TEXTAREA_ROW_H
    y -= block_h
    _draw_rect(c, x0, y, COL_A_W, block_h, LABEL_BG)
    c.setFont(font_bold, LABEL_FONT_SIZE)
    c.setFillColor(BLACK)
    c.drawString(x0 + TEXT_OFFSET_X, y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                 "Tempo de Indisponibilidade")
    _draw_rect(c, x0 + COL_A_W, y, COL_B_W, block_h, VALUE_BG)
    c.setFont(font_regular, VALUE_FONT_SIZE)
    c.setFillColor(BLACK)
    c.drawString(x0 + COL_A_W + TEXT_OFFSET_X,
                 y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                 get("tempo_indisponibilidade"))

    y -= SECTION_GAP

    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO 4: Escopo Técnico
    # ═══════════════════════════════════════════════════════════════════
    y -= HEADER_H
    _draw_rect(c, x0, y, FULL_W, HEADER_H, HEADER_BG, border=True, border_weight=1)
    c.setFont(font_bold, HEADER_FONT_SIZE)
    c.setFillColor(WHITE)
    text_w = c.stringWidth("4. Escopo Técnico", font_bold, HEADER_FONT_SIZE)
    c.drawString(x0 + (FULL_W - text_w) / 2, y + TEXT_OFFSET_Y, "4. Escopo Técnico")

    # Escopo técnico Aplicado (A41:A47 = 7 rows)
    sec4a_rows = 5
    block_h = sec4a_rows * TEXTAREA_ROW_H
    y -= block_h
    _draw_rect(c, x0, y, COL_A_W, block_h, LABEL_BG)
    c.setFont(font_bold, LABEL_FONT_SIZE)
    c.setFillColor(BLACK)
    c.drawString(x0 + TEXT_OFFSET_X, y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                 "Escopo técnico Aplicado")
    _draw_rect(c, x0 + COL_A_W, y, COL_B_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("escopo_tecnico"),
                       x0 + COL_A_W + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       COL_B_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec4a_rows)

    # Regras aplicadas (A48:A50 = 3 rows)
    sec4b_rows = 2
    block_h = sec4b_rows * TEXTAREA_ROW_H
    y -= block_h
    _draw_rect(c, x0, y, COL_A_W, block_h, LABEL_BG)
    c.setFont(font_bold, LABEL_FONT_SIZE)
    c.setFillColor(BLACK)
    c.drawString(x0 + TEXT_OFFSET_X, y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                 "Regras aplicadas")
    _draw_rect(c, x0 + COL_A_W, y, COL_B_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("regras_aplicadas"),
                       x0 + COL_A_W + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       COL_B_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec4b_rows)

    # Alterações em estruturas (A51:A57 = 7 rows)
    sec4c_rows = 5
    block_h = sec4c_rows * TEXTAREA_ROW_H
    y -= block_h
    _draw_rect(c, x0, y, COL_A_W, block_h, LABEL_BG)
    c.setFont(font_bold, LABEL_FONT_SIZE)
    c.setFillColor(BLACK)
    c.drawString(x0 + TEXT_OFFSET_X, y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                 "Alterações em estruturas")
    _draw_rect(c, x0 + COL_A_W, y, COL_B_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("alteracoes_estruturas"),
                       x0 + COL_A_W + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       COL_B_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec4c_rows)

    y -= SECTION_GAP

    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO 5: Plano de Implementação
    # ═══════════════════════════════════════════════════════════════════
    y -= HEADER_H
    _draw_rect(c, x0, y, FULL_W, HEADER_H, HEADER_BG, border=True, border_weight=1)
    c.setFont(font_bold, HEADER_FONT_SIZE)
    c.setFillColor(WHITE)
    text_w = c.stringWidth("5. Plano de Implementação", font_bold, HEADER_FONT_SIZE)
    c.drawString(x0 + (FULL_W - text_w) / 2, y + TEXT_OFFSET_Y, "5. Plano de Implementação")

    # Texto livre (rows 60-75 = 16 rows merged A:B)
    sec5_rows = 12
    block_h = sec5_rows * TEXTAREA_ROW_H
    y -= block_h
    _draw_rect(c, x0, y, FULL_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("plano_implementacao"),
                       x0 + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       FULL_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec5_rows)

    y -= SECTION_GAP

    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO 6: Plano de Rollback
    # ═══════════════════════════════════════════════════════════════════
    y -= HEADER_H
    _draw_rect(c, x0, y, FULL_W, HEADER_H, HEADER_BG, border=True, border_weight=1)
    c.setFont(font_bold, HEADER_FONT_SIZE)
    c.setFillColor(WHITE)
    text_w = c.stringWidth("6. Plano de Rollback", font_bold, HEADER_FONT_SIZE)
    c.drawString(x0 + (FULL_W - text_w) / 2, y + TEXT_OFFSET_Y, "6. Plano de Rollback")

    # Texto livre (rows 77-91 = 15 rows merged A:B)
    sec6_rows = 12
    block_h = sec6_rows * TEXTAREA_ROW_H
    y -= block_h
    _draw_rect(c, x0, y, FULL_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("plano_rollback"),
                       x0 + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       FULL_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec6_rows)

    y -= SECTION_GAP

    # ═══════════════════════════════════════════════════════════════════
    # SEÇÃO 7: Validação após mudança
    # ═══════════════════════════════════════════════════════════════════
    y -= HEADER_H
    _draw_rect(c, x0, y, FULL_W, HEADER_H, HEADER_BG, border=True, border_weight=1)
    c.setFont(font_bold, HEADER_FONT_SIZE)
    c.setFillColor(WHITE)
    text_w = c.stringWidth("7. Validação após mudança", font_bold, HEADER_FONT_SIZE)
    c.drawString(x0 + (FULL_W - text_w) / 2, y + TEXT_OFFSET_Y, "7. Validação após mudança")

    # Texto livre (rows 93-106 = 14 rows merged A:B)
    # Usar o espaço restante até a margem inferior
    remaining_h = y - MARGIN_B
    sec7_rows = max(3, int(remaining_h / TEXTAREA_ROW_H))
    block_h = remaining_h
    y -= block_h
    _draw_rect(c, x0, y, FULL_W, block_h, VALUE_BG)
    _draw_wrapped_text(c, get("validacao_pos_mudanca"),
                       x0 + TEXT_OFFSET_X,
                       y + block_h - TEXTAREA_ROW_H + TEXT_OFFSET_Y,
                       font_regular, VALUE_FONT_SIZE,
                       FULL_W - 2 * TEXT_OFFSET_X, LINE_H, max_lines=sec7_rows)

    c.save()
    return filepath
