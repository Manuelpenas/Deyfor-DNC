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

# --- FUNCIONES DE PERSISTENCIA ---
def guardar_datos(archivo, datos):
    with open(archivo, 'w') as f:
        json.dump(datos, f)

def cargar_datos(archivo, defecto):
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            return json.load(f)
    return defecto

# --- CARGA INICIAL DE CONFIGURACIÓN ---
config_temp = cargar_datos('config.json', {
    "color_primario": "#2E7D32", 
    "api_proveedor": "Groq",
    "api_key": "",
    "logo_base64": "",
    "favicon_base64": "",
    "macroprocesos": [],
    "perfiles": [],
    "personal": []
})

# --- CONFIGURACIÓN DE PÁGINA (DEBE SER LO PRIMERO) ---
# Intentar cargar favicon desde la configuración
favicon_img = "📊" # Icono por defecto
if config_temp["favicon_base64"]:
    try:
        favicon_bytes = base64.b64decode(config_temp["favicon_base64"])
        favicon_img = Image.open(io.BytesIO(favicon_bytes))
    except:
        pass

st.set_page_config(
    page_title="DEYFOR",
    page_icon=favicon_img,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INICIALIZACIÓN DE ESTADOS EN SESSION_STATE ---
if "config" not in st.session_state:
    st.session_state.config = config_temp

if "historial" not in st.session_state:
    st.session_state.historial = cargar_datos('historial.json', [])

# --- CONFIGURACIÓN VISUAL (MODO OSCURO) ---
def aplicar_estilos():
    cp = st.session_state.config["color_primario"]
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #0E1117; }}
        [data-testid="stSidebar"] {{ background-color: #000000; border-right: 1px solid #333; }}
        h1, h2, h3, h4, h5, h6, p, span, label, div, li {{ color: #FFFFFF !important; }}
        .stButton>button {{ 
            background-color: {cp} !important; 
            color: #FFFFFF !important; 
            border-radius: 8px; 
            font-weight: bold;
            border: none;
            width: 100%;
        }}
        .stButton>button:hover {{ 
            background-color: #1B5E20 !important; 
            border: 1px solid #FFFFFF;
        }}
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div>div {{
            background-color: #1E1E1E !important;
            color: #FFFFFF !important;
            border: 1px solid #444 !important;
        }}
        .stCheckbox>label>span {{ color: #FFFFFF !important; }}
        [data-testid="stDataFrame"] {{ background-color: #1E1E1E !important; }}
        </style>
    """, unsafe_allow_html=True)

aplicar_estilos()

# --- BARRA LATERAL (NAVEGACIÓN) ---
with st.sidebar:
    if st.session_state.config["logo_base64"]:
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_base64"]}" width="100%">', unsafe_allow_html=True)
    
    st.title("DEYFOR")
    st.markdown("---")
    menu = st.radio("Módulos", 
        ["⚙️ Configuración", "👤 Análisis Individual", "📦 Análisis Masivo", "💰 Calculadora ROI", "📜 Historial"])

# --- LÓGICA DE IA ---
def llamar_ia(prompt):
    prov = st.session_state.config["api_proveedor"]
    key = st.session_state.config["api_key"]
    if not key: return "⚠️ Configura tu API Key primero."
    try:
        if prov == "Groq":
            client = Groq(api_key=key)
            model = "llama3-70b-8192"
        else: 
            client = OpenAI(api_key=key)
            model = "gpt-4" if prov == "ChatGPT" else "mixtral-8x7b-32768"
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error de IA: {str(e)}"

# --- MÓDULO 1: CONFIGURACIÓN ---
if menu == "⚙️ Configuración":
    st.header("⚙️ Configuración del Sistema")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Identidad Visual")
        logo = st.file_uploader("Logo Principal (PNG/JPG)", type=["png", "jpg"], key="logo_up")
        if logo:
            st.session_state.config["logo_base64"] = base64.b64encode(logo.read()).decode()
        
        favicon = st.file_uploader("Favicon de Pestaña (PNG/ICO)", type=["png", "ico"], key="fav_up")
        if favicon:
            st.session_state.config["favicon_base64"] = base64.b64encode(favicon.read()).decode()
            st.info("💡 El favicon se actualizará al reiniciar o guardar.")

        color = st.color_picker("Color de Marca", st.session_state.config["color_primario"])
        st.session_state.config["color_primario"] = color

    with col2:
        st.subheader("Conexión de IA")
        proveedor = st.selectbox("IA Engine", ["Groq", "ChatGPT", "Gemini", "Claude", "OpenRouter", "NVIDIA"])
        st.session_state.config["api_proveedor"] = proveedor
        key = st.text_input("API Key", value=st.session_state.config["api_key"], type="password")
        st.session_state.config["api_key"] = key

    st.markdown("---")
    st.subheader("📥 Carga de Matrices DEYFOR")
    
    st.info(f"📊 Estado: {len(st.session_state.config['personal'])} Empleados | {len(st.session_state.config['macroprocesos'])} MP | {len(st.session_state.config['perfiles'])} PP")

    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown("**1. Empleados**\n*(DNI | Nombre | PP)*")
        f_emp = st.file_uploader("Cargar Empleados", type=["xlsx", "csv"], key="f_emp")
    with colB:
        st.markdown("**2. Macroprocesos**\n*(MP)*")
        f_mp = st.file_uploader("Cargar MP", type=["xlsx", "csv"], key="f_mp")
    with colC:
        st.markdown("**3. Perfiles**\n*(PP)*")
        f_pp = st.file_uploader("Cargar PP", type=["xlsx", "csv"], key="f_pp")

    if st.button("💾 GUARDAR TODO"):
        exito = True
        if f_emp:
            df = pd.read_csv(f_emp) if f_emp.name.endswith('.csv') else pd.read_excel(f_emp)
            if set(['DNI', 'Nombre', 'PP']).issubset(df.columns):
                st.session_state.config["personal"] = df['Nombre'].dropna().astype(str).unique().tolist()
            else: st.error("Encabezados incorrectos en Empleados"); exito = False
        if f_mp:
            df = pd.read_csv(f_mp) if f_mp.name.endswith('.csv') else pd.read_excel(f_mp)
            if 'MP' in df.columns:
                st.session_state.config["macroprocesos"] = df['MP'].dropna().astype(str).unique().tolist()
            else: st.error("Encabezado 'MP' no encontrado"); exito = False
        if f_pp:
            df = pd.read_csv(f_pp) if f_pp.name.endswith('.csv') else pd.read_excel(f_pp)
            if 'PP' in df.columns:
                st.session_state.config["perfiles"] = df['PP'].dropna().astype(str).unique().tolist()
            else: st.error("Encabezado 'PP' no encontrado"); exito = False

        if exito:
            guardar_datos('config.json', st.session_state.config)
            st.success("✅ Configuración y matrices guardadas.")
            st.rerun()

# --- MÓDULO 2: ANÁLISIS INDIVIDUAL ---
elif menu == "👤 Análisis Individual":
    st.header("👤 Análisis de Brechas Individual")
    if not st.session_state.config["personal"]:
        st.warning("⚠️ Sube las matrices en Configuración.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: nom = st.selectbox("Colaborador", st.session_state.config["personal"])
        with c2: mac = st.selectbox("Macroproceso", st.session_state.config["macroprocesos"] if st.session_state.config["macroprocesos"] else ["S/D"])
        with c3: per = st.selectbox("Perfil", st.session_state.config["perfiles"] if st.session_state.config["perfiles"] else ["S/D"])

        st.subheader("Evaluación de Competencias")
        comps = ["ISO 45001", "Trabajos Altura", "LOTO / Bloqueo", "Gestión Logística", "Liderazgo", "Manejo Defensivo", "Excel"]
        sels = {}
        col_a, col_b = st.columns(2)
        for i, c in enumerate(comps):
            with (col_a if i%2==0 else col_b): sels[c] = st.checkbox(c)

        if st.button("🚀 ANALIZAR"):
            with st.spinner("IA Analizando..."):
                prompt = f"Consultor DEYFOR. Colaborador: {nom}. Puesto: {per}. Domina: {[k for k,v in sels.items() if v]}. Faltan: {[k for k,v in sels.items() if not v]}. Reporte de brecha %, riesgos y plan de acción."
                res = llamar_ia(prompt)
                st.markdown(res)
                st.session_state.historial.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "sujeto": nom, "perfil": per, "resultado": res})
                guardar_datos('historial.json', st.session_state.historial)

# --- MÓDULO 3: ANÁLISIS MASIVO ---
elif menu == "📦 Análisis Masivo":
    st.header("📦 Perfilamiento por Puesto")
    if not st.session_state.config["perfiles"]:
        st.warning("⚠️ Sube las matrices primero.")
    else:
        mac = st.selectbox("Macroproceso", st.session_state.config["macroprocesos"])
        per = st.selectbox("Perfil", st.session_state.config["perfiles"])
        if st.button("🏗️ GENERAR ESTÁNDAR"):
            with st.spinner("Consultando estándares..."):
                res = llamar_ia(f"Define perfil ideal para '{per}' en '{mac}' para DEYFOR (Minería). Competencias SSOMA y técnicas.")
                st.markdown(res)

# --- MÓDULO 4: CALCULADORA ROI ---
elif menu == "💰 Calculadora ROI":
    st.header("💰 Calculadora ROI de Capacitación")
    with st.form("roi"):
        cap = st.text_input("Capacitación")
        n = st.number_input("Participantes", 1)
        cost = st.number_input("Inversión (S/.)", 0.0)
        acc = st.slider("% Reducción Accidentes", 0, 100, 20)
        if st.form_submit_button("📊 CALCULAR"):
            res = llamar_ia(f"CFO Análisis ROI: {cap}, {n} pers, S/. {cost}, {acc}% menos accidentes. Viabilidad y ahorros.")
            st.write(res)

# --- MÓDULO 5: HISTORIAL ---
elif menu == "📜 Historial":
    st.header("📜 Historial")
    if st.session_state.historial:
        df = pd.DataFrame(st.session_state.historial)
        st.dataframe(df[["fecha", "sujeto", "perfil"]], use_container_width=True)
        idx = st.number_input("Ver índice", 0, len(df)-1)
        if st.button("VER REPORTE"):
            st.markdown(df.iloc[idx]["resultado"])
