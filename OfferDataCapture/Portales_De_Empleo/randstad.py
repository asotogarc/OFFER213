import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pandas as pd
import re

def create_and_check_url(url_base):
    city = st.session_state.get('city', '')
    skill = st.session_state.get('skill', '')
    
    st.text_input('Introduzca la ciudad donde quiere buscar la oferta de trabajo:', key='city', value=city)
    st.text_input('Introduzca la skill principal de la oferta de trabajo (opcional):', key='skill', value=skill)
    
    if st.session_state.city:
        url_user_input = f"p-{st.session_state.city}/"
        if st.session_state.skill:
            url_user_input += f"q-{st.session_state.skill}/"
        url = url_base + url_user_input
        return url
    return None

def get_url_offers(url):
    all_links = []
    page = 1
    while True:
        page_url = f"{url}pg-{page}/"
        respuesta = requests.get(page_url)
        if respuesta.status_code != 200:
            break
        
        soup = BeautifulSoup(respuesta.content, "html.parser")
        links = soup.find_all('a', class_='text--navy rand-job-search-results__offer-title-link js-offer-title')
        
        if not links:
            break
        
        all_links.extend([link['href'] for link in links])
        page += 1
        time.sleep(1)  # Añadir un pequeño retraso para no sobrecargar el servidor
    
    return all_links
# Función para extraer datos de cada oferta
def extract_data_from_offer(url_base):
    par_text = []
    links_list = get_url_offers(url_base)

    for url in links_list:
        time.sleep(1)
        p_resp = requests.get(url)
        soup = BeautifulSoup(p_resp.content, 'html.parser')

        nombre_oferta = soup.find('h1', class_='content-block__title').get_text(strip=True) if soup.find('h1', class_='content-block__title') else "Título no encontrado"

        requisitos_title = soup.find('h3', class_='job-detail__section-title text--alternative', string='requisitos del puesto')
        requisitos = []
        if requisitos_title:
            requisitos_list = requisitos_title.find_next('ul')
            if requisitos_list:
                for item in requisitos_list.find_all('li'):
                    h4 = item.find('h4')
                    if h4:
                        requisitos.append(f"{h4.get_text(strip=True)}: {item.get_text(strip=True).replace(h4.get_text(strip=True), '').strip()}")

        salario = soup.find('li', class_='contact-details__link behat-salary')
        salario_text = salario.get_text(strip=True) if salario else "Salario no encontrado"

        tipo_contrato = soup.find('li', class_='cards__meta-item')
        tipo_contrato_text = tipo_contrato.find('h3', class_='lowercase body--m').get_text(strip=True) if tipo_contrato else "Tipo de contrato no encontrado"

        tipo_jornada = soup.find('h3', class_='lowercase body--m', string=lambda text: 'jornada' in text.lower())
        tipo_jornada_text = tipo_jornada.get_text(strip=True) if tipo_jornada else "Tipo de jornada no encontrado"

        modalidad_trabajo = soup.find('h3', class_='lowercase body--m', string=lambda text: 'modalidad' in text.lower())
        modalidad_trabajo_text = modalidad_trabajo.get_text(strip=True) if modalidad_trabajo else "Modalidad de trabajo no encontrada"

        area_especialidad = soup.find('h3', class_='lowercase body--m', string=lambda text: 'sector' in text.lower())
        area_especialidad_text = area_especialidad.get_text(strip=True) if area_especialidad else "Área de especialidad no encontrada"

        tipo_puesto = soup.find('h3', class_='text--alternative body--s', string='puesto')
        tipo_puesto_text = tipo_puesto.find_next('span', class_='lowercase').get_text(strip=True) if tipo_puesto else "Tipo de puesto no encontrado"

        num_vacantes = soup.find('span', class_='lowercase', string=lambda text: text.isdigit())
        num_vacantes_text = num_vacantes.get_text(strip=True) if num_vacantes else "Número de vacantes no encontrado"

        localidad = soup.find('h3', class_='text--alternative body--s', string='localidad')
        localidad_text = localidad.find_next('span', class_='').get_text(strip=True) if localidad else "Localidad no encontrada"

        provincia = soup.find('h3', class_='text--alternative body--s', string='provincia')
        provincia_text = provincia.find_next('span', class_='').get_text(strip=True) if provincia else "Provincia no encontrada"

        especialidad = soup.find('h3', class_='text--alternative body--s', string='especialidad')
        especialidad_text = especialidad.find_next('span', class_='lowercase').get_text(strip=True) if especialidad else "Especialidad no encontrada"

        subespecialidad = soup.find('h3', class_='text--alternative body--s', string='subespecialidad')
        subespecialidad_text = subespecialidad.find_next('span', class_='lowercase').get_text(strip=True) if subespecialidad else "Subespecialidad no encontrada"

        funciones_title = soup.find('h3', class_='job-detail__section-title text--alternative', string='tus funciones')
        texto_funciones = funciones_title.find_next('p', class_='collapsible-text__content').get_text(strip=True) if funciones_title else "Funciones no encontradas"

        info_publicacion = soup.find('p', class_='body--s text--alternative hidden--until-l')
        info_publicacion_text = info_publicacion.get_text(strip=True) if info_publicacion else "Información de publicación no encontrada"

        fecha_cierre = soup.find('p', class_='job-detail__end-date')
        if fecha_cierre:
            fecha_cierre_text = fecha_cierre.get_text(strip=True)
            # Extraer solo la fecha usando una expresión regular
            match = re.search(r'\d{2}/\d{2}/\d{4}', fecha_cierre_text)
            fecha_cierre_text = match.group(0) if match else "Fecha de cierre no encontrada"
        else:
            fecha_cierre_text = "Fecha de cierre no encontrada"

        fecha_scrapeo = datetime.now().strftime("%d/%m/%Y")

        par_text.append(f"Nombre: {nombre_oferta} | {' | '.join(requisitos)} | Salario: {salario_text} | Tipo de contrato: {tipo_contrato_text} | Tipo de jornada: {tipo_jornada_text} | Modalidad: {modalidad_trabajo_text} | Sector: {area_especialidad_text} | Tipo de puesto: {tipo_puesto_text} | Vacantes: {num_vacantes_text} | Localidad: {localidad_text} | Provincia: {provincia_text} | Especialidad: {especialidad_text} | Subespecialidad: {subespecialidad_text} | Funciones: {texto_funciones}  | Fecha de publicación, visitas e inscritos: {info_publicacion_text} | Fecha de cierre: {fecha_cierre_text} | Fecha de scrapeo: {fecha_scrapeo} | url: {url}")

    return par_text

# Función para parsear un registro
def parse_record(record):
    fields = record.split(" | ")
    record_dict = {}
    for field in fields:
        parts = field.split(": ", 1)
        if len(parts) == 2:
            key, value = parts
            record_dict[key.strip()] = value.strip()
        else:
            key = f"campo_{len(record_dict)}"
            record_dict[key] = field.strip()
    return record_dict

# Función para crear un DataFrame
def create_dataframe(par_text):
    data = []
    for record in par_text:
        try:
            data.append(parse_record(record))
        except Exception as e:
            st.warning(f"Error al procesar el registro: {str(e)}")
            st.text(f"Registro problemático: {record}")
    df = pd.DataFrame(data)
    return df

# Función para transformar los datos
def transform_data(df):
    columns_to_process = ['Formación', 'Idiomas', 'Conocimientos', 'Experiencia', 'Fecha de cierre']
    for col in columns_to_process:
        if col in df.columns:
            df[col] = df[col].str.replace(r':', '', regex=True).str.strip()

    if 'Fecha de publicación, visitas e inscritos' in df.columns:
        df['Fecha de publicación'] = df['Fecha de publicación, visitas e inscritos'].str.extract(r'publicado el (\d{2}/\d{2}/\d{4})')
        df['Visitas'] = df['Fecha de publicación, visitas e inscritos'].str.extract(r'(\d+) visitas')
        df['Inscritos'] = df['Fecha de publicación, visitas e inscritos'].str.extract(r'(\d+) inscritos')
        df = df.drop(columns=['Fecha de publicación, visitas e inscritos'])

    for col in ['Visitas', 'Inscritos', 'Vacantes']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.fillna("")
    df = df.fillna(0)

    date_columns = ['Fecha de publicación', 'Fecha de cierre', 'Fecha de scrapeo']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')

    return df
# Función para parsear un registro
def parse_record(record):
    fields = record.split(" | ")
    record_dict = {}
    for field in fields:
        parts = field.split(": ", 1)
        if len(parts) == 2:
            key, value = parts
            record_dict[key.strip()] = value.strip()
        
    return record_dict

# Función para crear un DataFrame
def create_dataframe(par_text):
    data = []
    for record in par_text:
        try:
            data.append(parse_record(record))
        except Exception as e:
            st.warning(f"Error al procesar el registro: {str(e)}")
            st.text(f"Registro problemático: {record}")
    df = pd.DataFrame(data)
    return df

# Función para transformar los datos
def transform_data(df):
    columns_to_process = ['Formación', 'Idiomas', 'Conocimientos', 'Experiencia', 'Fecha de cierre']
    for col in columns_to_process:
        if col in df.columns:
            df[col] = df[col].str.replace(r':', '', regex=True).str.strip()

    if 'Fecha de publicación, visitas e inscritos' in df.columns:
        df['Fecha de publicación'] = df['Fecha de publicación, visitas e inscritos'].str.extract(r'publicado el (\d{2}/\d{2}/\d{4})')
        df['Visitas'] = df['Fecha de publicación, visitas e inscritos'].str.extract(r'(\d+) visitas')
        df['Inscritos'] = df['Fecha de publicación, visitas e inscritos'].str.extract(r'(\d+) inscritos')
        df = df.drop(columns=['Fecha de publicación, visitas e inscritos'])

    for col in ['Visitas', 'Inscritos', 'Vacantes']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.fillna("")
    df = df.fillna(0)

    date_columns = ['Fecha de publicación', 'Fecha de cierre', 'Fecha de scrapeo']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')

    return df
