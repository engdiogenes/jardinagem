
import streamlit as st
import folium
from datetime import datetime
from branca.element import Template, MacroElement
import pandas as pd
import io
from streamlit_folium import folium_static
import json
import os
import matplotlib.pyplot as plt

def load_area_config():
    try:
        if os.path.exists("area_config.json"):
            with open("area_config.json", "r") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Erro ao carregar configuração: {e}")
    # Retorna configuração padrão se não existir ou falhar
    return [
        {
            "nome": f"Área {i+1}",
            "maquina": "Trator",
            "periodo_chuvoso": 30,
            "periodo_seco": 60
        } for i in range(35)
    ]


def save_area_config(config):
    with open("area_config.json", "w") as f:
        json.dump(config, f, indent=4)

# Função para converter mês em português para número
def mes_para_numero(mes):
    meses_pt = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    return meses_pt[mes]

# Configuração inicial do Streamlit
st.set_page_config(layout="wide")

# Inicialização segura do session_state
if "area_info" not in st.session_state:
    area_config = load_area_config()
    if area_config:
        st.session_state.area_info = area_config
    else:
        st.session_state.area_info = [
            {
                "nome": f"Área {i+1}",
                "maquina": "Trator",
                "periodo_chuvoso": 30,
                "periodo_seco": 60
            } for i in range(35)
        ]

if "meses_chuvosos" not in st.session_state:
    st.session_state.meses_chuvosos = ["Janeiro", "Fevereiro", "Março", "Dezembro"]

if "default_color" not in st.session_state:
    st.session_state.default_color = "#90EE90"

if "max_days" not in st.session_state:
    st.session_state.max_days = 90

# Escala de cores padrão
default_colors = {
    0: '#90EE90', 5: '#A8E05F', 10: '#C0D94B', 15: '#D8C93A', 20: '#E8B930',
    25: '#F0A830', 30: '#F7982F', 35: '#F87C2C', 40: '#F95F2A', 45: '#FA4327',
    50: '#FB2A26', 55: '#FC1A24', 60: '#FD0F23', 65: '#E00D20', 70: '#C10B1D',
    75: '#A3091A', 80: '#850717', 85: '#670514', 90: '#490311'
}

def get_color(cut_date, colors):
    cut_date = datetime.combine(cut_date, datetime.min.time())
    days_since_cut = (datetime.now() - cut_date).days
    for days in range(0, st.session_state.get("max_days", 90) + 1, 5):
        if days_since_cut <= days:
            return colors.get(days, st.session_state.get("default_color", "#90EE90"))
    return colors.get(90, st.session_state.get("default_color", "#90EE90"))

def get_status(days_since_cut, chuvoso, seco):
    current_month = datetime.now().month
    meses_chuvosos = [mes_para_numero(month) for month in st.session_state.meses_chuvosos]
    periodicidade = chuvoso if current_month in meses_chuvosos else seco
    return "Vencido" if days_since_cut > periodicidade else "Em dia"

# Sidebar
page = st.sidebar.radio("Navegar para:", ["Mapa", "Configuração", "Histórico de Cortes"])

# Página de configuração
if page == "Configuração":
    st.title("Configuração das Áreas")

    st.session_state["default_color"] = st.color_picker(
        "Cor padrão para áreas sem corte",
        st.session_state.get("default_color", "#90EE90")
    )

    st.session_state["max_days"] = st.slider(
        "Número máximo de dias para escala de cores",
        30, 120, st.session_state.get("max_days", 90)
    )

    st.session_state.meses_chuvosos = st.multiselect(
        "Meses considerados chuvosos",
        options=[
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ],
        default=st.session_state.meses_chuvosos
    )

    for i in range(35):
        with st.expander(f"Configuração da Área {i+1}", expanded=False):
            st.session_state.area_info[i]["nome"] = st.text_input(
                f"Nome da Área {i+1}",
                value=st.session_state.area_info[i]["nome"],
                key=f"nome_{i}"
            )

            st.session_state.area_info[i]["maquina"] = st.selectbox(
                f"Máquina utilizada na Área {i+1}",
                ["Trator", "Girozero", "Roçadeira"],
                index=["Trator", "Girozero", "Roçadeira"].index(
                    st.session_state.area_info[i]["maquina"]
                ),
                key=f"maquina_{i}"
            )

            st.session_state.area_info[i]["periodo_chuvoso"] = st.number_input(
                f"Periodicidade de corte no período chuvoso (dias) - Área {i+1}",
                min_value=1, max_value=180,
                value=st.session_state.area_info[i]["periodo_chuvoso"],
                key=f"chuvoso_{i}"
            )

            st.session_state.area_info[i]["periodo_seco"] = st.number_input(
                f"Periodicidade de corte no período seco (dias) - Área {i+1}",
                min_value=1, max_value=180,
                value=st.session_state.area_info[i]["periodo_seco"],
                key=f"seco_{i}"
            )

    st.success("Configurações atualizadas com sucesso!")
    # Salvar configurações ao final da aba de configuração
    save_area_config(st.session_state.area_info)

# Página do mapa
elif page == "Mapa":
    st.title("Mapa de gestão de corte de vegetação")

    # Baixar modelo de CSV
    st.markdown("### 📄 Baixe o modelo de preenchimento:")
    modelo_df = pd.DataFrame({
        "area": list(range(1, 36)),
        "data_corte": ["2025-03-01"] * 35
    })
    csv_modelo = io.StringIO()
    modelo_df.to_csv(csv_modelo, index=False)
    st.download_button(
        label="📥 Baixar modelo de CSV",
        data=csv_modelo.getvalue(),
        file_name="modelo_corte_vegetacao.csv",
        mime="text/csv"
    )

    # Upload do CSV
    uploaded_file = st.file_uploader("📤 Envie o arquivo CSV com as datas de corte", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "area" not in df.columns or "data_corte" not in df.columns:
            st.error("CSV inválido. As colunas devem ser: 'area' e 'data_corte'")
        else:
            df["data_corte"] = pd.to_datetime(df["data_corte"], errors='coerce')
            if df["data_corte"].isnull().any():
                st.warning("Algumas datas estão inválidas no CSV.")
            else:
                min_days = st.slider("Mostrar áreas com no mínimo X dias desde o corte", 0, st.session_state.get("max_days", 90), 0)

                # Coordenadas das áreas (exemplo fictício)
                area_coords = [[] for _ in range(35)]  # Substitua com coordenadas reais

                m = folium.Map(location=[-22.4882, -44.5424], zoom_start=16.45)

                data = []
                for i in range(35):
                    row = df[df["area"] == i + 1]
                    if not row.empty and area_coords[i]:
                        data_corte = row.iloc[0]["data_corte"].date()
                        days_since_cut = (datetime.now().date() - data_corte).days
                        if days_since_cut >= min_days:
                            nome_area = st.session_state.area_info[i]["nome"]
                            maquina = st.session_state.area_info[i]["maquina"]
                            chuvoso = st.session_state.area_info[i]["periodo_chuvoso"]
                            seco = st.session_state.area_info[i]["periodo_seco"]
                            status = get_status(days_since_cut, chuvoso, seco)
                            folium.Polygon(
                                area_coords[i],
                                color=get_color(data_corte, default_colors),
                                fill=True,
                                fill_opacity=0.7,
                                popup=f"{nome_area}<br>{days_since_cut} dias desde o corte<br>Máquina: {maquina}<br>Status: {status}"
                            ).add_to(m)
                            data.append([nome_area, maquina, days_since_cut, chuvoso, seco, status, data_corte.strftime('%B')])

                # Legenda
                legend_html = '''
                <div style='position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto;
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius:5px; padding: 10px;'>
                <b>Legenda - Dias desde o corte</b><br>
                '''
                for days in range(0, st.session_state.get("max_days", 90) + 1, 15):
                    color = default_colors.get(days, st.session_state.get("default_color", "#C5F5C5"))
                    legend_html += f"<i style='background:{color};width:18px;height:18px;float:left;margin-right:8px;opacity:0.7;'></i>{days} dias<br>"
                legend_html += "</div>"

                legend = MacroElement()
                legend._template = Template(legend_html)
                m.get_root().add_child(legend)

                if data:
                    df_prioridade = pd.DataFrame(data, columns=[
                        "Nome da Área", "Máquina", "Dias desde o corte",
                        "Periodicidade Chuvoso", "Periodicidade Seco", "Status", "Mês do Último Corte"
                    ])
                    df_prioridade = df_prioridade.sort_values(by="Dias desde o corte", ascending=False)

                    st.markdown("### 📋 Ordem de Prioridade de Corte")
                    mes_atual = datetime.now().strftime('%B')
                    periodo_atual = "Chuvoso" if mes_atual in st.session_state.meses_chuvosos else "Seco"
                    st.markdown(f"Atualmente, estamos em período: **{periodo_atual}**")

                    def highlight_status(val):
                        if val == "Vencido":
                            return "background-color: red; color: black"
                        return ""

                    styled_df = df_prioridade.style.applymap(highlight_status, subset=["Status"])
                    st.dataframe(styled_df)

                    folium_static(m, width=1400, height=800)

                    if data and st.button("Exportar Relatório"):
                        df_export = pd.DataFrame(data, columns=[
                            "Nome da Área", "Máquina", "Dias desde o corte",
                            "Periodicidade Chuvoso", "Periodicidade Seco", "Status", "Mês do Último Corte"
                        ])
                        df_export.to_csv("relatorio_corte_vegetacao.csv", index=False)
                        st.success("Relatório exportado com sucesso!")

# Página do histórico de cortes
elif page == "Histórico de Cortes":
    st.title("📄 Histórico de Cortes Realizados")

    uploaded_file = st.file_uploader("📤 Envie o arquivo CSV com as datas de corte", type="csv", key="historico")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "area" not in df.columns or "data_corte" not in df.columns:
            st.error("CSV inválido. As colunas devem ser: 'area' e 'data_corte'")
        else:
            df["data_corte"] = pd.to_datetime(df["data_corte"], errors='coerce')
            df = df.dropna(subset=["data_corte"])
            historico = []

            for i in range(35):
                row = df[df["area"] == i + 1]
                if not row.empty:
                    data_corte = row.iloc[0]["data_corte"].date()
                    dias = (datetime.now().date() - data_corte).days
                    info = st.session_state.area_info[i]
                    status = get_status(dias, info["periodo_chuvoso"], info["periodo_seco"])
                    periodo = "Chuvoso" if datetime.now().month in [mes_para_numero(m) for m in st.session_state.meses_chuvosos] else "Seco"
                    historico.append([
                        info["nome"], data_corte.strftime("%d/%m/%Y"), info["maquina"],
                        dias, status, periodo
                    ])

            df_hist = pd.DataFrame(historico, columns=[
                "Área", "Data do Corte", "Máquina", "Dias desde o Corte", "Status", "Período"
            ])
            st.dataframe(df_hist)
