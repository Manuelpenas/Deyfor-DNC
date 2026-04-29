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
    "OpenRouter": ["meta-llama/llama-3.3-70b-instruct", "google/gemini-2.0-flash-001"],
    "NVIDIA": ["meta/llama-3.1-405b-instruct", "nvidia/llama-3.1-nemotron-70b-instruct"]
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
    # Se establece Análisis Individual como la primera opción
    menu = st.radio("GESTIÓN DEYFOR", ["👤 Análisis Individual", "📦 Perfiles y Cursos", "📈 ROI Potente", "📋 Módulo PDP", "📜 Historial", "⚙️ Configuración"])

# --- MODULO 1: ANÁLISIS INDIVIDUAL (HOME) ---
if menu == "👤 Análisis Individual":
    st.header("👤 Análisis Individual y Desarrollo")
    data = st.session_state.config.get("colaboradores_data", [])
    if not data: st.warning("Por favor, cargue los datos en la sección de Configuración.")
    else:
        df = pd.DataFrame(data)
        colab = st.selectbox("Seleccionar Colaborador", ["--"] + df['Nombre'].tolist())
        if colab != "--":
            info = df[df['Nombre'] == colab].iloc[0]
            perfil = str(info['PP']).strip()
            cursos = st.session_state.config.get("matriz_cursos", {}).get(perfil, [])
            
            st.info(f"📍 Perfil: {perfil} | CC: {info['CC']} | MP: {info['MP']}")
            
            if not cursos: st.error("No hay cursos configurados.")
            else:
                check_c = {}
                c1, c2 = st.columns(2)
                for i, c in enumerate(cursos):
                    with (c1 if i%2==0 else c2): check_c[c] = st.checkbox(c, key=f"ci_{i}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🚀 GENERAR REPORTE DE BRECHAS"):
                        aprobados = [k for k, v in check_c.items() if v]
                        pendientes = [k for k, v in check_c.items() if not v]
                        avance = round((len(aprobados)/len(cursos))*100, 2) if cursos else 0
                        prompt = f"Consultor DEYFOR. Colaborador: {colab}. Perfil: {perfil}. CC: {info['CC']}. MP: {info['MP']}. Avance: {avance}%. Cursos faltantes: {pendientes}. Análisis ejecutivo."
                        with st.spinner("Analizando..."):
                            res = llamar_ia(prompt)
                            st.markdown(f'<div class="report-box">### {colab} - {avance}% Avance\n\n{res}</div>', unsafe_allow_html=True)
                            st.session_state.historial.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "sujeto": colab, "resultado": res})
                            guardar_datos('historial.json', st.session_state.historial)

                with col_btn2:
                    if st.button("📄 GENERAR PDP (PLAN DE DESARROLLO)"):
                        pendientes = [k for k, v in check_c.items() if not v]
                        prompt_pdp = f"""Actúa como el Jefe de Manuel Wilfredo Penas Culqui en DEYFOR. Genera un PDP basado en el modelo ABInBev.
                        DATOS DEL EMPLEADO:
                        Nombre: {colab}
                        Posición: {perfil}
                        Macroproceso: {info['MP']}
                        
                        ESTRUCTURA REQUERIDA (Al estilo ABInBev):
                        1. OBJETIVOS DE LIDERAZGO (Definir 3: Soñar en Grande, Desarrollar personas, Lograr Sostenibilidad).
                        2. OBJETIVOS TÉCNICOS: Basados en completar {pendientes}.
                        3. PLAN DE ACCIÓN: Detallar experiencias en el puesto y entrenamiento formal.
                        4. HERRAMIENTAS DIGITALES: Mencionar uso de Power BI, Dashboards o Chatbots para mejora de indicadores OTIF/NPS.
                        
                        Relaciona todo directamente a las operaciones de DEYFOR."""
                        
                        with st.spinner("Creando Plan de Desarrollo..."):
                            pdp_text = llamar_ia(prompt_pdp)
                            st.markdown(f'<div class="report-box">### PLAN DE DESARROLLO PERSONAL - {colab}\n\n{pdp_text}</div>', unsafe_allow_html=True)
                            # Guardar en el nuevo módulo PDP
                            st.session_state.pdp_history.append({
                                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "empleado": colab,
                                "pdp": pdp_text
                            })
                            guardar_datos('pdp_history.json', st.session_state.pdp_history)

# --- MODULO PDP GUARDADOS ---
elif menu == "📋 Módulo PDP":
    st.header("📋 Planes de Desarrollo Personal Guardados")
    if not st.session_state.pdp_history:
        st.info("No se han generado planes de desarrollo aún.")
    else:
        for p in reversed(st.session_state.pdp_history):
            with st.expander(f"{p['fecha']} - {p['empleado']}"):
                st.markdown(p['pdp'])
                st.download_button("📥 Descargar Plan (TXT)", p['pdp'], file_name=f"PDP_{p['empleado']}_{p['fecha']}.txt")

# --- CONFIGURACIÓN CON CONTRASEÑA ---
elif menu == "⚙️ Configuración":
    st.header("⚙️ Configuración del Sistema")
    if not st.session_state.autenticado:
        pwd = st.text_input("Ingrese Contraseña de Administrador", type="password")
        if st.button("Acceder"):
            if pwd == "D3yf0rE1RL":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña Incorrecta")
    else:
        if st.button("🔒 Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()
            
        st.subheader("Identidad Visual")
        cv1, cv2 = st.columns(2)
        with cv1:
            f_logo = st.file_uploader("Subir Logo", type=["png", "jpg"])
            if f_logo: st.session_state.config["logo_base64"] = base64.b64encode(f_logo.read()).decode()
        with cv2:
            f_fav = st.file_uploader("Subir Favicon", type=["ico", "png"])
            if f_fav: st.session_state.config["favicon_base64"] = base64.b64encode(f_fav.read()).decode()

        st.markdown("---")
        st.subheader("Conexión de IA")
        c1, c2, c3 = st.columns(3)
        with c1: st.session_state.config["api_proveedor"] = st.selectbox("IA Engine", list(PROVEEDORES.keys()))
        with c2: st.session_state.config["api_key"] = st.text_input("API Key", value=st.session_state.config["api_key"], type="password")
        with c3: st.session_state.config["api_modelo"] = st.selectbox("Modelo", PROVEEDORES.get(st.session_state.config["api_proveedor"], ["Cargando..."]))

        st.markdown("---")
        st.subheader("Matrices de Datos")
        col1, col2, col3 = st.columns(3)
        with col1: f_col = st.file_uploader("Cargar Colaboradores", type=["xlsx"])
        with col2: f_mp = st.file_uploader("Cargar Macroprocesos", type=["xlsx"])
        with col3: f_pp = st.file_uploader("Cargar Perfiles Base", type=["xlsx"])

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
            st.success("✅ Datos sincronizados correctamente.")

# --- OTROS MÓDULOS ---
elif menu == "📦 Perfiles y Cursos":
    st.header("📦 Gestión de Perfiles")
    p_sel = st.selectbox("Perfil", ["--"] + st.session_state.config.get("perfiles", []))
    if p_sel != "--":
        for c in st.session_state.config["matriz_cursos"].get(p_sel, []): st.markdown(f"✅ {c}")

elif menu == "📈 ROI Potente":
    st.header("📈 Calculadora ROI")
    costo = st.number_input("Inversión S/.", 0.0)
    if st.button("Calcular"):
        st.write(llamar_ia(f"ROI DEYFOR para inversión de S/.{costo}."))

elif menu == "📜 Historial":
    st.header("📜 Historial de Reportes")
    if st.session_state.historial:
        for h in reversed(st.session_state.historial):
            with st.expander(f"{h['fecha']} - {h['sujeto']}"): st.markdown(h['resultado'])
