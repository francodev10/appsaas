import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SaaS PNCP Pro", layout="wide", page_icon="🏛️")

# --- LÓGICA DE BUSCA (BACKEND INTEGRADO) ---
def buscar_pncp(termo, modalidades, data_alvo, uf):
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    params = {
        "pagina": 1,
        "tamanhoPagina": 50,
        "dataInicial": data_alvo,
        "dataFinal": data_alvo,
        "codigoModalidadeContratacao": modalidades,
        "termoBusca": termo,
        "uf": uf if uf else None
    }
    try:
        res = requests.get(url, params=params, timeout=20)
        res.raise_for_status()
        return res.json().get("data", [])
    except:
        return []

def formatar_data(dt_str):
    if not dt_str: return None
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except:
        return None

# --- GERADOR DE LINK DO GOOGLE CALENDAR ---
def gerar_link_google_calendar(titulo, descricao, data_fechamento, url_edital):
    if not data_fechamento:
        return None
    
    # Formato Google: YYYYMMDDTHHMMSSZ
    data_fmt = data_fechamento.strftime("%Y%m%dT%H%M%SZ")
    
    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    params = {
        "text": f"🚨 PRAZO PNCP: {titulo}",
        "dates": f"{data_fmt}/{data_fmt}",
        "details": f"Objeto: {descricao}\n\nLink do Edital: {url_edital}",
        "location": "Portal PNCP",
        "sf": "true",
        "output": "xml"
    }
    return base_url + "&" + urllib.parse.urlencode(params)

# --- INTERFACE ---
st.title("🏛️ Inteligência PNCP (Cloud Edition)")
st.markdown("Busque oportunidades e agende prazos diretamente no seu Google Calendar.")

st.sidebar.header("Filtros de Busca")
termo = st.sidebar.text_input("Palavra-chave")
uf_sel = st.sidebar.selectbox("Estado (UF)", ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
data_sel = st.sidebar.date_input("Data de Publicação", datetime.now())
m6 = st.sidebar.checkbox("Dispensa (6)", value=True)
m8 = st.sidebar.checkbox("Pregão (8)", value=True)

if st.sidebar.button("🔍 Pesquisar"):
    modalidades = []
    if m6: modalidades.append(6)
    if m8: modalidades.append(8)
    
    with st.spinner("Consultando base do governo..."):
        dados_brutos = buscar_pncp(termo, modalidades, data_sel.strftime("%Y%m%d"), uf_sel)
        
        if dados_brutos:
            st.success(f"Encontradas {len(dados_brutos)} oportunidades!")
            for item in dados_brutos:
                orgao = item['orgaoEntidade']['razaoSocial']
                objeto = item['objetoCompra']
                dt_fim = formatar_data(item.get('dataEncerramentoPropostas'))
                link_edital = f"https://pncp.gov.br/app/editais/{item['orgaoEntidade']['cnpj']}/{item['anoCompra']}/{item['sequencialCompra']}"
                
                with st.expander(f"🏢 {orgao}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Objeto:** {objeto}")
                        st.write(f"⌛ **Encerramento:** {dt_fim.strftime('%d/%m/%Y %H:%M') if dt_fim else 'Não informado'}")
                    with col2:
                        st.link_button("📄 Ver Edital", link_edital, use_container_width=True)
                        
                        # BOTÃO DO GOOGLE CALENDAR
                        if dt_fim:
                            link_cal = gerar_link_google_calendar(orgao, objeto, dt_fim, link_edital)
                            st.link_button("📅 Agendar Google", link_cal, use_container_width=True, type="primary")
        else:
            st.info("Nenhum edital encontrado.")
        