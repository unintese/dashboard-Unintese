import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import streamlit_authenticator as stauth
from gspread_dataframe import get_as_dataframe

# ========================
# CONFIGURAÇÃO DA PÁGINA
# ========================
st.set_page_config(page_title="Dashboard Acadêmica", page_icon="logo-unintese-simples.png", layout="wide")

# ========================
# LÓGICA DE AUTENTICAÇÃO
# ========================
config = {
    'credentials': {
        'usernames': {}
    },
    'cookie': {
        'name': st.secrets['cookie']['name'],
        'key': st.secrets['cookie']['key'],
        'expiry_days': st.secrets['cookie']['expiry_days']
    }
}
for username, user_info in st.secrets['credentials']['usernames'].items():
    config['credentials']['usernames'][username] = {
        'email': user_info['email'],
        'name': user_info['name'],
        'password': user_info['password']
    }

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login('main')

if st.session_state["authentication_status"]:
    # --- O DASHBOARD SÓ É RENDERIZADO SE O LOGIN FOR BEM-SUCEDIDO ---

    # ========================
    # CORES PRINCIPAIS
    # ========================
    COR_LARANJA = "#E85112"
    COR_ROXO = "#703D94"
    COR_FUNDO = "#000000"
    COR_TEXTO = "#FFFFFF"

    # ========================
    # CARREGAR DADOS DO GOOGLE SHEETS
    # ========================
    try:
        creds_dict = st.secrets['gcp_service_account']
        sa = gspread.service_account_from_dict(creds_dict)
        spreadsheet = sa.open('basededados')
        worksheet_base = spreadsheet.worksheet('basededados')
        worksheet_coords = spreadsheet.worksheet('coordenadas')

        dados = get_as_dataframe(worksheet_base)
        coordenadas = get_as_dataframe(worksheet_coords)

        dados.dropna(axis=1, how='all', inplace=True)
        coordenadas.dropna(axis=1, how='all', inplace=True)

    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {e}")
        st.info("Verifique as credenciais 'gcp_service_account' e os nomes da planilha/abas.")
        st.stop()

    # ========================
    # NORMALIZAR CHAVES E JUNTAR DADOS
    # ========================
    if "Cidade" in dados.columns and "Estado" in dados.columns and "Chave" in coordenadas.columns:
        dados["Chave"] = (dados["Cidade"].astype(str).str.strip().str.upper() + " - " + dados["Estado"].astype(str).str.strip().str.upper())
        coordenadas["Chave"] = coordenadas["Chave"].astype(str).str.strip().str.upper()
        dados = dados.merge(coordenadas, on="Chave", how="left")
    else:
        st.error("Colunas essenciais ('Cidade', 'Estado', 'Chave') não encontradas.")
        st.stop()

    # ========================
    # COLUNAS COMO STRING
    # ========================
    for col in ["Estado", "Cidade", "Tipo", "Situacao do contrato", "Curso"]:
        if col in dados.columns:
            dados[col] = dados[col].astype(str)

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
        header {{
            visibility: hidden;
        }}
        ._profileContainer_gzau3_53 {{
            display: none !important;
        }}
        ._container_gzau3_1 _viewerBadge_nim44_23 {{
            display: none !important;
        }}
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
        st.image(LOGO_EMPRESA, use_column_width=True)
        
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
    total_alunos = df_filtrado.shape[0]
    alunos_ativos = df_filtrado[df_filtrado['Situacao do contrato'].str.upper().isin(['VIGENTE','TRANCADO'])].shape[0]
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
        st.subheader("📌 Total de Alunos por Situação do Contrato")
        tabela_situacao = df_filtrado.groupby("Situacao do contrato").size().reset_index(name="Qtd Alunos")
        tabela_situacao["Qtd Alunos"] = tabela_situacao["Qtd Alunos"].apply(lambda x: f"{x:,}".replace(",", "."))
        st.table(tabela_situacao)
    
        st.subheader("🎓 Total de Alunos por Curso")
        tabela_cursos = df_filtrado.groupby("Curso").size().reset_index(name="Qtd Alunos")
        tabela_cursos["Qtd Alunos"] = tabela_cursos["Qtd Alunos"].apply(lambda x: f"{x:,}".replace(",", "."))
        st.table(tabela_cursos)
    
        # Download dos dados filtrados
        csv = df_filtrado.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(label="📥 Download dos dados filtrados", data=csv, file_name='dados_filtrados.csv', mime='text/csv')
    
    # ========================
    # ABA CIDADES
    # ========================
    with tab_cidade:
        st.subheader("📍 Distribuição de alunos por cidade")
        
        # Agrupa os dados como antes
        df_cidade = df_filtrado.groupby(["Chave", "Cidade", "Estado", "Latitude", "Longitude"]).size().reset_index(name="Qtd")
    
        # --- INÍCIO DA CORREÇÃO MATEMÁTICA ---
    
        # 1. Converte as colunas para o tipo numérico, tratando possíveis erros.
        df_cidade['Latitude'] = pd.to_numeric(df_cidade['Latitude'], errors='coerce')
        df_cidade['Longitude'] = pd.to_numeric(df_cidade['Longitude'], errors='coerce')
    
        # 2. (A CORREÇÃO CRÍTICA) Divide os valores por 10^7 para corrigir o ponto decimal ausente.
        #    A condição 'abs(x) > 180' garante que a divisão só aconteça em números que claramente perderam o decimal.
        df_cidade['Latitude'] = df_cidade['Latitude'].apply(lambda x: x / 10000000 if abs(x) > 90 else x)
        df_cidade['Longitude'] = df_cidade['Longitude'].apply(lambda x: x / 10000000 if abs(x) > 180 else x)
    
        # 3. Remove qualquer linha que ainda tenha coordenadas nulas ou inválidas após a correção.
        df_cidade.dropna(subset=["Latitude", "Longitude"], inplace=True)
        df_cidade = df_cidade[df_cidade['Latitude'].between(-90, 90)]
        df_cidade = df_cidade[df_cidade['Longitude'].between(-180, 180)]
        
        # 4. Verifica se, após a limpeza completa, ainda existem dados para mostrar.
        if df_cidade.empty:
            st.warning("Não há dados de cidades com coordenadas geográficas válidas para exibir com os filtros atuais.")
        else:
            # Se houver dados válidos, cria e exibe o mapa.
            mapa_bolhas = px.scatter_mapbox(df_cidade, lat="Latitude", lon="Longitude", size="Qtd",
                                            hover_name="Cidade",
                                            hover_data={"Estado":True,"Qtd":True},
                                            color="Qtd",
                                            color_continuous_scale=[COR_LARANJA, COR_ROXO],
                                            size_max=35,
                                            zoom=3,
                                            height=600)
            mapa_bolhas.update_layout(mapbox_style="open-street-map",
                                      margin={"r":0,"t":0,"l":0,"b":0},
                                      paper_bgcolor=COR_FUNDO,
                                      plot_bgcolor=COR_FUNDO,
                                      font_color=COR_TEXTO)
            st.plotly_chart(mapa_bolhas, use_container_width=True)
    
        # O código do gráfico de barras continua o mesmo
        st.subheader(f"🏙️ Top {top_n_cidades} Cidades com mais alunos")
        top_cidades = df_filtrado.groupby("Cidade").size().reset_index(name="Qtd Alunos")
        top_cidades = top_cidades.sort_values(by="Qtd Alunos", ascending=False).head(top_n_cidades)
        fig_top_cidades = px.bar(top_cidades, x="Qtd Alunos", y="Cidade", orientation="h",
                                 text="Qtd Alunos", color_discrete_sequence=[COR_ROXO])
        fig_top_cidades.update_traces(texttemplate='%{text:,}'.replace(',', '.'), textfont=dict(color=COR_TEXTO))
        fig_top_cidades.update_layout(yaxis={'categoryorder':'total ascending'},
                                      paper_bgcolor=COR_FUNDO,
                                      plot_bgcolor=COR_FUNDO,
                                      font_color=COR_TEXTO)
        st.plotly_chart(fig_top_cidades, use_container_width=True)
    # ========================
    # ABA ESTADOS
    # ========================
    with tab_estado:
        st.subheader("🗺️ Distribuição de alunos por estado")
        df_estado = df_filtrado.groupby("Estado").size().reset_index(name="Qtd")
        mapa_estados = px.choropleth(df_estado,
                                     geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
                                     locations="Estado", featureidkey="properties.sigla", color="Qtd",
                                     color_continuous_scale=[COR_LARANJA, COR_ROXO],
                                     scope="south america",
                                     height=600)
        mapa_estados.update_geos(fitbounds="locations", visible=False)
        mapa_estados.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                                   paper_bgcolor=COR_FUNDO,
                                   plot_bgcolor=COR_FUNDO,
                                   font_color=COR_TEXTO,
                                   hoverlabel=dict(bgcolor=COR_ROXO, font_size=14, font_color=COR_TEXTO))
        mapa_estados.update_traces(hovertemplate='Estado: %{location}<br>Qtd: %{z:,}'.replace(',', '.'))
        st.plotly_chart(mapa_estados, use_container_width=True)
    
        st.subheader(f"🗺️ Top {top_n_estados} Estados com mais alunos")
        top_estados = df_filtrado.groupby("Estado").size().reset_index(name="Qtd Alunos")
        top_estados = top_estados.sort_values(by="Qtd Alunos", ascending=False).head(top_n_estados)
        fig_top_estados = px.bar(top_estados, x="Qtd Alunos", y="Estado", orientation="h",
                                 text="Qtd Alunos", color_discrete_sequence=[COR_LARANJA])
        fig_top_estados.update_traces(texttemplate='%{text:,}'.replace(',', '.'), textfont=dict(color=COR_TEXTO))
        fig_top_estados.update_layout(yaxis={'categoryorder':'total ascending'},
                                      paper_bgcolor=COR_FUNDO,
                                      plot_bgcolor=COR_FUNDO,
                                      font_color=COR_TEXTO)
        st.plotly_chart(fig_top_estados, use_container_width=True)
    
    # ========================
    # RODAPÉ
    # ========================
    st.markdown(f"<p style='text-align:center; color:{COR_TEXTO}; font-size:12px;'>Criado e desenvolvido por Eduardo Martins e Pietro Kettner</p>", unsafe_allow_html=True)

elif st.session_state["authentication_status"] is False:
    st.error('Usuário ou senha incorreta')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, insira seu usuário e senha')





















