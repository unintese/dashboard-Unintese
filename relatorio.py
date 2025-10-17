import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import streamlit_authenticator as stauth
from gspread_dataframe import get_as_dataframe
from supabase import create_client, Client

# ========================
# CONFIGURAÇÃO DA PÁGINA
# ========================
st.set_page_config(page_title="Dashboard Acadêmica", page_icon="logo-unintese-simples.png", layout="wide")

# ========================
# LÓGICA DE AUTENTICAÇÃO
# ========================
# Conecta ao Supabase usando os secrets do Streamlit Cloud
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Sessão
if "user" not in st.session_state:
    st.session_state.user = None

st.title("🔐 Login - Dashboard Acadêmico")

if st.session_state.user is None:
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        # Busca usuário no Supabase
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data:
            user = response.data[0]
            if bcrypt.checkpw(password.encode(), user["password"].encode()):
                st.session_state.user = user
                st.success("Login realizado!")
                st.experimental_rerun()
            else:
                st.error("Senha incorreta")
        else:
            st.error("Usuário não encontrado")

else:
    st.sidebar.success(f"Bem-vindo(a), {st.session_state.user['name']}!")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.experimental_rerun()

if st.session_state.get("session") is not None:
    # --- O DASHBOARD SÓ É RENDERIZADO SE O LOGIN FOR BEM-SUCEDIDO ---

    # ========================
    # CORES PRINCIPAIS
    # ========================
    COR_LARANJA = "#E85112"
    COR_ROXO = "#703D94"
    COR_FUNDO = "#000000"
    COR_TEXTO = "#FFFFFF"

    # ========================
    # FUNÇÃO DE CACHE PARA CARREGAR DADOS
    # ========================
    @st.cache_data(ttl=600)
    def carregar_dados():
        try:
            creds_dict = st.secrets['gcp_service_account']
            sa = gspread.service_account_from_dict(creds_dict)
            spreadsheet = sa.open('basededados')
            worksheet_base = spreadsheet.worksheet('basededados')
            worksheet_coords = spreadsheet.worksheet('coordenadas')

            dados = get_as_dataframe(worksheet_base, header=0)
            coordenadas = get_as_dataframe(worksheet_coords, header=0)

            dados.dropna(axis=1, how='all', inplace=True)
            coordenadas.dropna(axis=1, how='all', inplace=True)

            # NORMALIZAR CHAVES E JUNTAR DADOS
            if "Cidade" in dados.columns and "Estado" in dados.columns and "Chave" in coordenadas.columns:
                dados["Chave"] = (dados["Cidade"].astype(str).str.strip().str.upper() + " - " + dados["Estado"].astype(str).str.strip().str.upper())
                coordenadas["Chave"] = coordenadas["Chave"].astype(str).str.strip().str.upper()
                dados = dados.merge(coordenadas, on="Chave", how="left")
            else:
                st.error("Colunas essenciais ('Cidade', 'Estado', 'Chave') não encontradas.")
                return None

            # COLUNAS COMO STRING
            for col in ["Estado", "Cidade", "Tipo", "Situacao do contrato", "Curso"]:
                if col in dados.columns:
                    dados[col] = dados[col].astype(str)
            
            return dados
        except Exception as e:
            st.error(f"Erro ao carregar dados do Google Sheets: {e}")
            st.info("Verifique as credenciais 'gcp_service_account' e os nomes da planilha/abas.")
            return None

    dados = carregar_dados()

    if dados is None:
        st.stop()
        
    # ========================
    # CSS E ESTILOS
    # ========================
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {COR_FUNDO}; color: {COR_TEXTO}; }}
        section[data-testid="stSidebar"] {{ background-color: {COR_ROXO}; color: {COR_TEXTO}; }}
        .stSidebar h1, .stSidebar h2, .stSidebar h3 {{ color: {COR_LARANJA}; }}
        .stDownloadButton>button {{ background-color: {COR_LARANJA}; color: white; border-radius: 12px; padding: 0.6em 1.2em; font-weight: 600; border: none; }}
        .stTable thead tr th {{ background-color: {COR_ROXO}; color: white; }}
        .stTable tbody tr td {{ color: {COR_TEXTO}; background-color: {COR_FUNDO}; }}
        .stTabs [role="tablist"] button {{ color: {COR_TEXTO}; }}
        h2, h3 {{ color: {COR_TEXTO}; }}
        header {{ visibility: hidden; }}
        </style>
    """, unsafe_allow_html=True)

    # ========================
    # INFORMAÇÃO DE EXTRAÇÃO E TÍTULO
    # ========================
    st.markdown(f"<p style='text-align:right; color:{COR_TEXTO}; font-size:12px;'>Dados extraídos em: 22/08/2025</p>", unsafe_allow_html=True)
    st.title("📊 Dashboard de Alunos")

    # ========================
    # BARRA LATERAL
    # ========================
    with st.sidebar:
        LOGO_EMPRESA = "logo-unintese-simples.png"
        st.image(LOGO_EMPRESA, use_container_width=True)
        
        st.write(f'Bem-vindo(a), *{st.session_state["name"]}*')
        authenticator.logout('Logout')
        st.markdown("---")

        st.sidebar.markdown(f"<div style='padding:10px; border-radius:5px'>", unsafe_allow_html=True)
        filtro_estado = st.sidebar.multiselect("Selecione Estado(s):", sorted(dados["Estado"].dropna().unique()))
        filtro_cidade = st.sidebar.multiselect("Selecione Cidade(s):", sorted(dados["Cidade"].dropna().unique()))
        filtro_tipo = st.sidebar.multiselect("Selecione Tipo:", sorted(dados["Tipo"].dropna().unique()))
        filtro_situacao = st.sidebar.multiselect("Situação do contrato:", sorted(dados["Situacao do contrato"].dropna().unique()))
        filtro_curso = st.sidebar.multiselect("Curso:", sorted(dados["Curso"].dropna().unique()))
        top_n_cidades = st.sidebar.slider("Top N Cidades:", min_value=5, max_value=20, value=10, step=1)
        top_n_estados = st.sidebar.slider("Top N Estados:", min_value=5, max_value=20, value=10, step=1)
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # ========================
    # FILTRAR DADOS
    # ========================
    df_filtrado = dados.copy()
    if filtro_estado:
        df_filtrado = df_filtrado[df_filtrado["Estado"].isin(filtro_estado)]
    if filtro_cidade:
        df_filtrado = df_filtrado[df_filtrado["Cidade"].isin(filtro_cidade)]
    if filtro_tipo:
        df_filtrado = df_filtrado[df_filtrado["Tipo"].isin(filtro_tipo)]
    if filtro_situacao:
        df_filtrado = df_filtrado[df_filtrado["Situacao do contrato"].isin(filtro_situacao)]
    if filtro_curso:
        df_filtrado = df_filtrado[df_filtrado["Curso"].isin(filtro_curso)]

    # ========================
    # KPIs
    # ========================
    total_alunos = len(df_filtrado)
    alunos_ativos = len(df_filtrado[df_filtrado['Situacao do contrato'].str.upper().isin(['VIGENTE','TRANCADO'])])
    percent_ativos = round((alunos_ativos / total_alunos * 100),1) if total_alunos > 0 else 0
    total_cidades = df_filtrado['Cidade'].nunique()
    total_estados = df_filtrado['Estado'].nunique()
    total_cursos = df_filtrado['Curso'].nunique()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Alunos", f"{total_alunos:,}".replace(',', '.'))
    col2.metric("Cidades", f"{total_cidades:,}".replace(',', '.'))
    col3.metric("Estados", f"{total_estados:,}".replace(',', '.'))
    col4.metric("Alunos Ativos", f"{alunos_ativos:,}".replace(',', '.'), f"{percent_ativos}% do total")
    col5.metric("Cursos", f"{total_cursos:,}".replace(',', '.'))
    
    # ========================
    # ABAS
    # ========================
    tab_geral, tab_cidade, tab_estado = st.tabs(["📊 Geral", "📍 Por Cidade", "🗺️ Por Estado"])

    # ========================
    # ABA GERAL
    # ========================
    with tab_geral:
        if df_filtrado.empty:
            st.warning("Nenhum aluno encontrado para os filtros selecionados.")
        else:
            st.subheader("📌 Total de Alunos por Situação do Contrato")
            tabela_situacao = df_filtrado.groupby("Situacao do contrato").size().reset_index(name="Qtd Alunos")
            tabela_situacao["Qtd Alunos"] = tabela_situacao["Qtd Alunos"].apply(lambda x: f"{x:,}".replace(",", "."))
            st.table(tabela_situacao)
        
            st.subheader("🎓 Total de Alunos por Curso")
            tabela_cursos = df_filtrado.groupby("Curso").size().reset_index(name="Qtd Alunos")
            tabela_cursos["Qtd Alunos"] = tabela_cursos["Qtd Alunos"].apply(lambda x: f"{x:,}".replace(",", "."))
            st.table(tabela_cursos)
        
            csv = df_filtrado.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button(label="📥 Download dos dados filtrados", data=csv, file_name='dados_filtrados.csv', mime='text/csv')

    # ========================
    # ABA CIDADES
    # ========================
    with tab_cidade:
        if df_filtrado.empty:
            st.warning("Nenhum aluno encontrado para os filtros selecionados.")
        else:
            st.subheader("📍 Distribuição de alunos por cidade")
            df_cidade = df_filtrado.groupby(["Chave", "Cidade", "Estado", "Latitude", "Longitude"]).size().reset_index(name="Qtd")
            df_cidade = df_cidade.dropna(subset=["Latitude","Longitude"])
            
            mapa_bolhas = px.scatter_mapbox(df_cidade, lat="Latitude", lon="Longitude", size="Qtd",
                                            hover_name="Cidade", hover_data={"Estado":True,"Qtd":True},
                                            color="Qtd", color_continuous_scale=[COR_LARANJA, COR_ROXO],
                                            size_max=35, zoom=3, height=600)
            mapa_bolhas.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0},
                                      paper_bgcolor=COR_FUNDO, plot_bgcolor=COR_FUNDO, font_color=COR_TEXTO)
            st.plotly_chart(mapa_bolhas, use_container_width=True)
        
            st.subheader(f"🏙️ Top {top_n_cidades} Cidades com mais alunos")
            top_cidades = df_filtrado.groupby("Cidade").size().reset_index(name="Qtd Alunos")
            top_cidades = top_cidades.sort_values(by="Qtd Alunos", ascending=False).head(top_n_cidades)
            
            fig_top_cidades = px.bar(top_cidades, x="Qtd Alunos", y="Cidade", orientation="h",
                                     color_discrete_sequence=[COR_ROXO])
            fig_top_cidades.update_traces(texttemplate='%{x:,}', textposition='outside', textfont=dict(color=COR_TEXTO))
            fig_top_cidades.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor=COR_FUNDO,
                                          plot_bgcolor=COR_FUNDO, font_color=COR_TEXTO)
            st.plotly_chart(fig_top_cidades, use_container_width=True)

    # ========================
    # ABA ESTADOS
    # ========================
    with tab_estado:
        if df_filtrado.empty:
            st.warning("Nenhum aluno encontrado para os filtros selecionados.")
        else:
            st.subheader("🗺️ Distribuição de alunos por estado")
            df_estado = df_filtrado.groupby("Estado").size().reset_index(name="Qtd")
            
            mapa_estados = px.choropleth(df_estado, geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
                                         locations="Estado", featureidkey="properties.sigla", color="Qtd",
                                         color_continuous_scale=[COR_LARANJA, COR_ROXO],
                                         scope="south america", height=600)
            mapa_estados.update_geos(fitbounds="locations", visible=False)
            mapa_estados.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor=COR_FUNDO,
                                       plot_bgcolor=COR_FUNDO, font_color=COR_TEXTO,
                                       hoverlabel=dict(bgcolor=COR_ROXO, font_size=14, font_color=COR_TEXTO))
            mapa_estados.update_traces(hovertemplate='Estado: %{location}<br>Qtd: %{z:,}')
            st.plotly_chart(mapa_estados, use_container_width=True)
        
            st.subheader(f"🗺️ Top {top_n_estados} Estados com mais alunos")
            top_estados = df_filtrado.groupby("Estado").size().reset_index(name="Qtd Alunos")
            top_estados = top_estados.sort_values(by="Qtd Alunos", ascending=False).head(top_n_estados)
            
            fig_top_estados = px.bar(top_estados, x="Qtd Alunos", y="Estado", orientation="h",
                                     color_discrete_sequence=[COR_LARANJA])
            fig_top_estados.update_traces(texttemplate='%{x:,}', textposition='outside', textfont=dict(color=COR_TEXTO))
            fig_top_estados.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor=COR_FUNDO,
                                          plot_bgcolor=COR_FUNDO, font_color=COR_TEXTO)
            st.plotly_chart(fig_top_estados, use_container_width=True)
    
    # ========================
    # RODAPÉ
    # ========================
    st.markdown(f"<p style='text-align:center; color:{COR_TEXTO}; font-size:12px;'>Criado e desenvolvido por Eduardo Martins e Pietro Kettner</p>", unsafe_allow_html=True)



