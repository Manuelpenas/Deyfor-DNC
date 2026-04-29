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
        .stButton>button {{ background-color: {cp} !important; color: white !important; border-radius: 8px; width: 100%; }}
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

def llamar_ia(prompt):
    prov = st.session_state.config["api_proveedor"]
    key = st.session_state.config["api_key"]
    if not key: return "⚠️ Configura la API Key."
    try:
        client = Groq(api_key=key) if prov == "Groq" else OpenAI(api_key=key)
        model = "llama3-70b-8192" if prov == "Groq" else "gpt-4"
        response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=model)
        return response.choices[0].message.content
    except Exception as e: return f"❌ Error: {str(e)}"

# --- MÓDULO 1: CONFIGURACIÓN ---
if menu == "⚙️ Configuración":
    st.header("⚙️ Gestión de Matrices")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Identidad")
        logo = st.file_uploader("Logo", type=["png", "jpg"])
        if logo: st.session_state.config["logo_base64"] = base64.b64encode(logo.read()).decode()
        favicon = st.file_uploader("Favicon", type=["png", "ico"])
        if favicon: st.session_state.config["favicon_base64"] = base64.b64encode(favicon.read()).decode()
    
    with col2:
        st.subheader("IA")
        st.session_state.config["api_proveedor"] = st.selectbox("Proveedor", ["Groq", "ChatGPT"], index=0)
        st.session_state.config["api_key"] = st.text_input("API Key", value=st.session_state.config["api_key"], type="password")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Colaboradores**\n(DNI|Nombre|PP|CC|MP)")
        f_col = st.file_uploader("Excel Colaboradores", type=["xlsx"])
    with c2:
        st.markdown("**2. Macroprocesos**\n(MP|Detalle)")
        f_mp = st.file_uploader("Excel Macroprocesos", type=["xlsx"])
    with c3:
        st.markdown("**3. Perfiles y Cursos**\n(PP|Cursos_Requeridos)")
        f_pp = st.file_uploader("Excel Perfiles", type=["xlsx"])

    if st.button("💾 GUARDAR Y ACTUALIZAR"):
        exito = True
        if f_col:
            st.session_state.config["colaboradores_data"] = pd.read_excel(f_col).to_dict('records')
        if f_mp:
            df_mp = pd.read_excel(f_mp)
            st.session_state.config["macroprocesos"] = df_mp['MP'].unique().tolist()
            st.session_state.config["detalles_mp"] = pd.Series(df_mp.Detalle.values, index=df_mp.MP).to_dict()
        if f_pp:
            df_pp = pd.read_excel(f_pp)
            if 'PP' in df_pp.columns and 'Cursos_Requeridos' in df_pp.columns:
                st.session_state.config["perfiles"] = [str(x).strip() for x in df_pp['PP'].unique().tolist()]
                nueva_matriz = {}
                for _, row in df_pp.iterrows():
                    p_nombre = str(row['PP']).strip()
                    c_texto = str(row['Cursos_Requeridos'])
                    # Separar por coma y limpiar cada curso
                    lista_cursos = [c.strip() for c in c_texto.split(',') if c.strip() and c.lower() != 'nan']
                    nueva_matriz[p_nombre] = lista_cursos
                st.session_state.config["matriz_cursos"] = nueva_matriz
            else:
                st.error("❌ El Excel de Perfiles debe tener columnas 'PP' y 'Cursos_Requeridos'")
                exito = False
            
        if exito:
            guardar_datos('config.json', st.session_state.config)
            st.success("✅ Datos sincronizados correctamente.")
            st.rerun()

# --- MÓDULO 2: ANÁLISIS INDIVIDUAL ---
elif menu == "👤 Análisis Individual":
    st.header("👤 Análisis de Brechas")
    data_colabs = st.session_state.config.get("colaboradores_data", [])
    
    if not data_colabs:
        st.warning("⚠️ Primero carga los Colaboradores en Configuración.")
    else:
        df_c = pd.DataFrame(data_colabs)
        # Limpiar nombres de perfiles en la data de colabs por si acaso
        df_c['PP'] = df_c['PP'].astype(str).str.strip()
        
        seleccionado = st.selectbox("Seleccione Colaborador", ["-- Seleccione --"] + df_c['Nombre'].tolist())
        
        if seleccionado != "-- Seleccione --":
            info = df_c[df_c['Nombre'] == seleccionado].iloc[0]
            perfil_buscado = info['PP']
            
            st.info(f"📍 **Perfil:** {perfil_buscado} | **CC:** {info['CC']} | **MP:** {info['MP']}")
            
            # Buscar cursos en la matriz
            matriz = st.session_state.config.get("matriz_cursos", {})
            cursos_perfil = matriz.get(perfil_buscado, [])
            
            if not cursos_perfil:
                st.error(f"❌ No se encontraron cursos para el perfil '{perfil_buscado}'.")
                st.info("Verifica que el nombre del perfil en el Excel de Colaboradores sea idéntico al del Excel de Perfiles.")
            else:
                st.subheader(f"📚 Cursos Obligatorios ({len(cursos_perfil)})")
                st.write("Marque los cursos que el colaborador ya completó:")
                
                check_cursos = {}
                # Mostrar en 2 columnas
                cols = st.columns(2)
                for i, curso in enumerate(cursos_perfil):
                    with cols[i % 2]:
                        check_cursos[curso] = st.checkbox(curso, key=f"chk_{i}")
                
                if st.button("🚀 GENERAR REPORTE DE IA"):
                    aprobados = [c for c, v in check_cursos.items() if v]
                    pendientes = [c for c, v in check_cursos.items() if not v]
                    
                    prompt = f"""Consultor SSOMA DEYFOR. 
                    Analiza a: {seleccionado}
                    Cargo: {perfil_buscado}
                    Macroproceso: {info['MP']}
                    Cursos Realizados: {aprobados}
                    Cursos Faltantes: {pendientes}
                    
                    Genera un informe con:
                    1. Porcentaje de cumplimiento.
                    2. Análisis de riesgos por competencias faltantes.
                    3. Plan de acción recomendado."""
                    
                    with st.spinner("IA procesando matriz..."):
                        res = llamar_ia(prompt)
                        st.markdown(res)
                        # Guardar en historial
                        st.session_state.historial.append({
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "sujeto": seleccionado, "perfil": perfil_buscado, "resultado": res
                        })
                        guardar_datos('historial.json', st.session_state.historial)

# --- MANTENER OTROS MÓDULOS IGUAL ---
elif menu == "💰 Calculadora ROI":
    st.header("💰 Calculadora ROI")
    with st.form("roi"):
        c1, c2 = st.columns(2)
        with c1: cost = st.number_input("Inversión S/.", 0.0)
        with c2: prod = st.slider("% Mejora Productividad", 0, 100, 10)
        if st.form_submit_button("Analizar"):
            st.write(llamar_ia(f"ROI para inversión de S/.{cost} con mejora de {prod}% en productividad."))

elif menu == "📜 Historial":
    st.header("📜 Historial")
    if st.session_state.historial:
        for i, reg in enumerate(reversed(st.session_state.historial)):
            with st.expander(f"{reg['fecha']} - {reg['sujeto']}"):
                st.markdown(reg['resultado'])
