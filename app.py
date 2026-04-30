import streamlit as st
import pandas as pd
import json
import os
from groq import Groq
from openai import OpenAI
import google.generativeai as genai
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

# --- CONFIGURACIÓN INICIAL ---
config_temp = cargar_datos('config.json', {
    "color_primario": "#1B5E20", 
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

if "pdp_history" not in st.session_state:
    st.session_state.pdp_history = cargar_datos('pdp_history.json', [])

favicon_img = "🚀"
if config_temp.get("favicon_base64"):
    try:
        favicon_bytes = base64.b64decode(config_temp["favicon_base64"])
        favicon_img = Image.open(io.BytesIO(favicon_bytes))
    except: pass

st.set_page_config(page_title="DEYFOR - Gestión de Talento", page_icon=favicon_img, layout="wide")

if "config" not in st.session_state:
    st.session_state.config = config_temp
if "historial" not in st.session_state:
    st.session_state.historial = cargar_datos('historial.json', [])
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def aplicar_estilos():
    cp = st.session_state.config["color_primario"]
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #0E1117; }}
        [data-testid="stSidebar"] {{ background-color: #000000; border-right: 1px solid #333; }}
        h1, h2, h3 {{ color: {cp} !important; font-weight: 800; }}
        .stButton>button {{ background-color: {cp} !important; color: white !important; border-radius: 10px; font-weight: bold; width: 100%; }}
        .report-box {{ background-color: #1E1E1E; padding: 25px; border-radius: 10px; border-left: 5px solid {cp}; margin-top: 20px; color: white; white-space: pre-wrap; }}
        </style>
    """, unsafe_allow_html=True)

aplicar_estilos()

# --- MOTOR IA ---
PROVEEDORES = {
    "Groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "OpenAI (ChatGPT)": ["gpt-4o", "gpt-4o-mini"],
    "Gemini (Google)": ["gemini-1.5-flash", "gemini-1.5-pro"],
    "OpenRouter": ["meta-llama/llama-3.3-70b-instruct"],
    "NVIDIA": ["meta/llama-3.1-405b-instruct"]
}

def llamar_ia(prompt):
    p = st.session_state.config["api_proveedor"]
    k = st.session_state.config["api_key"]
    m = st.session_state.config["api_modelo"]
    if not k: return "⚠️ Falta API Key."
    try:
        if p == "Groq":
            return Groq(api_key=k).chat.completions.create(messages=[{"role": "user", "content": prompt}], model=m).choices[0].message.content
        elif p == "OpenAI (ChatGPT)":
            return OpenAI(api_key=k).chat.completions.create(messages=[{"role": "user", "content": prompt}], model=m).choices[0].message.content
        elif p == "Gemini (Google)":
            genai.configure(api_key=k)
            return genai.GenerativeModel(m).generate_content(prompt).text
        elif p == "OpenRouter":
            return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=k).chat.completions.create(messages=[{"role": "user", "content": prompt}], model=m).choices[0].message.content
        elif p == "NVIDIA":
            return OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k).chat.completions.create(messages=[{"role": "user", "content": prompt}], model=m).choices[0].message.content
        return "Error de proveedor."
    except Exception as e: return f"❌ Error: {str(e)}"

# --- BARRA LATERAL ---
with st.sidebar:
    if st.session_state.config.get("logo_base64"):
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_base64"]}" width="100%">', unsafe_allow_html=True)
    menu = st.radio("GESTIÓN DEYFOR", ["👤 Análisis Individual", "📦 Perfiles y Cursos", "📈 ROI Potente", "📋 Módulo PDP", "📜 Historial", "⚙️ Configuración"])

# --- MODULO 1: ANÁLISIS INDIVIDUAL ---
if menu == "👤 Análisis Individual":
    st.header("👤 Desarrollo de Talento DEYFOR")
    data = st.session_state.config.get("colaboradores_data", [])
    if not data: st.warning("Cargue los datos en Configuración.")
    else:
        df = pd.DataFrame(data)
        colab = st.selectbox("Seleccionar Colaborador", ["--"] + df['Nombre'].tolist())
        if colab != "--":
            info = df[df['Nombre'] == colab].iloc[0]
            perfil = str(info['PP']).strip()
            cursos = st.session_state.config.get("matriz_cursos", {}).get(perfil, [])
            
            st.info(f"👤 **Colaborador:** {colab} | **CC:** {info['CC']} | **MP:** {info['MP']}")
            
            if not cursos: st.error("No hay cursos configurados.")
            else:
                check_c = {}
                c1, c2 = st.columns(2)
                for i, c in enumerate(cursos):
                    with (c1 if i%2==0 else c2): check_c[c] = st.checkbox(c, key=f"ci_{i}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🚀 GENERAR ANÁLISIS DE IMPACTO"):
                        aprobados = [k for k, v in check_c.items() if v]
                        avance = round((len(aprobados)/len(cursos))*100, 2)
                        prompt = f"Analiza brechas para DEYFOR. Persona: {colab}. Avance: {avance}%. Cursos faltantes: {[k for k,v in check_c.items() if not v]}. Sé ejecutivo."
                        res = llamar_ia(prompt)
                        st.markdown(f'<div class="report-box">### {colab} - {avance}% Avance\n\n{res}</div>', unsafe_allow_html=True)

                with col_btn2:
                    if st.button("📄 GENERAR PDP CORPORATIVO"):
                        pendientes = [k for k, v in check_c.items() if not v]
                        prompt_pdp = f"""Genera un Plan de Desarrollo Personal (PDP) para DEYFOR con alta rigurosidad técnica.
                        
                        DATOS BASE:
                        - Nombre: {colab}
                        - Centro de Costo (CC): {info['CC']}
                        - Macroproceso (MP): {info['MP']}
                        - Puesto: {perfil}
                        
                        REQUISITOS DEL PDP:
                        1. OBJETIVOS Y COMPETENCIAS: Identifica 3 competencias clave a perfeccionar basadas en los cursos pendientes ({pendientes}) y el perfil de puesto.
                        2. MÉTRICAS INNOVADORAS: Calcula e inventa métricas de impacto específicas para DEYFOR (ej. % Reducción de incidentes en {info['MP']}, Eficiencia de tiempo por automatización, etc.). No uses OTIF/NPS.
                        3. CRONOGRAMA DE FORMACIÓN (DIAGRAMA GANTT): Crea una tabla o lista visual tipo Gantt que incluya Actividad, Fecha Inicio Propuesta y Fecha Fin Propuesta para cubrir las brechas.
                        
                        Estilo: Corporativo, motivador y directo."""
                        
                        pdp_text = llamar_ia(prompt_pdp)
                        st.markdown(f'<div class="report-box">### PDP DEYFOR - {colab}\n\n{pdp_text}</div>', unsafe_allow_html=True)
                        st.session_state.pdp_history.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "empleado": colab, "pdp": pdp_text})
                        guardar_datos('pdp_history.json', st.session_state.pdp_history)

# --- MÓDULOS RESTANTES ---
elif menu == "📋 Módulo PDP":
    st.header("📋 Archivo de Planes PDP")
    if not st.session_state.pdp_history: st.info("No hay planes generados.")
    else:
        for p in reversed(st.session_state.pdp_history):
            with st.expander(f"{p['fecha']} - {p['empleado']}"):
                st.markdown(p['pdp'])
                st.download_button("📥 Descargar Plan", p['pdp'], file_name=f"PDP_{p['empleado']}.txt", key=p['fecha'])

elif menu == "⚙️ Configuración":
    st.header("⚙️ Configuración")
    if not st.session_state.autenticado:
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Acceder"):
            if pwd == "D3yf0rE1RL":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Denegado")
    else:
        cv1, cv2 = st.columns(2)
        with cv1:
            f_logo = st.file_uploader("Subir Logo", type=["png", "jpg"])
            if f_logo: st.session_state.config["logo_base64"] = base64.b64encode(f_logo.read()).decode()
        with cv2:
            f_fav = st.file_uploader("Subir Favicon", type=["ico", "png"])
            if f_fav: st.session_state.config["favicon_base64"] = base64.b64encode(f_fav.read()).decode()

        c1, c2, c3 = st.columns(3)
        with c1: st.session_state.config["api_proveedor"] = st.selectbox("IA", list(PROVEEDORES.keys()))
        with c2: st.session_state.config["api_key"] = st.text_input("Key", value=st.session_state.config["api_key"], type="password")
        with c3: st.session_state.config["api_modelo"] = st.selectbox("Modelo", PROVEEDORES.get(st.session_state.config["api_proveedor"], ["Cargando..."]))

        col1, col2, col3 = st.columns(3)
        with col1: f_col = st.file_uploader("1. Colaboradores", type=["xlsx"])
        with col2: f_mp = st.file_uploader("2. Macroprocesos", type=["xlsx"])
        with col3: f_pp = st.file_uploader("3. Perfiles", type=["xlsx"])

        if st.button("💾 GUARDAR Y ACTUALIZAR"):
            if f_col: st.session_state.config["colaboradores_data"] = pd.read_excel(f_col).to_dict('records')
            if f_mp:
                df_m = pd.read_excel(f_mp)
                if 'MP' in df_m.columns and 'Detalle' in df_m.columns:
                    st.session_state.config["detalles_mp"] = pd.Series(df_m.Detalle.values, index=df_m.MP).to_dict()
            if f_pp:
                df_p = pd.read_excel(f_pp)
                if 'PP' in df_p.columns and 'Cursos_Requeridos' in df_p.columns:
                    matriz = df_p.groupby('PP')['Cursos_Requeridos'].apply(lambda l: [str(i).strip() for i in l if str(i).lower() != 'nan']).to_dict()
                    st.session_state.config["matriz_cursos"] = {str(k).strip(): v for k, v in matriz.items()}
                    st.session_state.config["perfiles"] = list(st.session_state.config["matriz_cursos"].keys())
            guardar_datos('config.json', st.session_state.config)
            st.success("✅ Sincronizado")

elif menu == "📦 Perfiles y Cursos":
    st.header("📦 Perfiles")
    p_sel = st.selectbox("Perfil", ["--"] + st.session_state.config.get("perfiles", []))
    if p_sel != "--":
        for c in st.session_state.config["matriz_cursos"].get(p_sel, []): st.markdown(f"✅ {c}")

elif menu == "📈 ROI Potente":
    st.header("📈 ROI")
    costo = st.number_input("Inversión S/.", 0.0)
    if st.button("Calcular"): st.write(llamar_ia(f"ROI DEYFOR inversión S/.{costo}"))

elif menu == "📜 Historial":
    st.header("📜 Historial")
    for h in reversed(st.session_state.historial):
        with st.expander(f"{h['fecha']} - {h['sujeto']}"): st.markdown(h['resultado'])
