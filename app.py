import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar PNCP SaaS", layout="wide", page_icon="🏛️")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .data-box {
        background-color: #f1f3f5;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA CORRIGIDA ---
def buscar_pncp(termo, modalidades, data_alvo, uf):
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    
    # Construção manual dos parâmetros para garantir que modalidades múltiplas funcionem
    # A API do PNCP exige repetição da chave para listas
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
    
    # Adiciona cada modalidade individualmente (Resolve o problema de trazer apenas uma)
    for mod in modalidades:
        params.append(('codigoModalidadeContratacao', mod))

    try:
        # Usamos 'params=params' onde params é uma lista de tuplas para chaves repetidas
        res = requests.get(url, params=params, timeout=25)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        st.error(f"Erro na API: {e}")
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
        "text": f"🚨 PRAZO: {titulo[:50]}",
        "dates": f"{data_fmt}/{data_fmt}",
        "details": f"Objeto: {objeto}\n\nLink: {link}",
        "sf": "true"
    }
    return "https://www.google.com/calendar/render?" + urllib.parse.urlencode(params)

# --- INTERFACE ---
st.title("🏛️ Radar de Licitações PNCP")
st.markdown("Busque editais em tempo real e agende prazos no seu calendário.")

# Sidebar
st.sidebar.header("Filtros")
termo_input = st.sidebar.text_input("Termo de busca", placeholder="Ex: TI, Limpeza, Software")
uf_input = st.sidebar.selectbox("Estado (UF)", ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
data_input = st.sidebar.date_input("Data da Publicação", datetime.now())

st.sidebar.subheader("Modalidades")
m6 = st.sidebar.checkbox("Dispensa (6)", value=True)
m8 = st.sidebar.checkbox("Pregão (8)", value=True)

if st.sidebar.button("🔍 Pesquisar Agora", use_container_width=True):
    modalidades_list = []
    if m6: modalidades_list.append(6)
    if m8: modalidades_list.append(8)
    
    if not modalidades_list:
        st.warning("Selecione ao menos uma modalidade.")
    else:
        with st.spinner("Sincronizando com o Portal Nacional..."):
            resultados = buscar_pncp(termo_input, modalidades_list, data_input.strftime("%Y%m%d"), uf_input)
            
            if resultados:
                st.write(f"### Foram encontradas {len(resultados)} oportunidades")
                
                for item in resultados:
                    orgao = item['orgaoEntidade']['razaoSocial']
                    objeto = item['objetoCompra']
                    link = f"https://pncp.gov.br/app/editais/{item['orgaoEntidade']['cnpj']}/{item['anoCompra']}/{item['sequencialCompra']}"
                    dt_fim = formatar_data(item.get('dataEncerramentoPropostas'))
                    
                    # Card Visual
                    st.markdown(f"""
                    <div class="card">
                        <h4>🏢 {orgao}</h4>
                        <p><strong>📝 Objeto:</strong> {objeto}</p>
                        <p><strong>⚖️ Modalidade:</strong> {item.get('modalidadeNome')} | <strong>🌐 Plataforma:</strong> {item.get('nomeFonteSincronizacao')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns([1, 1, 1])
                    with c1:
                        st.info(f"🚀 Abertura: {formatar_data(item.get('dataAberturaPropostas')).strftime('%d/%m/%Y %H:%M') if item.get('dataAberturaPropostas') else '-'}")
                    with c2:
                        st.error(f"⌛ Encerramento: {dt_fim.strftime('%d/%m/%Y %H:%M') if dt_fim else 'Não informado'}")
                    with c3:
                        sub_c1, sub_c2 = st.columns(2)
                        sub_c1.link_button("📄 Edital", link, use_container_width=True)
                        link_google = gerar_link_google(orgao, objeto, dt_fim, link)
                        sub_c2.link_button("📅 Agendar", link_google, use_container_width=True, type="primary")
                    
                    st.divider()
            else:
                st.info("Nenhum resultado encontrado. Tente mudar o termo ou a data.")
