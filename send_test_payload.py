import requests
import json
import base64
from pdf_generator import generate_pdf

# 1. Dados de exemplo da GMUD
payload = {
    "id_interna": "KAN-123",
    "data_documentacao": "2026-08-06",
    "descricao_mudanca": "Migração do Relatório de Pesagem ATM-056",
    "solicitante": "Lucas Nascimento",
    "responsavel_documento": "Lucas Nascimento",
    "responsavel_tecnico": "Lucas Nascimento",
    "responsavel_aplicacao": "Equipe DevOps",
    "cards_jira": "KAN-123",
    "pr": "https://github.com/empresa/repo/pull/123",
    "versao_anterior": "2.17.17",
    "versao_atualizada": "2.17.18",
    "tipo_mudanca": "Normal",
    "classificacao_riscos": "Baixo",
    "interdependencia_merges": "Sem dependências de outros merges",
    "objetivo_alteracao": "Refatorar a query de pesagem para otimizar tempo de execução do relatório ATM-056.",
    "sistemas_servidores": "ElisConnect Central, Módulo de Relatórios, SSRS Viewer",
    "impactos_previstos": "Nenhum impacto previsto durante a aplicação.",
    "tempo_indisponibilidade": "Sem indisponibilidade",
    "escopo_tecnico": "Refatoração de rotinas de banco de dados e atualização de pacotes.",
    "regras_aplicadas": "Validação de limites de tolerância de peso entregue.",
    "alteracoes_estruturas": "Nenhuma alteração de tabela em banco de dados.",
    "plano_implementacao": "1. Executar script de atualização se houver.\n2. Deploy do pacote 2.17.18 no ambiente de produção.\n3. Validar acesso aos relatórios.",
    "plano_rollback": "1. Realizar a reversão do deploy para a versão 2.17.17.\n2. Validar estabilidade dos relatórios.",
    "validacao_pos_mudanca": "1. Executar testes funcionais no ambiente.\n2. Confirmar dados de pesagem exibidos no relatório.",
    "email": "lnascimento8@elis.com.br",
    "data_implementacao": "2026-08-12",
    "departamento": "Tecnologia / Desenvolvimento"
}

print("1. Gerando o arquivo PDF de teste...")
filename, pdf_bytes = generate_pdf(payload)
pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
payload["pdf_base64"] = pdf_b64
payload["filename"] = filename

webhook_url = "https://default7b3c007331d44dfd8d4d122bd10aab.6b.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/06/workflows/d913c2a72f994253a698f3e5a2ce98d0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=vEBXCQj-T-4Ui6MMN5K_AfCFoljs-1k9pq7ZCS77vZU"

print(f"2. Enviando JSON + PDF Base64 para a URL do Power Automate...")
headers = {"Content-Type": "application/json"}
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
res = requests.post(webhook_url, json=payload, headers=headers, verify=False)

print(f"\nStatus do Power Automate: {res.status_code}")
print(f"Resposta do Power Automate: {res.text}")
