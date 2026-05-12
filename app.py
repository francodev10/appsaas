import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar PNCP Pro", layout="wide", page_icon="🏛️")

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
st.markdown("""
    <style>
    .licitacao-card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e6e9ef;
        margin-bottom: 20px;
        background-color: #f8f9fa;
    }
    .status-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE BUSCA ---
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

def formatar_data_br(dt_str):
    if not dt_str: return None
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except:
        return None

# --- GERADOR DE LINK GOOGLE CALENDAR ---
def gerar_link_google_calendar(titulo, objeto, data_fim, url_edital):
    # Se não houver data fim, agendamos para 1h após a abertura ou momento atual
    if not data_fim:
        data_fim = datetime.now() + timedelta(hours=1)
    
    data_fmt = data_fim.strftime("%Y%m%dT%H%M%SZ")
    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    detalhes = f"Objeto: {objeto}\n\nLink: {url_edital}"
    params = {
        "text": f"📌 PRAZO: {titulo[:50]}...",
        "dates": f"{data_fmt}/{data_fmt}",
        "details": detalhes,
        "sf": "true",
        "output": "xml"
    }
    return base_url + "&" + urllib.parse.urlencode(params)

# --- INTERFACE ---
st.title("🏛️ Radar de Oportunidades PNCP")
st.caption("Versão Cloud - Filtre por região e agende no seu Google Calendar")

# Sidebar
st.sidebar.header("Filtros")
termo = st.sidebar.text_input("Palavra-chave (ex: TI, Limpeza)")
uf_sel = st.sidebar.selectbox("Estado (UF)", ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
data_sel = st.sidebar.date_input("Data de Publicação", datetime.now())
m6 = st.sidebar.checkbox("Dispensa (6)", value=True)
m8 = st.sidebar.checkbox("Pregão (8)", value=True)

if st.sidebar.button("🔍 Iniciar Busca"):
    modalidades = []
    if m6: modalidades.append(6)
    if m8: modalidades.append(8)
    
    with st.spinner("Extraindo dados do PNCP..."):
        dados = buscar_pncp(termo, modalidades, data_sel.strftime("%Y%m%d"), uf_sel)
        
        if dados:
            st.write(f"### Encontradas {len(dados)} oportunidades")
            
            for index, item in enumerate(dados):
                orgao = item['orgaoEntidade']['razaoSocial']
                objeto = item['objetoCompra']
                link_edital = f"https://pncp.gov.br/app/editais/{item['orgaoEntidade']['cnpj']}/{item['anoCompra']}/{item['sequencialCompra']}"
                plataforma = item.get('nomeFonteSincronizacao', 'PNCP')
                modalidade_nome = item.get('modalidadeNome', 'N/A')
                
                # Datas
                dt_pub = formatar_data_br(item.get('dataPublicacao'))
                dt_abert = formatar_data_br(item.get('dataAberturaPropostas'))
                dt_fim = formatar_data_br(item.get('dataEncerramentoPropostas'))

                # Renderização do Card sem Expander
                with st.container():
                    st.markdown(f"#### 🏢 {orgao}")
                    
                    col_info, col_btn = st.columns([4, 1])
                    
                    with col_info:
                        st.write(f"**📝 Objeto:** {objeto}")
                        st.write(f"**⚖️ Modalidade:** {modalidade_nome} | **🌐 Plataforma:** {plataforma}")
                        
                        # Linha de Datas
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"📅 **Publicação:**\n{dt_pub.strftime('%d/%m/%Y') if dt_pub else '-'}")
                        c2.write(f"🚀 **Abertura:**\n{dt_abert.strftime('%d/%m/%Y %H:%M') if dt_abert else '-'}")
                        c3.markdown(f"⌛ **Encerramento:**\n<span style='color:red; font-weight:bold;'>{dt_fim.strftime('%d/%m/%Y %H:%M') if dt_fim else 'Não informado'}</span>", unsafe_allow_html=True)
                    
                    with col_btn:
                        st.link_button("📄 Ver Edital", link_edital, use_container_width=True)
                        
                        # Geração do Botão de Agendar
                        link_google = gerar_link_google_calendar(orgao, objeto, dt_fim, link_edital)
                        st.link_button("📅 Agendar Google", link_google, use_container_width=True, type="primary")
                    
                    st.divider()
        else:
            st.info("Nenhuma oportunidade encontrada para os filtros aplicados.")
