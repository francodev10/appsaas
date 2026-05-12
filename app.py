import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar PNCP SaaS", layout="wide")

# --- CUSTOMIZAÇÃO ESTÉTICA (CSS) ---
# Fundo preto, letras amarelas e fontes menores
st.markdown("""
    <style>
    /* Fundo principal e Sidebar */
    .stApp, [data-testid="stSidebar"] {
        background-color: #000000 !important;
        color: #FFFF00 !important;
    }
    
    /* Textos, Títulos e Labels */
    h1, h2, h3, h4, p, span, label, .stMarkdown {
        color: #FFFF00 !important;
        font-size: 14px !important;
    }
    
    /* Inputs e Selectboxes */
    .stTextInput input, .stSelectbox div, .stDateInput input {
        background-color: #111 !important;
        color: #FFFF00 !important;
        border: 1px solid #FFFF00 !important;
        font-size: 13px !important;
    }

    /* Cards de Licitação */
    .licitacao-box {
        border: 1px solid #FFFF00;
        padding: 10px;
        margin-bottom: 15px;
        border-radius: 5px;
    }

    /* Botões */
    .stButton button {
        background-color: #000 !important;
        color: #FFFF00 !important;
        border: 1px solid #FFFF00 !important;
        width: 100%;
        font-size: 12px !important;
    }
    .stButton button:hover {
        background-color: #FFFF00 !important;
        color: #000 !important;
    }

    /* Links de botões (Ver Edital e Agendar) */
    a {
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA (Lógica de Múltiplas Modalidades) ---
def buscar_pncp(termo, modalidades, data_alvo, uf):
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    
    # Lista de tuplas para permitir chaves repetidas na URL (Necessário para a API PNCP)
    params = [
        ('pagina', 1),
        ('tamanhoPagina', 50),
        ('dataInicial', data_alvo),
        ('dataFinal', data_alvo),
    ]
    
    if termo:
        params.append(('termoBusca', termo))
    if uf:
        params.append(('uf', uf))
    
    for mod in modalidades:
        params.append(('codigoModalidadeContratacao', mod))

    try:
        res = requests.get(url, params=params, timeout=25)
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

def gerar_link_google(titulo, objeto, data_fim, link):
    if not data_fim:
        data_fim = datetime.now() + timedelta(days=1)
    data_fmt = data_fim.strftime("%Y%m%dT%H%M%SZ")
    params = {
        "action": "TEMPLATE",
        "text": f"PNCP: {titulo[:40]}",
        "dates": f"{data_fmt}/{data_fmt}",
        "details": f"Objeto: {objeto}\nLink: {link}",
        "sf": "true"
    }
    return "https://www.google.com/calendar/render?" + urllib.parse.urlencode(params)

# --- INTERFACE ---
st.title("RADAR PNCP - MODO TERMINAL")

# Sidebar
st.sidebar.markdown("### FILTROS")
termo_input = st.sidebar.text_input("BUSCA")
uf_input = st.sidebar.selectbox("UF", ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
data_input = st.sidebar.date_input("DATA", datetime.now())

m6 = st.sidebar.checkbox("DISPENSA (6)", value=True)
m8 = st.sidebar.checkbox("PREGÃO (8)", value=True)

if st.sidebar.button("EXECUTAR BUSCA"):
    mods = []
    if m6: mods.append(6)
    if m8: mods.append(8)
    
    with st.spinner("CARREGANDO..."):
        resultados = buscar_pncp(termo_input, mods, data_input.strftime("%Y%m%d"), uf_input)
        
        if resultados:
            st.markdown(f"RESULTADOS: {len(resultados)}")
            
            for item in resultados:
                orgao = item['orgaoEntidade']['razaoSocial']
                objeto = item['objetoCompra']
                link = f"https://pncp.gov.br/app/editais/{item['orgaoEntidade']['cnpj']}/{item['anoCompra']}/{item['sequencialCompra']}"
                dt_fim = formatar_data(item.get('dataEncerramentoPropostas'))
                dt_abert = formatar_data(item.get('dataAberturaPropostas'))

                # Card de Informação com estilo "Terminal"
                st.markdown(f"""
                <div class="licitacao-box">
                    <strong>ORGÃO:</strong> {orgao}<br>
                    <strong>OBJETO:</strong> {objeto}<br>
                    <strong>ABERTURA:</strong> {dt_abert.strftime('%d/%m/%Y %H:%M') if dt_abert else '---'} | 
                    <strong>FIM:</strong> {dt_fim.strftime('%d/%m/%Y %H:%M') if dt_fim else '---'}
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, _ = st.columns([1, 1, 2])
                with col1:
                    st.link_button("EDITAL", link)
                with col2:
                    url_cal = gerar_link_google(orgao, objeto, dt_fim, link)
                    st.link_button("AGENDAR", url_cal)
                
                st.markdown("---")
        else:
            st.markdown("NENHUM DADO ENCONTRADO.")
