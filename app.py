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
        .stButton>button {{ background-color: {cp} !important; color: white !important; border-radius: 10px; font-weight: bold; width: 100%; }}
        .report-box {{ background-color: #1E1E1E; padding: 25px; border-radius: 10px; border-left: 5px solid {cp}; margin-top: 20px; color: white; }}
        .stNumberInput label, .stSlider label {{ color: #FFFFFF !important; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)

aplicar_estilos()

# --- MOTOR IA ---
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
        return "Error de proveedor."
    except Exception as e: return f"❌ Error: {str(e)}"

# --- BARRA LATERAL ---
with st.sidebar:
    if st.session_state.config.get("logo_base64"):
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_base64"]}" width="100%">', unsafe_allow_html=True)
    menu = st.radio("MÓDULOS DE GESTIÓN", ["⚙️ Configuración", "👤 Análisis Individual", "📦 Análisis Masivo", "📈 ROI Potente", "📜 Historial"])

# --- MODULOS ---
if menu == "⚙️ Configuración":
    st.header("⚙️ Configuración General")
    c1, c2, c3 = st.columns(3)
    with c1: st.session_state.config["api_proveedor"] = st.selectbox("IA Engine", list(PROVEEDORES.keys()))
    with c2: st.session_state.config["api_key"] = st.text_input("API Key", value=st.session_state.config["api_key"], type="password")
    with c3: st.session_state.config["api_modelo"] = st.selectbox("Modelo", PROVEEDORES[st.session_state.config["api_proveedor"]])

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1: f_col = st.file_uploader("Cargar Colaboradores", type=["xlsx"])
    with col2: f_mp = st.file_uploader("Cargar Macroprocesos", type=["xlsx"])
    with col3: f_pp = st.file_uploader("Cargar Perfiles", type=["xlsx"])

    if st.button("💾 SINCRONIZAR DATOS"):
        if f_col: st.session_state.config["colaboradores_data"] = pd.read_excel(f_col).to_dict('records')
        if f_pp:
            df_pp = pd.read_excel(f_pp)
            matriz = df_pp.groupby('PP')['Cursos_Requeridos'].apply(lambda x: [str(i).strip() for i in x if str(i).lower() != 'nan']).to_dict()
            st.session_state.config["matriz_cursos"] = {str(k).strip(): v for k, v in matriz.items()}
            st.session_state.config["perfiles"] = list(st.session_state.config["matriz_cursos"].keys())
        guardar_datos('config.json', st.session_state.config)
        st.success("✅ Matrices sincronizadas correctamente.")

elif menu == "👤 Análisis Individual":
    st.header("👤 Reporte de Avance Individual")
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
                st.write(f"**Cursos Obligatorios para {perfil}:**")
                check_c = {}
                c1, c2 = st.columns(2)
                for i, c in enumerate(cursos):
                    with (c1 if i%2==0 else c2): check_c[c] = st.checkbox(c, key=f"ci_{i}")
                
                if st.button("🚀 GENERAR ANÁLISIS"):
                    aprobados = [k for k, v in check_c.items() if v]
                    pendientes = [k for k, v in check_c.items() if not v]
                    avance = round((len(aprobados)/len(cursos))*100, 2)
                    prompt = f"Analiza impacto para DEYFOR. Colaborador: {colab}. Perfil: {perfil}. CC: {info['CC']}. MP: {info['MP']}. Avance: {avance}%. Cursos faltantes: {pendientes}. Sin fórmulas, directo al grano."
                    with st.spinner("Analizando..."):
                        res = llamar_ia(prompt)
                        st.markdown(f'<div class="report-box">### {colab}<br>**CC:** {info["CC"]} | **MP:** {info["MP"]} | **Avance:** {avance}%<hr>{res}</div>', unsafe_allow_html=True)
                        st.session_state.historial.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "sujeto": colab, "resultado": res})
                        guardar_datos('historial.json', st.session_state.historial)

elif menu == "📦 Análisis Masivo":
    st.header("📦 Matriz por Perfil")
    perfil_sel = st.selectbox("Seleccionar Perfil", ["--"] + st.session_state.config.get("perfiles", []))
    if perfil_sel != "--":
        cursos_p = st.session_state.config.get("matriz_cursos", {}).get(perfil_sel, [])
        st.subheader(f"Cursos para: {perfil_sel}")
        for c in cursos_p: st.markdown(f"✅ {c}")

# --- MODULO 4: ROI POTENTE (ACTUALIZADO) ---
elif menu == "📈 ROI Potente":
    st.header("📈 Calculadora de Retorno de Inversión (ROI)")
    st.write("Complete los datos para generar un análisis financiero y estratégico del impacto de la capacitación.")
    
    with st.container():
        st.subheader("📋 Datos de la Capacitación")
        c1, c2, c3 = st.columns(3)
        with c1: nom_cap = st.text_input("Nombre de la Capacitación", placeholder="Ej. Manejo Defensivo")
        with c2: costo_cap = st.number_input("Costo Total (S/.)", min_value=0.0, step=100.0)
        with c3: cant_part = st.number_input("Número de Participantes", min_value=1, step=1)
        
        st.markdown("---")
        st.subheader("💰 Beneficios Esperados (Estimados)")
        st.info("Estime los ahorros y beneficios monetarios que generará esta capacitación anualmente.")
        
        b1, b2 = st.columns(2)
        with b1:
            ahorro_acc = st.number_input("Ahorros por Reducción de Accidentes (S/.)", help="Considere gastos médicos, multas y días perdidos evitados.", min_value=0.0)
            inc_prod = st.number_input("Incremento en Productividad (S/.)", help="Valor monetario del aumento en la eficiencia del personal.", min_value=0.0)
        with b2:
            red_err = st.number_input("Reducción de Errores / Costos Operativos (S/.)", help="Ahorro por menos reprocesos, mermas o fallas técnicas.", min_value=0.0)
            ahorro_multas = st.number_input("Prevención de Multas / Sanciones Legales (S/.)", help="Ahorro por cumplimiento normativo (SUTRAN, SUNAFIL, etc.)", min_value=0.0)
            
        if st.button("📊 GENERAR ANÁLISIS DE ROI E IMPACTO"):
            if not nom_cap:
                st.error("Por favor, ingrese el nombre de la capacitación.")
            else:
                prompt = f"""
                Actúa como un Consultor Senior de Finanzas y Operaciones para DEYFOR.
                Realiza un análisis de ROI para la capacitación: {nom_cap}.
                
                DATOS:
                - Costo Inversión: S/. {costo_cap}
                - Participantes: {cant_part}
                
                BENEFICIOS ESTIMADOS:
                - Reducción Accidentes: S/. {ahorro_acc}
                - Incremento Productividad: S/. {inc_prod}
                - Reducción Errores/Operativos: S/. {red_err}
                - Prevención Multas: S/. {ahorro_multas}
                
                ENTREGABLE (Sé directo, ejecutivo y no muestres fórmulas):
                1. ROI Porcentual Estimado.
                2. Análisis de Viabilidad (¿Se recupera la inversión rápido?).
                3. Valor estratégico para DEYFOR (Seguridad, Operaciones y Reputación).
                4. Conclusión: ¿Aprobado o Rechazado?
                """
                with st.spinner("IA calculando impacto financiero..."):
                    res = llamar_ia(prompt)
                    st.markdown(f'<div class="report-box">### Análisis de ROI: {nom_cap}<hr>{res}</div>', unsafe_allow_html=True)

elif menu == "📜 Historial":
    st.header("📜 Historial")
    if st.session_state.historial:
        for h in reversed(st.session_state.historial):
            with st.expander(f"{h['fecha']} - {h['sujeto']}"): st.markdown(h['resultado'])
