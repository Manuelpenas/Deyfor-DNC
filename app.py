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

st.set_page_config(page_title="DEYFOR - Gestión de Talento", page_icon="🚀", layout="wide")

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
        .report-box {{ background-color: #1E1E1E; padding: 25px; border-radius: 10px; border-left: 5px solid {cp}; margin-top: 20px; color: white; }}
        </style>
    """, unsafe_allow_html=True)

aplicar_estilos()

# --- MOTOR IA ---
PROVEEDORES = {
    "Groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "OpenAI (ChatGPT)": ["gpt-4o", "gpt-4o-mini"],
    "Gemini (Google)": ["gemini-1.5-flash", "gemini-1.5-pro"]
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
        return "Error de proveedor."
    except Exception as e: return f"❌ Error: {str(e)}"

# --- BARRA LATERAL ---
with st.sidebar:
    if st.session_state.config.get("logo_base64"):
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_base64"]}" width="100%">', unsafe_allow_html=True)
    # Cambiamos el orden para que Análisis Individual sea el primero
    menu = st.radio("GESTIÓN DEYFOR", ["👤 Análisis Individual", "📦 Perfiles y Cursos", "📈 ROI Potente", "📜 Historial", "⚙️ Configuración"])

# --- MODULO 1: ANÁLISIS INDIVIDUAL (PÁGINA DE INICIO) ---
if menu == "👤 Análisis Individual":
    st.header("👤 Análisis de Brechas y Desarrollo")
    data = st.session_state.config.get("colaboradores_data", [])
    if not data:
        st.warning("⚠️ No hay datos de colaboradores. Contacte al administrador para configurar las matrices.")
    else:
        df = pd.DataFrame(data)
        colab = st.selectbox("Seleccionar Colaborador", ["--"] + df['Nombre'].tolist())
        
        if colab != "--":
            info = df[df['Nombre'] == colab].iloc[0]
            perfil = str(info['PP']).strip()
            st.info(f"📍 **Perfil:** {perfil} | **CC:** {info['CC']} | **MP:** {info['MP']}")
            
            cursos = st.session_state.config.get("matriz_cursos", {}).get(perfil, [])
            if not cursos:
                st.error("No hay cursos configurados para este perfil.")
            else:
                st.subheader("Validación de Competencias")
                check_c = {}
                c1, c2 = st.columns(2)
                for i, c in enumerate(cursos):
                    with (c1 if i%2==0 else c2): check_c[c] = st.checkbox(c, key=f"ci_{i}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🚀 GENERAR ANÁLISIS DE IMPACTO"):
                        aprobados = [k for k, v in check_c.items() if v]
                        pendientes = [k for k, v in check_c.items() if not v]
                        avance = round((len(aprobados)/len(cursos))*100, 2)
                        prompt = f"Consultor DEYFOR. Colaborador: {colab}. Puesto: {perfil}. CC: {info['CC']}. MP: {info['MP']}. Avance: {avance}%. Cursos faltantes: {pendientes}. Reporte al grano."
                        with st.spinner("Analizando..."):
                            res = llamar_ia(prompt)
                            st.markdown(f'<div class="report-box">### {colab} - {avance}% Avance<hr>{res}</div>', unsafe_allow_html=True)
                
                with col_btn2:
                    if st.button("📄 CREAR PLAN DE DESARROLLO (PDP)"):
                        aprobados = [k for k, v in check_c.items() if v]
                        pendientes = [k for k, v in check_c.items() if not v]
                        # Prompt estructurado según el modelo de ABInBev enviado
                        prompt_pdp = f"""Crea un Plan de Desarrollo Personal (PDP) para {colab} en DEYFOR.
                        Basado en el modelo ABInBev:
                        - Perfil: {perfil}. 
                        - Posición Inicio: {info['MP']}.
                        - Objetivos de Liderazgo: Definir 3 (Soñar en Grande, Desarrollo de Colaboradores, Sostenibilidad).
                        - Objetivos Técnicos: Basados en completar los cursos pendientes: {pendientes}.
                        - Plan de Acción: Detallar cómo usará Power BI, Chatbots u otras herramientas para mejorar sus indicadores de {info['MP']}.
                        Presenta el PDP en formato profesional, listo para descargar."""
                        with st.spinner("Estructurando PDP..."):
                            pdp_res = llamar_ia(prompt_pdp)
                            st.markdown(f'<div class="report-box">### 📝 PDP DEYFOR: {colab}<hr>{pdp_res}</div>', unsafe_allow_html=True)
                            st.download_button("📥 Descargar PDP en Texto", pdp_res, file_name=f"PDP_{colab}.txt")

# --- MODULO 2: PERFILES ---
elif menu == "📦 Perfiles y Cursos":
    st.header("📦 Matriz de Perfiles")
    p_sel = st.selectbox("Perfil", ["--"] + st.session_state.config.get("perfiles", []))
    if p_sel != "--":
        cursos_p = st.session_state.config.get("matriz_cursos", {}).get(p_sel, [])
        for c in cursos_p: st.markdown(f"✅ {c}")

# --- MODULO 3: ROI ---
elif menu == "📈 ROI Potente":
    st.header("📈 ROI Estratégico")
    c1, c2 = st.columns(2)
    with c1: nom_cap = st.text_input("Capacitación")
    with c2: costo_cap = st.number_input("Inversión (S/.)")
    if st.button("Calcular Impacto"):
        st.write(llamar_ia(f"Calcula ROI DEYFOR para {nom_cap} con costo {costo_cap}. Reporte resumido."))

# --- MODULO 4: HISTORIAL ---
elif menu == "📜 Historial":
    st.header("📜 Historial de Reportes")
    if st.session_state.historial:
        for h in reversed(st.session_state.historial):
            with st.expander(f"{h['fecha']} - {h['sujeto']}"): st.markdown(h['resultado'])

# --- MODULO 5: CONFIGURACIÓN (CON CONTRASEÑA) ---
elif menu == "⚙️ Configuración":
    st.header("⚙️ Configuración de Administrador")
    
    if not st.session_state.autenticado:
        pass_input = st.text_input("Ingrese Contraseña de Acceso", type="password")
        if st.button("Desbloquear"):
            if pass_input == "D3yf0rE1RL":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        if st.button("🔒 Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()
            
        st.subheader("Ajustes de Sistema")
        c1, c2, c3 = st.columns(3)
        with c1: st.session_state.config["api_proveedor"] = st.selectbox("IA", list(PROVEEDORES.keys()))
        with c2: st.session_state.config["api_key"] = st.text_input("Key", value=st.session_state.config["api_key"], type="password")
        with c3: st.session_state.config["api_modelo"] = st.selectbox("Modelo", PROVEEDORES[st.session_state.config["api_proveedor"]])

        col1, col2, col3 = st.columns(3)
        with col1: f_col = st.file_uploader("Colaboradores", type=["xlsx"])
        with col2: f_mp = st.file_uploader("Macroprocesos", type=["xlsx"])
        with col3: f_pp = st.file_uploader("Perfiles", type=["xlsx"])

        if st.button("💾 GUARDAR CAMBIOS"):
            if f_col: st.session_state.config["colaboradores_data"] = pd.read_excel(f_col).to_dict('records')
            if f_pp:
                df_pp = pd.read_excel(f_pp)
                matriz = df_pp.groupby('PP')['Cursos_Requeridos'].apply(lambda x: [str(i).strip() for i in x if str(i).lower() != 'nan']).to_dict()
                st.session_state.config["matriz_cursos"] = {str(k).strip(): v for k, v in matriz.items()}
                st.session_state.config["perfiles"] = list(st.session_state.config["matriz_cursos"].keys())
            guardar_datos('config.json', st.session_state.config)
            st.success("Configuración actualizada.")
