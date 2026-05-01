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
    menu = st.radio("GESTIÓN DEYFOR", ["👤 Análisis Individual", "📦 Perfiles y Cursos", "📈 ROI Potente", "📋 Módulo PDP", "📜 Historial", "⚙️ Configuración"])

# --- MODULO 1: ANÁLISIS INDIVIDUAL ---
if menu == "👤 Análisis Individual":
    st.header("👤 Análisis Individual y Desarrollo")
    data = st.session_state.config.get("colaboradores_data", [])
    if not data:
        st.warning("Cargue los datos en Configuración.")
    else:
        df = pd.DataFrame(data)
        colab = st.selectbox("Seleccionar Colaborador", ["--"] + df['Nombre'].tolist())
        if colab != "--":
            info = df[df['Nombre'] == colab].iloc[0]
            perfil = str(info['PP']).strip()
            cursos = st.session_state.config.get("matriz_cursos", {}).get(perfil, [])
            st.info(f"👤 **Colaborador:** {colab} | **CC:** {info['CC']} | **MP:** {info['MP']}")
            if not cursos:
                st.error("No hay cursos configurados.")
            else:
                check_c = {}
                c1, c2 = st.columns(2)
                for i, c in enumerate(cursos):
                    with (c1 if i%2==0 else c2): check_c[c] = st.checkbox(c, key=f"ci_{i}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🚀 GENERAR ANÁLISIS"):
                        aprobados = [k for k, v in check_c.items() if v]
                        avance = round((len(aprobados)/len(cursos))*100, 2) if cursos else 0
                        prompt = f"Analiza impacto DEYFOR. Persona: {colab}. Avance: {avance}%. Directo."
                        res = llamar_ia(prompt)
                        st.markdown(f'<div class="report-box">### {colab} - {avance}% Avance\n\n{res}</div>', unsafe_allow_html=True)
                with col_btn2:
                    if st.button("📄 GENERAR PDP CORPORATIVO"):
                        pendientes = [k for k, v in check_c.items() if not v]
                        prompt_pdp = f"Genera PDP DEYFOR para {colab}. CC: {info['CC']}. MP: {info['MP']}. Puesto: {perfil}. Competencias: {pendientes}. Incluye Gantt y métricas innovadoras."
                        pdp_text = llamar_ia(prompt_pdp)
                        st.markdown(f'<div class="report-box">### PDP DEYFOR - {colab}\n\n{pdp_text}</div>', unsafe_allow_html=True)
                        st.session_state.pdp_history.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "empleado": colab, "pdp": pdp_text})
                        guardar_datos('pdp_history.json', st.session_state.pdp_history)

# --- MODULO 2: PERFILES Y CURSOS ---
elif menu == "📦 Perfiles y Cursos":
    st.header("📦 Gestión de Perfiles")
    p_sel = st.selectbox("Seleccionar Perfil", ["--"] + st.session_state.config.get("perfiles", []))
    if p_sel != "--":
        cursos_p = st.session_state.config.get("matriz_cursos", {}).get(p_sel, [])
        for c in cursos_p: st.markdown(f"✅ {c}")
        st.markdown("---")
        with st.expander("➕ Agregar curso manualmente"):
            nuevo_curso = st.text_input("Nombre del nuevo curso")
            if st.button("Añadir"):
                if nuevo_curso and nuevo_curso not in st.session_state.config["matriz_cursos"][p_sel]:
                    st.session_state.config["matriz_cursos"][p_sel].append(nuevo_curso)
                    guardar_datos('config.json', st.session_state.config)
                    st.rerun()

# --- MODULO 3: ROI POTENTE ---
elif menu == "📈 ROI Potente":
    st.header("📈 Calculadora de ROI")
    todos_los_cursos = sorted(list(set([c for lista in st.session_state.config.get("matriz_cursos", {}).values() for c in lista])))
    
    c1, c2, c3 = st.columns(3)
    with c1: 
        nom_cap = st.selectbox("Seleccionar Capacitación", ["-- Personalizado --"] + todos_los_cursos)
        if nom_cap == "-- Personalizado --": nom_cap = st.text_input("Nombre Manual")
    with c2: costo_cap = st.number_input("Inversión Total (S/.)", min_value=0, step=1, format="%d")
    with c3: cant_part = st.number_input("Participantes", min_value=1, step=1, format="%d")
    
    st.subheader("Beneficios Estimados (Enteros)")
    b1, b2 = st.columns(2)
    with b1:
        a_acc = st.number_input("Ahorro Accidentes (S/.)", min_value=0, step=1, format="%d")
        i_prod = st.number_input("Mejora Productividad (S/.)", min_value=0, step=1, format="%d")
    with b2:
        r_err = st.number_input("Reducción Errores (S/.)", min_value=0, step=1, format="%d")
        p_mul = st.number_input("Prevención Multas (S/.)", min_value=0, step=1, format="%d")
            
    if st.button("📊 CALCULAR ROI"):
        prompt = f"ROI DEYFOR. Cap: {nom_cap}. Inversión: {costo_cap}. Beneficios: Accidentes {a_acc}, Productividad {i_prod}, Errores {r_err}, Multas {p_mul}."
        res = llamar_ia(prompt)
        st.markdown(f'<div class="report-box">### ROI: {nom_cap}\n\n{res}</div>', unsafe_allow_html=True)

# --- MODULOS ADICIONALES ---
elif menu == "📋 Módulo PDP":
    st.header("📋 Archivo de Planes PDP")
    for p in reversed(st.session_state.pdp_history):
        with st.expander(f"{p['fecha']} - {p['empleado']}"): st.markdown(p['pdp'])

elif menu == "📜 Historial":
    st.header("📜 Historial")
    for h in reversed(st.session_state.historial):
        with st.expander(f"{h['fecha']} - {h['sujeto']}"): st.markdown(h['resultado'])

elif menu == "⚙️ Configuración":
    st.header("⚙️ Configuración")
    if not st.session_state.autenticado:
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Acceder"):
            if pwd == "D3yf0rE1RL": st.session_state.autenticado = True; st.rerun()
            else: st.error("Denegado")
    else:
        # Aquí van tus cargadores de archivos y logos (se mantienen igual que antes)
        if st.button("🔒 Cerrar Sesión"): st.session_state.autenticado = False; st.rerun()
        st.subheader("Matrices y Datos")
        c1, c2, c3 = st.columns(3)
        with c1: f_col = st.file_uploader("Colaboradores", type=["xlsx"])
        with c2: f_mp = st.file_uploader("Macroprocesos", type=["xlsx"])
        with c3: f_pp = st.file_uploader("Perfiles", type=["xlsx"])
        if st.button("💾 GUARDAR"):
            if f_col: st.session_state.config["colaboradores_data"] = pd.read_excel(f_col).to_dict('records')
            if f_pp:
                df_p = pd.read_excel(f_pp)
                matriz = df_p.groupby('PP')['Cursos_Requeridos'].apply(lambda l: [str(i).strip() for i in l if str(i).lower() != 'nan']).to_dict()
                st.session_state.config["matriz_cursos"] = {str(k).strip(): v for k, v in matriz.items()}
                st.session_state.config["perfiles"] = list(st.session_state.config["matriz_cursos"].keys())
            guardar_datos('config.json', st.session_state.config); st.success("✅ Sincronizado")
