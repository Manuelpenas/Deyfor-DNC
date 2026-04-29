import streamlit as st
import pandas as pd
import json
import os
from groq import Groq
from openai import OpenAI
import base64
from datetime import datetime

# --- FUNCIONES DE PERSISTENCIA ---
def guardar_datos(archivo, datos):
    with open(archivo, 'w') as f:
        json.dump(datos, f)

def cargar_datos(archivo, defecto):
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            return json.load(f)
    return defecto

# --- INICIALIZACIÓN DE ESTADOS ---
if "config" not in st.session_state:
    st.session_state.config = cargar_datos('config.json', {
        "color_primario": "#1F4E78",
        "api_proveedor": "Groq",
        "api_key": "",
        "logo_base64": "",
        "favicon_base64": ""
    })

if "historial" not in st.session_state:
    st.session_state.historial = cargar_datos('historial.json', [])

if "master_data" not in st.session_state:
    st.session_state.master_data = None

# --- CONFIGURACIÓN VISUAL DINÁMICA ---
def aplicar_estilos():
    cp = st.session_state.config["color_primario"]
    st.markdown(f"""
        <style>
        .stApp {{ background-color: white; }}
        .stButton>button {{ background-color: {cp}; color: white; border-radius: 8px; }}
        h1, h2, h3 {{ color: {cp}; }}
        .css-10trblm {{ color: {cp}; }} /* Color de sidebar */
        </style>
    """, unsafe_allow_html=True)

aplicar_estilos()

# --- BARRA LATERAL (NAVEGACIÓN) ---
with st.sidebar:
    if st.session_state.config["logo_base64"]:
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_base64"]}" width="100%">', unsafe_allow_html=True)
    
    st.title("DEYFOR TMS v2")
    menu = st.radio("Módulos del Sistema", 
        ["⚙️ Configuración", "👤 Análisis Individual", "📦 Análisis Masivo", "💰 Calculadora ROI", "📜 Historial"])

# --- LÓGICA DE INTELIGENCIA ARTIFICIAL ---
def llamar_ia(prompt):
    prov = st.session_state.config["api_proveedor"]
    key = st.session_state.config["api_key"]
    
    if not key:
        return "⚠️ Error: Configura tu API Key en el módulo de Configuración."

    try:
        if prov == "Groq":
            client = Groq(api_key=key)
            model = "llama3-70b-8192"
        else: # ChatGPT / OpenRouter / Otros (Usa estandar OpenAI)
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
        st.subheader("Imagen y Marca")
        logo = st.file_uploader("Subir Logo (PNG/JPG)", type=["png", "jpg"])
        if logo:
            st.session_state.config["logo_base64"] = base64.b64encode(logo.read()).decode()
        
        color = st.color_picker("Color Principal del Sistema", st.session_state.config["color_primario"])
        st.session_state.config["color_primario"] = color

    with col2:
        st.subheader("Conectividad IA")
        proveedor = st.selectbox("Proveedor de IA", 
            ["Groq", "ChatGPT", "NVIDIA", "OpenRouter", "Gemini", "Claude"])
        st.session_state.config["api_proveedor"] = proveedor
        
        key = st.text_input("API Key del Proveedor", value=st.session_state.config["api_key"], type="password")
        st.session_state.config["api_key"] = key

    st.subheader("Base de Datos Maestra")
    archivo_maestro = st.file_uploader("Subir Excel de Perfiles (167 filas)", type=["xlsx"])
    if archivo_maestro:
        st.session_state.master_data = pd.read_excel(archivo_maestro)
        st.success("✅ Base de datos cargada.")

    if st.button("Guardar Configuración"):
        guardar_datos('config.json', st.session_state.config)
        st.rerun()

# --- MÓDULO 2: ANÁLISIS INDIVIDUAL ---
elif menu == "👤 Análisis Individual":
    st.header("👤 Diagnóstico de Brechas Individual")
    
    if st.session_state.master_data is None:
        st.warning("Carga la base de datos en Configuración primero.")
    else:
        nombre = st.text_input("Nombre del Colaborador")
        macro = st.selectbox("Macroproceso", st.session_state.master_data.iloc[:,0].unique())
        perfiles_filtrados = st.session_state.master_data[st.session_state.master_data.iloc[:,0] == macro].iloc[:,1].unique()
        perfil = st.selectbox("Perfil de Puesto", perfiles_filtrados)

        st.subheader("Evaluación de Competencias")
        # Aquí simulamos competencias del Excel. Ajusta los índices según tu Excel real.
        competencias = ["Seguridad Minera", "Gestión Logística", "Uso de EPP", "Liderazgo", "Excel Técnico"]
        seleccionadas = {}
        for c in competencias:
            seleccionadas[c] = st.checkbox(f"Domina: {c}")

        if st.button("Analizar con IA"):
            prompt = f"""Analiza las brechas de {nombre} en el puesto {perfil}. 
            Competencias evaluadas: {seleccionadas}. 
            Genera un reporte con: Porcentaje de brecha, competencias faltantes y plan de entrenamiento."""
            
            reporte = llamar_ia(prompt)
            st.markdown(reporte)
            
            # Guardar en historial
            st.session_state.historial.append({
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "tipo": "Individual",
                "sujeto": nombre,
                "perfil": perfil,
                "resultado": reporte
            })
            guardar_datos('historial.json', st.session_state.historial)

# --- MÓDULO 3: ANÁLISIS MASIVO ---
elif menu == "📦 Análisis Masivo":
    st.header("📦 Análisis por Perfil de Puesto")
    if st.session_state.master_data is None:
        st.warning("Carga la base de datos en Configuración primero.")
    else:
        macro = st.selectbox("Seleccionar Macroproceso", st.session_state.master_data.iloc[:,0].unique())
        perfil = st.selectbox("Seleccionar Perfil", st.session_state.master_data.iloc[:,1].unique())
        
        if st.button("Generar Perfil Ideal con IA"):
            prompt = f"Define el perfil ideal de competencias para {perfil} en el macroproceso {macro} para una empresa minera."
            resultado = llamar_ia(prompt)
            st.markdown(resultado)

# --- MÓDULO 4: CALCULADORA ROI ---
elif menu == "💰 Calculadora ROI":
    st.header("💰 Cálculo de Retorno de Inversión (ROI)")
    
    with st.form("roi_form"):
        capacitacion = st.text_input("Nombre de la Capacitación")
        n_part = st.number_input("Número de Participantes", min_value=1)
        costo_total = st.number_input("Costo Total Inversión (S/.)", min_value=0.0)
        
        st.subheader("Beneficios Esperados")
        acc = st.slider("Reducción accidentes (%)", 0, 100, 10)
        prod = st.slider("Incremento productividad (%)", 0, 100, 10)
        err = st.slider("Reducción de errores (%)", 0, 100, 10)
        
        if st.form_submit_button("Calcular ROI con IA"):
            prompt = f"""Calcula el ROI estimado para la capacitación {capacitacion}.
            Inversión: S/. {costo_total}. Participantes: {n_part}.
            Impacto esperado: {acc}% menos accidentes, {prod}% más productividad.
            Da un análisis financiero y estratégico."""
            
            analisis = llamar_ia(prompt)
            st.write(analisis)

# --- MÓDULO 5: HISTORIAL ---
elif menu == "📜 Historial":
    st.header("📜 Historial de Análisis")
    if not st.session_state.historial:
        st.info("No hay registros aún.")
    else:
        df_hist = pd.DataFrame(st.session_state.historial)
        st.dataframe(df_hist[["fecha", "tipo", "sujeto", "perfil"]])
        
        idx = st.number_input("Ver detalle del registro N°", min_value=0, max_value=len(df_hist)-1)
        st.markdown(df_hist.iloc[idx]["resultado"])
