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
