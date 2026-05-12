import streamlit as st
import requests
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Terminal PNCP v5", layout="wide")

# --- CSS: ESTILO TERMINAL AMARELO E PRETO ---
st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"] {
        background-color: #000000 !important;
        color: #FFFF00 !important;
    }
    * {
        color: #FFFF00 !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 12px !important;
    }
    input, div[data-baseweb="select"], div[data-baseweb="input"], .stSelectbox {
        background-color: #000 !important;
        color: #FFFF00 !important;
        border: 1px solid #FFFF00 !important;
    }
    .result-card {
        border: 1px solid #FFFF00;
        padding: 10px;
        margin-bottom: 15px;
        background-color: #000;
    }
    .stButton button {
        background-color: #000 !important;
        color: #FFFF00 !important;
        border: 1px solid #FFFF00 !important;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #FFFF00 !important;
        color: #000 !important;
    }
    hr { border-top: 1px solid #FFFF00 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA CORRIGIDA ---
def buscar_dados(termo, modalidades, data_alvo, uf):
    # Endpoint oficial de contratações do PNCP
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    
    # Parâmetros base
    params = [
        ('pagina', 1),
        ('tamanhoPagina', 50),
        ('dataInicial', data_alvo),
        ('dataFinal', data_alvo)
    ]
    
    # Adiciona termo apenas se tiver conteúdo (PNCP costuma exigir min. 3 caracteres)
    if termo and len(termo.strip()) >= 3:
        params.append(('termoBusca', termo.strip()))
    
    if uf:
        params.append(('uf', uf))
        
    # Adiciona cada modalidade separadamente (Obrigatório para API do PNCP)
    for mod in modalidades:
        params.append(('codigoModalidadeContratacao', mod))

    try:
        # Enviamos params como lista de tuplas para suportar chaves repetidas
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        st.error(f"ERRO_CONEXAO: {e}")
        return []

def parse_data(iso_str):
    if not iso_str: return "---"
    try:
        # Limpa o sufixo Z ou +0000 para converter
        clean_str = iso_str.split('.')[0].replace('Z', '')
        dt = datetime.fromisoformat(clean_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return iso_str[:10]

def gerar_link_google(titulo, objeto, data_fim_str, url_edital):
    # Tenta extrair a data para o calendário, se falhar usa amanhã
    try:
        dt_obj = datetime.strptime(data_fim_str, "%d/%m/%Y %H:%M")
    except:
        dt_obj = datetime.now() + timedelta(days=1)
        
    dt_cal = dt_obj.strftime("%Y%m%dT%H%M%SZ")
    p = {
        "action": "TEMPLATE",
        "text": f"LIMITE PNCP: {titulo[:50]}",
        "dates": f"{dt_cal}/{dt_cal}",
        "details": f"OBJETO: {objeto}\nLINK: {url_edital}",
        "sf": "true"
    }
    return "https://www.google.com/calendar/render?" + urllib.parse.urlencode(p)

# --- INTERFACE ---
st.title("RADAR PNCP v5.0 - SISTEMA TERMINAL")

# Filtros na Sidebar
st.sidebar.markdown("### FILTROS_ENTRADA")
termo_in = st.sidebar.text_input("TERMO_PESQUISA (MIN 3 CHARS)")
uf_in = st.sidebar.selectbox("UF_LOCALIDADE", ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
data_in = st.sidebar.date_input("DATA_PUBLICACAO", datetime.now())

m6 = st.sidebar.checkbox("DISPENSA (6)", value=True)
m8 = st.sidebar.checkbox("PREGAO (8)", value=True)

if st.sidebar.button("EXECUTAR_QUERY"):
    mods = []
    if m6: mods.append(6)
    if m8: mods.append(8)
    
    with st.spinner("QUERYING_DATABASE..."):
        data_str = data_in.strftime("%Y%m%d")
        resultados = buscar_dados(termo_in, mods, data_str, uf_in)
        
        if resultados:
            st.markdown(f"**ENCONTRADOS:** {len(resultados)} REGISTROS")
            st.divider()
            
            for item in resultados:
                # Extração segura de campos
                razao = item.get('orgaoEntidade', {}).get('razaoSocial', 'DESCONHECIDO')
                obj_compra = item.get('objetoCompra', 'SEM_DESCRICAO')
                cnpj = item.get('orgaoEntidade', {}).get('cnpj')
                ano = item.get('anoCompra')
                seq = item.get('sequencialCompra')
                link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
                
                # Datas (Abertura e Fechamento)
                # O PNCP usa campos específicos: dataAberturaPropostas e dataEncerramentoPropostas
                dt_abertura = parse_data(item.get('dataAberturaPropostas'))
                dt_fechamento = parse_data(item.get('dataEncerramentoPropostas'))
                
                # Exibição Terminal
                st.markdown(f"""
                <div class="result-card">
                    <b>ORGAO:</b> {razao}<br>
                    <b>OBJETO:</b> {obj_compra}<br>
                    <b>ABERTURA:</b> {dt_abertura} | <b>FECHAMENTO:</b> {dt_fechamento}
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, _ = st.columns([1, 1, 3])
                with c1:
                    st.link_button("EDITAL", link)
                with c2:
                    link_cal = gerar_link_google(razao, obj_compra, dt_fechamento, link)
                    st.link_button("AGENDAR", link_cal)
        else:
            st.error("ZERO_RESULTS: TENTE OUTRO TERMO OU DATA.")
