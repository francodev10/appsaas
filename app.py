import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Terminal PNCP", layout="wide")

# --- CSS: ESTILO TERMINAL (PRETO E AMARELO) ---
st.markdown("""
    <style>
    /* Reset de Cores Principal */
    .stApp, [data-testid="stSidebar"], div[data-testid="stToolbar"] {
        background-color: #000000 !important;
        color: #FFFF00 !important;
    }
    
    /* Textos Gerais e Labels */
    h1, h2, h3, h4, h5, h6, p, span, label, li, .stMarkdown {
        color: #FFFF00 !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 13px !important;
    }

    /* Inputs e Selectboxes */
    input, div[data-baseweb="select"], div[data-baseweb="input"] {
        background-color: #111 !important;
        color: #FFFF00 !important;
        border: 1px solid #FFFF00 !important;
    }

    /* Cards de Resultados */
    .result-card {
        border: 1px solid #FFFF00;
        padding: 8px;
        margin-bottom: 10px;
        background-color: #000;
    }

    /* Botões */
    .stButton button {
        background-color: #000 !important;
        color: #FFFF00 !important;
        border: 1px solid #FFFF00 !important;
        font-size: 11px !important;
        font-weight: bold;
        text-transform: uppercase;
    }
    .stButton button:hover {
        background-color: #FFFF00 !important;
        color: #000 !important;
    }
    
    /* Divider */
    hr { border-top: 1px solid #FFFF00 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA ROBUSTA ---
def buscar_dados_pncp(termo, modalidades, data_alvo, uf):
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    
    # Montagem correta dos parâmetros para múltiplas modalidades
    query_params = [
        ('pagina', 1),
        ('tamanhoPagina', 50),
        ('dataInicial', data_alvo),
        ('dataFinal', data_alvo),
    ]
    
    if termo and termo.strip():
        query_params.append(('termoBusca', termo.strip()))
    
    if uf and uf.strip():
        query_params.append(('uf', uf.strip()))
    
    # A API exige a repetição da chave para cada modalidade selecionada
    for mod in modalidades:
        query_params.append(('codigoModalidadeContratacao', mod))

    try:
        # O segredo para o filtro funcionar é passar a lista de tuplas no params
        response = requests.get(url, params=query_params, timeout=20)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        st.error(f"ERRO API: {e}")
        return []

def format_dt(dt_str):
    if not dt_str: return "---"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return dt_str[:10]

def link_google(titulo, objeto, dt_fim_str, url):
    # Tenta converter a string de volta para data para o link
    try:
        if dt_fim_str == "---":
            dt_base = datetime.now() + timedelta(days=1)
        else:
            dt_base = datetime.strptime(dt_fim_str, "%d/%m/%Y %H:%M")
    except:
        dt_base = datetime.now() + timedelta(days=1)
        
    dt_fmt = dt_base.strftime("%Y%m%dT%H%M%SZ")
    p = {
        "action": "TEMPLATE",
        "text": f"LIMITE: {titulo[:50]}",
        "dates": f"{dt_fmt}/{dt_fmt}",
        "details": f"OBJETO: {objeto}\nLINK: {url}",
        "sf": "true"
    }
    return "https://www.google.com/calendar/render?" + urllib.parse.urlencode(p)

# --- INTERFACE ---
st.title("RADAR PNCP v4.0 - TERMINAL MODE")

# Sidebar Filtros
st.sidebar.markdown("### FILTROS_SISTEMA")
termo_in = st.sidebar.text_input("TERMO_BUSCA")
uf_in = st.sidebar.selectbox("UF_REGIAO", ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
data_in = st.sidebar.date_input("DATA_REF", datetime.now())

st.sidebar.markdown("---")
m6 = st.sidebar.checkbox("DISPENSA (6)", value=True)
m8 = st.sidebar.checkbox("PREGAO (8)", value=True)

if st.sidebar.button("EXECUTAR_QUERY"):
    sel_mods = []
    if m6: sel_mods.append(6)
    if m8: sel_mods.append(8)
    
    if not sel_mods:
        st.warning("SELECIONE UMA MODALIDADE")
    else:
        with st.spinner("PROCESSANDO..."):
            resultados = buscar_dados_pncp(termo_in, sel_mods, data_in.strftime("%Y%m%d"), uf_in)
            
            if resultados:
                st.markdown(f"**DATA_FOUND:** {len(resultados)} REGISTROS")
                st.divider()
                
                for item in resultados:
                    # Extração de campos
                    orgao = item['orgaoEntidade']['razaoSocial']
                    objeto = item['objetoCompra']
                    cnpj = item['orgaoEntidade']['cnpj']
                    ano = item['anoCompra']
                    seq = item['sequencialCompra']
                    link_edital = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
                    
                    # Datas (Formatadas para exibição)
                    fechamento = format_dt(item.get('dataEncerramentoPropostas'))
                    abertura = format_dt(item.get('dataAberturaPropostas'))
                    
                    # Layout Terminal
                    st.markdown(f"""
                    <div class="result-card">
                        <b>ORGAO:</b> {orgao}<br>
                        <b>OBJETO:</b> {objeto}<br>
                        <b>ABERTURA:</b> {abertura} | <b>FECHAMENTO:</b> {fechamento}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, _ = st.columns([1, 1, 3])
                    with c1:
                        st.link_button("EDITAL", link_edital)
                    with c2:
                        url_cal = link_google(orgao, objeto, fechamento, link_edital)
                        st.link_button("AGENDAR", url_cal)
            else:
                st.error("ZERO_RESULTS: NADA ENCONTRADO PARA OS FILTROS.")
