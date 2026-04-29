import streamlit as st
import pandas as pd
import json
import os
from groq import Groq
from openai import OpenAI
import anthropic
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

# --- CARGA INICIAL ---
config_temp = cargar_datos('config.json', {
    "color_primario": "#1B5E20", 
    "api_proveedor": "Groq",
    "api_key": "",
    "api_modelo": "llama-3.3-70b-versatile",
    "logo_base64": "",
    "macroprocesos": [],
    "detalles_mp": {},
    "perfiles": [],
    "colaboradores_data": [],
    "matriz_cursos": {} 
})

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="DEYFOR Intelligence Hub", page_icon="🚀", layout="wide")

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
        h1, h2, h3 {{ color: {cp} !important; font-weight: 800; }}
        .stButton>button {{ background-color: {cp} !important; color: white !important; border-radius: 10px; font-weight: bold; }}
        .report-box {{ background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid {cp}; margin-bottom: 20px; }}
        .metric-text {{ font-size: 24px; font-weight: bold; color: {cp}; }}
        </style>
    """, unsafe_allow_html=True)

aplicar_estilos()

# --- PROVEEDORES ---
PROVEEDORES = {
    "Groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "OpenAI (ChatGPT)": ["gpt-4o", "gpt-4o-mini"],
    "Claude (Anthropic)": ["claude-3-5-sonnet-20240620"],
    "Gemini (Google)": ["gemini-1.5-flash"]
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
        elif p == "Claude (Anthropic)":
            return anthropic.Anthropic(api_key=k).messages.create(model=m, max_tokens=1024, messages=[{"role": "user", "content": prompt}]).content[0].text
        elif p == "Gemini (Google)":
            genai.configure(api_key=k)
            return genai.GenerativeModel(m).generate_content(prompt).text
        return "Error de configuración."
    except Exception as e: return f"❌ Error: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    if st.session_state.config.get("logo_base64"):
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_base64"]}" width="100%">', unsafe_allow_html=True)
    menu = st.radio("MENÚ PRINCIPAL", ["⚙️ Configuración", "👤 Análisis Individual", "📦 Análisis Masivo", "📈 ROI Potente", "📜 Historial"])

# --- MODULO 1: CONFIGURACIÓN ---
if menu == "⚙️ Configuración":
    st.header("⚙️ Configuración Técnica")
    c1, c2, c3 = st.columns(3)
    with c1: st.session_state.config["api_proveedor"] = st.selectbox("Plataforma", list(PROVEEDORES.keys()))
    with c2: st.session_state.config["api_key"] = st.text_input("API Key", value=st.session_state.config["api_key"], type="password")
    with c3: st.session_state.config["api_modelo"] = st.selectbox("Modelo", PROVEEDORES[st.session_state.config["api_proveedor"]])

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1: f_col = st.file_uploader("Excel Colaboradores", type=["xlsx"])
    with col2: f_mp = st.file_uploader("Excel Macroprocesos", type=["xlsx"])
    with col3: f_pp = st.file_uploader("Excel Perfiles (Cursos)", type=["xlsx"])

    if st.button("💾 GUARDAR Y SINCRONIZAR"):
        if f_col: st.session_state.config["colaboradores_data"] = pd.read_excel(f_col).to_dict('records')
        if f_mp:
            df_mp = pd.read_excel(f_mp)
            st.session_state.config["detalles_mp"] = pd.Series(df_mp.Detalle.values, index=df_mp.MP).to_dict()
        if f_pp:
            df_pp = pd.read_excel(f_pp)
            matriz = df_pp.groupby('PP')['Cursos_Requeridos'].apply(lambda x: [str(i).strip() for i in x if str(i).lower() != 'nan']).to_dict()
            st.session_state.config["matriz_cursos"] = {str(k).strip(): v for k, v in matriz.items()}
            st.session_state.config["perfiles"] = list(st.session_state.config["matriz_cursos"].keys())
        guardar_datos('config.json', st.session_state.config)
        st.success("✅ Matrices cargadas.")

# --- MODULO 2: ANÁLISIS INDIVIDUAL ---
elif menu == "👤 Análisis Individual":
    st.header("👤 Reporte de Impacto Individual")
    data = st.session_state.config.get("colaboradores_data", [])
    if not data: st.warning("Carga colaboradores primero.")
    else:
        df = pd.DataFrame(data)
        colab = st.selectbox("Seleccionar Colaborador", ["--"] + df['Nombre'].tolist())
        if colab != "--":
            info = df[df['Nombre'] == colab].iloc[0]
            perfil = str(info['PP']).strip()
            cursos = st.session_state.config.get("matriz_cursos", {}).get(perfil, [])
            
            if not cursos: st.error("No hay cursos para este perfil.")
            else:
                st.write("Marque los cursos aprobados:")
                check_c = {}
                c1, c2 = st.columns(2)
                for i, c in enumerate(cursos):
                    with (c1 if i%2==0 else c2): check_c[c] = st.checkbox(c, key=f"ci_{i}")
                
                if st.button("🚀 GENERAR REPORTE AL GRANO"):
                    aprobados = [k for k, v in check_c.items() if v]
                    pendientes = [k for k, v in check_c.items() if not v]
                    avance = round((len(aprobados)/len(cursos))*100, 2)
                    
                    prompt = f"""Genera un reporte resumido para DEYFOR. 
                    Persona: {colab}. Perfil: {perfil}. CC: {info['CC']}. MP: {info['MP']}.
                    Avance: {avance}%.
                    Cursos Faltantes: {pendientes}.
                    Analiza el impacto directo en la operación y seguridad por estos cursos faltantes. Sin fórmulas, ve al grano."""
                    
                    with st.spinner("Procesando..."):
                        res = llamar_ia(prompt)
                        st.markdown(f'<div class="report-box">', unsafe_allow_html=True)
                        st.markdown(f"### Reporte: {colab}")
                        st.markdown(f"**CC:** {info['CC']} | **MP:** {info['MP']} | **Avance:** {avance}%")
                        st.markdown("---")
                        st.markdown(res)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.session_state.historial.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "sujeto": colab, "resultado": res})
                        guardar_datos('historial.json', st.session_state.historial)

# --- MODULO 3: ANÁLISIS MASIVO (SIMPLIFICADO) ---
elif menu == "📦 Análisis Masivo":
    st.header("📦 Matriz de Cursos por Perfil")
    perfil_sel = st.selectbox("Seleccionar Perfil de Puesto", ["--"] + st.session_state.config.get("perfiles", []))
    
    if perfil_sel != "--":
        cursos_p = st.session_state.config.get("matriz_cursos", {}).get(perfil_sel, [])
        st.subheader(f"Cursos Obligatorios para: {perfil_sel}")
        for c in cursos_p:
            st.markdown(f"✅ {c}")
        
        if st.button("📊 Análisis de Impacto del Perfil"):
            prompt = f"Analiza de forma resumida el impacto de un {perfil_sel} bien capacitado vs uno sin capacitar en el sector minero. Ve al grano."
            with st.spinner("Analizando..."):
                res = llamar_ia(prompt)
                st.markdown('<div class="report-box">', unsafe_allow_html=True)
                st.markdown(res)
                st.markdown('</div>', unsafe_allow_html=True)

# --- MODULO 4: ROI POTENTE ---
elif menu == "📈 ROI Potente":
    st.header("📈 Análisis de Retorno (ROI)")
    with st.container():
        inv = st.number_input("Inversión (S/.)", value=1000.0)
        prod = st.slider("% Mejora Eficiencia", 0, 100, 20)
        riesgo = st.slider("% Mitigación Accidentes", 0, 100, 40)
        if st.button("📊 Calcular ROI Estratégico"):
            res = llamar_ia(f"Calcula ROI para S/.{inv} con {prod}% mejora prod y {riesgo}% menos riesgo accidentes. Reporte resumido al grano.")
            st.markdown(f'<div class="report-box">{res}</div>', unsafe_allow_html=True)

# --- MODULO 5: HISTORIAL ---
elif menu == "📜 Historial":
    st.header("📜 Registro de Reportes")
    if st.session_state.historial:
        for h in reversed(st.session_state.historial):
            with st.expander(f"{h['fecha']} - {h['sujeto']}"):
                st.markdown(h['resultado'])
