import streamlit as st
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from Portales_De_Empleo.randstad import create_and_check_url, extract_data_from_offer, transform_data, create_dataframe
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
import config
from google_sheets import read_sheet, write_sheets
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import openai

# Configuración de la página
st.set_page_config(page_title="Dashboard de Ofertas de Trabajo", layout="wide")
credentials = config.credentials

# Estilo personalizado
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1E3A8A;
        text-align: center;
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        display: block;
        margin: 0 auto;
    }
    .stButton>button:hover {
        background-color: #2563EB;
    }
    .centered {
        display: flex;
        justify-content: center;
    }
    .metrics-container {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-wrap: wrap;
    }
    .metric-item {
        margin: 10px;
        text-align: center;
    }
    .section-divider {
        border-top: 2px solid #1E3A8A;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    .stMetric {
        text-align: center;
    }
    .stats-table {
        margin: 0 auto;
        width: 50%;
    }
    .stats-table th, .stats-table td {
        text-align: center;
        padding: 10px;
        border: 1px solid #1E3A8A;
    }
    .stats-table th {
        background-color: #1E3A8A;
        color: white;
    }
       .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
        header {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden !important;}
</style>
""", unsafe_allow_html=True)

# URL base de Randstad
url_base_randstad = "https://www.randstad.es/candidatos/ofertas-empleo/"


def generate_summary(data):
    prompt = f"Basándote en los siguientes datos de ofertas de trabajo, proporciona un breve resumen y conclusión:\n\n{data}\n\nResumen y conclusión:"
    
    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[
            {"role": "system", "content": "Eres un analista de datos experto que proporciona resúmenes concisos y conclusiones significativas."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message['content']



def main():
    st.markdown("<h1 style='text-align: center;'>EINNOVA | CAPTURA DE OFERTAS DE TRABAJO</h1>", unsafe_allow_html=True)

    # Inicializar el estado de la sesión si no existe
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'capture_time' not in st.session_state:
        st.session_state.capture_time = None
    if 'scrape_date' not in st.session_state:
        st.session_state.scrape_date = None

    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        url_base = url_base_randstad
        url = create_and_check_url(url_base)

        if st.button("🚀 Iniciar captura de datos", key="capture_button"):
            with st.spinner('Capturando datos...'):
                start_time = time.time()
                data = extract_data_from_offer(url)
                if not data:
                    st.error("❌ No se encontraron datos para procesar.")
                    return
                
                st.session_state.df = transform_data(create_dataframe(data))
                end_time = time.time()
                
                st.session_state.capture_time = end_time - start_time
                st.session_state.scrape_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"✅ Captura completada en {st.session_state.capture_time:.2f} segundos")

    # Contenedor principal
    if st.session_state.df is not None:
        # Convertir 'Inscritos' y 'Visitas' a numérico
        st.session_state.df['Inscritos'] = pd.to_numeric(st.session_state.df['Inscritos'], errors='coerce')
        st.session_state.df['Visitas'] = pd.to_numeric(st.session_state.df['Visitas'], errors='coerce')

        # Métricas principales
        st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
        metrics = [
            ("📊 Ofertas capturadas", len(st.session_state.df)),
            ("⏱️ Tiempo de captura", f"{st.session_state.capture_time:.2f} s"),
            ("📅 Fecha de scraping", st.session_state.scrape_date)
        ]
        for label, value in metrics:
            st.markdown(f"<div class='metric-item'><h3>{label}</h3><p>{value}</p></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Botón centrado
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("📤 Enviar datos a Google Sheets"):
                with st.spinner('Enviando datos a Google Sheets...'):
                    try:
                        database_original = read_sheet(credentials=config.credentials)
                        result = write_sheets(credentials=config.credentials, dataframe=st.session_state.df)
                        
                        if isinstance(result, HttpError):
                            st.error(f"❌ Error al enviar datos: {result}")
                        else:
                            st.success("✅ Datos enviados exitosamente a Google Sheets")
                            st.markdown(f"<div class='metric-item'><h3>📈 Total ofertas en Sheets</h3><p>{len(database_original) + len(st.session_state.df)}</p></div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"❌ Ocurrió un error inesperado: {e}")

        # Línea divisoria
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Tabla interactiva con los datos
        st.markdown("<h2 style='text-align: center;'>🔍 DATOS CAPTURADOS</h2>", unsafe_allow_html=True)
        st.dataframe(st.session_state.df)

        # Línea divisoria
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Nube de palabras de habilidades requeridas
        st.markdown("<h2 style='text-align: center;'>🔑 HABILIDADES MÁS DEMANDADAS</h2>", unsafe_allow_html=True)
        text = ' '.join(st.session_state.df['Conocimientos'].dropna())
        wordcloud = WordCloud(width=800, height=400, background_color='black', colormap='viridis').generate(text)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_facecolor('black')
        fig.patch.set_facecolor('black')
        st.pyplot(fig)

        # Línea divisoria
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Visualizaciones
        st.markdown("<h2 style='text-align: center;'>📊 ANÁLISIS DE LAS OFERTAS</h2>", unsafe_allow_html=True)
        
        def create_radar_chart(title, data):
            counts = data.value_counts().nlargest(10)
            fig = go.Figure(data=go.Scatterpolar(
                r=counts.values,
                theta=counts.index,
                fill='toself',
                fillcolor='rgba(30, 58, 138, 0.5)',  # Color azul semitransparente
                line=dict(color='#1E3A8A')  # Línea azul oscuro
            ))
            fig.update_layout(
                title=dict(
                    text=title,
                    font=dict(size=16, color='#1E3A8A'),
                    x=0.5,  # Center the title horizontally
                    y=0.95,
                    xanchor='center',  # Anchor point for centering
                    yanchor='top'  # Anchor to the top of the chart
                ),
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(counts.values)]
                    ),
                    bgcolor='black'  # Fondo negro
                ),
                showlegend=False,
                paper_bgcolor='black'  # Fondo del gráfico negro
            )
            return fig

        # Crear todos los gráficos de radar y organizarlos en filas de 3
        charts = [
            ("📍 Distribución Geográfica de Ofertas", st.session_state.df['Localidad']),
            ("💰 Distribución Salarial", st.session_state.df['Salario']),
            ("🏢 Distribución Sector laboral", st.session_state.df['Sector']),
            ("🎓 Distribución Formación Requerida", st.session_state.df['Formación']),
            ("🛠️ Distribución Experiencia necesaria", st.session_state.df['Experiencia']),
            ("🕒 Distribución tipo de jornada", st.session_state.df['Tipo de jornada']),
            ("🏠 Distribución Modalidad Laboral", st.session_state.df['Modalidad']),
            ("💼 Distribución Tipo de puesto", st.session_state.df['Tipo de puesto']),
            ("🧑‍🔬 Distribución Especialidad laboral", st.session_state.df['Especialidad']),
            ("🔧 Distribución Subespecialidad laboral", st.session_state.df['Subespecialidad']),
            ("🌍 Distribución Nivel de Idiomas", st.session_state.df['Idiomas'])
        ]

        for i in range(0, len(charts), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(charts):
                    with cols[j]:
                        st.plotly_chart(create_radar_chart(*charts[i+j]), use_container_width=True)

        # Línea divisoria
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Añadir la media de visitas y de inscritos al final
        st.markdown("<h2 style='text-align: center;'>📊 ESTADÍSTICA VISITAS/INSCRITOS</h2>", unsafe_allow_html=True)
        
        # Crear una tabla HTML para las estadísticas
        stats_table = f"""
        <table class="stats-table">
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
            </tr>
            <tr>
                <td>Media de Visitas</td>
                <td>{st.session_state.df['Visitas'].mean():.2f}</td>
            </tr>
            <tr>
                <td>Media de Inscritos</td>
                <td>{st.session_state.df['Inscritos'].mean():.2f}</td>
            </tr>
        </table>
        """
        st.markdown(stats_table, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
