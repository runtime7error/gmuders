"""
App FastAPI - Gerador de PDF Plano de Implantação (GMUD)

Rotas:
  GET  /                 → Formulário web
  POST /gerar-pdf        → Submissão do formulário (form-data)
  POST /api/gerar-pdf    → API REST (JSON)
  GET  /output/{file}    → Download do PDF gerado
"""

import os
import sys
import base64
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from pdf_generator import generate_pdf

app = FastAPI(title="GMUD - Gerador de Plano de Implantação")

# Quando empacotado com PyInstaller, os assets ficam em sys._MEIPASS
# O output fica sempre ao lado do executável (não dentro do temp)
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BUNDLE_DIR

OUTPUT_DIR = os.path.join(EXE_DIR, "output")

app.mount("/static", StaticFiles(directory=os.path.join(BUNDLE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BUNDLE_DIR, "templates"))


# ---------------------------------------------------------------------------
# Modelo de dados para a API
# ---------------------------------------------------------------------------
class GmudData(BaseModel):
    id_interna: Optional[str] = ""
    data_documentacao: Optional[str] = ""
    descricao_mudanca: Optional[str] = ""
    solicitante: Optional[str] = ""
    responsavel_documento: Optional[str] = ""
    responsavel_tecnico: Optional[str] = ""
    responsavel_aplicacao: Optional[str] = ""
    cards_jira: Optional[str] = ""
    versao_anterior: Optional[str] = ""
    versao_atualizada: Optional[str] = ""
    tipo_mudanca: Optional[str] = ""
    classificacao_riscos: Optional[str] = ""
    pr: Optional[str] = ""
    interdependencia_merges: Optional[str] = ""
    objetivo_alteracao: Optional[str] = ""
    sistemas_servidores: Optional[str] = ""
    impactos_previstos: Optional[str] = ""
    tempo_indisponibilidade: Optional[str] = ""
    escopo_tecnico: Optional[str] = ""
    regras_aplicadas: Optional[str] = ""
    alteracoes_estruturas: Optional[str] = ""
    plano_implementacao: Optional[str] = ""
    plano_rollback: Optional[str] = ""
    validacao_pos_mudanca: Optional[str] = ""


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Exibe o formulário web."""
    today = datetime.now().strftime("%Y-%m-%d")
    return templates.TemplateResponse(request=request, name="index.html", context={"today": today})


@app.post("/gerar-pdf")
async def gerar_pdf_form(
    request: Request,
    id_interna: str = Form(""),
    data_documentacao: str = Form(""),
    descricao_mudanca: str = Form(""),
    solicitante: str = Form(""),
    responsavel_documento: str = Form(""),
    responsavel_tecnico: str = Form(""),
    responsavel_aplicacao: str = Form(""),
    cards_jira: str = Form(""),
    versao_anterior: str = Form(""),
    versao_atualizada: str = Form(""),
    tipo_mudanca: str = Form(""),
    classificacao_riscos: str = Form(""),
    pr: str = Form(""),
    interdependencia_merges: str = Form(""),
    objetivo_alteracao: str = Form(""),
    sistemas_servidores: str = Form(""),
    impactos_previstos: str = Form(""),
    tempo_indisponibilidade: str = Form(""),
    escopo_tecnico: str = Form(""),
    regras_aplicadas: str = Form(""),
    alteracoes_estruturas: str = Form(""),
    plano_implementacao: str = Form(""),
    plano_rollback: str = Form(""),
    validacao_pos_mudanca: str = Form(""),
):
    """Recebe dados do formulário web e gera o PDF."""
    data = {
        "id_interna": id_interna,
        "data_documentacao": data_documentacao,
        "descricao_mudanca": descricao_mudanca,
        "solicitante": solicitante,
        "responsavel_documento": responsavel_documento,
        "responsavel_tecnico": responsavel_tecnico,
        "responsavel_aplicacao": responsavel_aplicacao,
        "cards_jira": cards_jira,
        "versao_anterior": versao_anterior,
        "versao_atualizada": versao_atualizada,
        "tipo_mudanca": tipo_mudanca,
        "classificacao_riscos": classificacao_riscos,
        "pr": pr,
        "interdependencia_merges": interdependencia_merges,
        "objetivo_alteracao": objetivo_alteracao,
        "sistemas_servidores": sistemas_servidores,
        "impactos_previstos": impactos_previstos,
        "tempo_indisponibilidade": tempo_indisponibilidade,
        "escopo_tecnico": escopo_tecnico,
        "regras_aplicadas": regras_aplicadas,
        "alteracoes_estruturas": alteracoes_estruturas,
        "plano_implementacao": plano_implementacao,
        "plano_rollback": plano_rollback,
        "validacao_pos_mudanca": validacao_pos_mudanca,
    }

    filepath = generate_pdf(data, OUTPUT_DIR)
    filename = os.path.basename(filepath)

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/gerar-pdf")
async def gerar_pdf_api(payload: GmudData):
    """API REST: recebe JSON e gera o PDF."""
    data = payload.model_dump()
    filepath = generate_pdf(data, OUTPUT_DIR)
    filename = os.path.basename(filepath)

    return JSONResponse(
        content={
            "status": "success",
            "filename": filename,
            "download_url": f"/output/{filename}",
        }
    )


@app.post("/api/gerar-pdf-base64")
async def gerar_pdf_base64_api(payload: GmudData):
    """API REST: recebe JSON, gera o PDF e retorna em base64 (útil para Jira Forge)."""
    data = payload.model_dump()
    filepath = generate_pdf(data, OUTPUT_DIR)
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    return JSONResponse(
        content={
            "status": "success",
            "filename": filename,
            "pdf_base64": pdf_base64,
        }
    )


@app.get("/output/{filename}")
async def download_pdf(filename: str):
    """Serve o PDF gerado para download."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Arquivo não encontrado"},
        )
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename,
    )
