import streamlit as st
import pandas as pd
import json
import os
from groq import Groq
from openai import OpenAI
import base64
from datetime import datetime
from PIL import Image
import io

# --- PERSISTENCIA ---
def guardar_datos(archivo, datos):
    with open(archivo, 'w') as f:
        json.dump(datos, f)

def cargar_datos(archivo, defecto):
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            return json.load(f)
    return defecto

# --- CARGA INICIAL ---
config_temp = cargar_datos('config.json', {
    "color_primario": "#2E7D32", 
    "api_proveedor": "Groq",
    "api_key": "",
    "api_modelo": "llama-3.3-70b-versatile",
    "logo_base64": "",
    "favicon_base64": "",
    "macroprocesos": [],
    "detalles_mp": {},
    "perfiles": [],
    "colaboradores_data": [],
    "matriz_cursos": {} 
})

# --- CONFIGURACIÓN DE PÁGINA ---
favicon_img = "📊"
if config_temp.get("favicon_base64"):
    try:
        favicon_bytes = base64.b64decode(config_temp["favicon_base64"])
        favicon_img = Image.open(io.BytesIO(favicon_bytes))
    except: pass

st.set_page_config(page_title="DEYFOR", page_icon=favicon_img, layout="wide")

if "config" not in st.session_state:
    st.session_state.config = config_temp
if "historial" not in st.session_state:
    st.session_state.historial = cargar_datos('historial.json', [])

def aplicar_estilos():
    cp = st.session_state.config["color_primario"]
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #0E1117; }}
        [data-testid="stSidebar"] {{ background-color: #000000; border-right: 1px solid #333; }}
        h1, h2, h3, h4, h5, h6, p, span, label, div, li {{ color: #FFFFFF !important; }}
        .stButton>button {{ background-color: {cp} !important; color: white !important; border-radius: 8px; font-weight: bold; }}
        .stTextInput>div>div>input, .stSelectbox>div>div>div {{ background-color: #1E1E1E !important; color: white !important; }}
        .stCheckbox>label>span {{ color: #FFFFFF !important; }}
        </style>
    """, unsafe_allow_html=True)

aplicar_estilos()

with st.sidebar:
    if st.session_state.config.get("logo_base64"):
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_base64"]}" width="100%">', unsafe_allow_html=True)
    st.title("DEYFOR")
    menu = st.radio("Módulos", ["⚙️ Configuración", "👤 Análisis Individual", "📦 Análisis Masivo", "💰 Calculadora ROI", "📜 Historial"])

# --- FUNCIÓN IA (CON MODELO ELEGIBLE) ---
def llamar_ia(prompt):
    prov = st.session_state.config["api_proveedor"]
    key = st.session_state.config["api_key"]
    modelo = st.session_state.config.get("api_modelo")
    
    if not key: return "⚠️ Configura la API Key en Configuración."

    try:
        if prov == "Groq":
            client = Groq(api_key=key)
        else: 
            client = OpenAI(api_key=key)
            
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=modelo
        )
        return response.choices[0].message.content
    except Exception as e: return f"❌ Error de IA: {str(e)}"

# --- MÓDULO 1: CONFIGURACIÓN ---
if menu == "⚙️ Configuración":
    st.header("⚙️ Configuración Técnica")
    
    col_ia1, col_ia2, col_ia3 = st.columns(3)
    with col_ia1:
        st.session_state.config["api_proveedor"] = st.selectbox("Proveedor de IA", ["Groq", "ChatGPT"], index=0)
    with col_ia2:
        st.session_state.config["api_key"] = st.text_input("Ingresar API Key", value=st.session_state.config["api_key"], type="password")
    
    with col_ia3:
        # Menú dinámico de modelos según el proveedor
        if st.session_state.config["api_proveedor"] == "Groq":
            modelos_disponibles = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]
        else:
            modelos_disponibles = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
            
        st.session_state.config["api_modelo"] = st.selectbox("Seleccionar Modelo", modelos_disponibles)

    st.markdown("---")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.subheader("Marca")
        logo = st.file_uploader("Subir Logo", type=["png", "jpg"])
        if logo: st.session_state.config["logo_base64"] = base64.b64encode(logo.read()).decode()
    with col_v2:
        st.subheader("Icono")
        favicon = st.file_uploader("Subir Favicon", type=["png", "ico"])
        if favicon: st.session_state.config["favicon_base64"] = base64.b64encode(favicon.read()).decode()

    st.markdown("---")
    st.subheader("📥 Carga de Datos")
    c1, c2, c3 = st.columns(3)
    with c1:
        f_col = st.file_uploader("Colaboradores (DNI|Nombre|PP|CC|MP)", type=["xlsx"])
    with c2:
        f_mp = st.file_uploader("Macroprocesos (MP|Detalle)", type=["xlsx"])
    with c3:
        f_pp = st.file_uploader("Perfiles y Cursos (PP|Cursos_Requeridos)", type=["xlsx"])

    if st.button("💾 GUARDAR TODO"):
        if f_col: st.session_state.config["colaboradores_data"] = pd.read_excel(f_col).to_dict('records')
        if f_mp:
            df_mp = pd.read_excel(f_mp)
            st.session_state.config["detalles_mp"] = pd.Series(df_mp.Detalle.values, index=df_mp.MP).to_dict()
        if f_pp:
            df_pp = pd.read_excel(f_pp)
            matriz_agrupada = df_pp.groupby('PP')['Cursos_Requeridos'].apply(lambda x: [str(i).strip() for i in x if str(i).lower() != 'nan']).to_dict()
            st.session_state.config["matriz_cursos"] = {str(k).strip(): v for k, v in matriz_agrupada.items()}
            
        guardar_datos('config.json', st.session_state.config)
        st.success(f"✅ Configuración guardada. Modelo activo: {st.session_state.config['api_modelo']}")
        st.rerun()

# --- MÓDULO 2: ANÁLISIS INDIVIDUAL ---
elif menu == "👤 Análisis Individual":
    st.header("👤 Análisis de Brechas")
    data_colabs = st.session_state.config.get("colaboradores_data", [])
    if not data_colabs: st.warning("Sube los datos en Configuración.")
    else:
        df_c = pd.DataFrame(data_colabs)
        df_c['PP'] = df_c['PP'].astype(str).str.strip()
        seleccionado = st.selectbox("Seleccione Colaborador", ["-- Seleccione --"] + df_c['Nombre'].tolist())
        
        if seleccionado != "-- Seleccione --":
            info = df_c[df_c['Nombre'] == seleccionado].iloc[0]
            perfil_c = str(info['PP']).strip()
            
            st.info(f"📍 Perfil: {perfil_c} | Modelo: {st.session_state.config.get('api_modelo')}")
            
            cursos = st.session_state.config.get("matriz_cursos", {}).get(perfil_c, [])
            
            if not cursos:
                st.error(f"❌ No hay cursos para el perfil '{perfil_c}'.")
            else:
                st.subheader("📚 Validación de Cursos")
                check_c = {}
                c_a, c_b = st.columns(2)
                for i, curso in enumerate(cursos):
                    with (c_a if i%2==0 else c_b):
                        check_c[curso] = st.checkbox(curso, key=f"chk_{i}")
                
                if st.button("🚀 REALIZAR ANÁLISIS"):
                    pendientes = [k for k, v in check_c.items() if not v]
                    prompt = f"Analiza brechas de {seleccionado} (Puesto: {perfil_c}). Cursos faltantes: {pendientes}. Da % de cumplimiento y riesgos para DEYFOR."
                    with st.spinner(f"IA analizando con {st.session_state.config.get('api_modelo')}..."):
                        res = llamar_ia(prompt)
                        st.markdown(res)
                        st.session_state.historial.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "sujeto": seleccionado, "perfil": perfil_c, "resultado": res})
                        guardar_datos('historial.json', st.session_state.historial)

# --- CALCULADORA ROI ---
elif menu == "💰 Calculadora ROI":
    st.header("💰 ROI")
    costo = st.number_input("Inversión S/.", 0.0)
    prod = st.slider("% Mejora Productividad", 0, 100, 10)
    if st.button("Calcular con IA"):
        st.write(llamar_ia(f"Calcula ROI de S/.{costo} con mejora de {prod}% en productividad."))

# --- HISTORIAL ---
elif menu == "📜 Historial":
    st.header("📜 Historial")
    if st.session_state.historial:
        for i, reg in enumerate(reversed(st.session_state.historial)):
            with st.expander(f"{reg['fecha']} - {reg['sujeto']}"):
                st.markdown(reg['resultado'])
