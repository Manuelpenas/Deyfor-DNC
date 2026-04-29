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
        "color_primario": "#2E7D32", 
        "api_proveedor": "Groq",
        "api_key": "",
        "logo_base64": "",
        "macroprocesos": ["Operaciones", "SSOMA", "Logística", "Administración"],
        "perfiles": ["Residente de Obra", "Prevencionista", "Operario", "Supervisor"],
        "personal": ["Juan Perez", "Maria Gomez", "Carlos Ruiz"]
    })

if "historial" not in st.session_state:
    st.session_state.historial = cargar_datos('historial.json', [])

if "master_data" not in st.session_state:
    st.session_state.master_data = None

# --- CONFIGURACIÓN VISUAL DINÁMICA (MODO OSCURO) ---
def aplicar_estilos():
    cp = st.session_state.config["color_primario"]
    st.markdown(f"""
        <style>
        /* Fondo general negro absoluto */
        .stApp {{ background-color: #0E1117; }}
        
        /* Fondo del menú lateral negro más profundo */
        [data-testid="stSidebar"] {{ background-color: #000000; border-right: 1px solid #333; }}
        
        /* Forzar TODAS las letras a blanco */
        h1, h2, h3, h4, h5, h6, p, span, label, div, li {{ color: #FFFFFF !important; }}
        
        /* Botones verdes con texto blanco */
        .stButton>button {{ 
            background-color: {cp} !important; 
            color: #FFFFFF !important; 
            border-radius: 8px; 
            font-weight: bold;
            border: none;
        }}
        .stButton>button:hover {{ 
            background-color: #1B5E20 !important; 
            border: 1px solid #FFFFFF;
        }}
        
        /* Cajas de texto y desplegables en gris oscuro para que combinen */
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div>div {{
            background-color: #1E1E1E !important;
            color: #FFFFFF !important;
            border: 1px solid #444 !important;
        }}
        
        /* Checkboxes y fondos de tablas */
        .stCheckbox>label>span {{ color: #FFFFFF !important; }}
        [data-testid="stDataFrame"] {{ background-color: #1E1E1E !important; }}
        </style>
    """, unsafe_allow_html=True)

aplicar_estilos()

# --- BARRA LATERAL (NAVEGACIÓN) ---
with st.sidebar:
    if st.session_state.config["logo_base64"]:
        st.markdown(f'<img src="data:image/png;base64,{st.session_state.config["logo_base64"]}" width="100%">', unsafe_allow_html=True)
    
    st.title("DEYFOR TMS")
    st.markdown("---")
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
        else: 
            client = OpenAI(api_key=key)
            model = "gpt-4" if prov == "ChatGPT" else "mixtral-8x7b-32768"

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error de IA: Verifica tu clave API. Detalle: {str(e)}"

# --- MÓDULO 1: CONFIGURACIÓN ---
if menu == "⚙️ Configuración":
    st.header("⚙️ Configuración del Sistema")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Imagen y Marca")
        logo = st.file_uploader("Subir Logo (PNG/JPG)", type=["png", "jpg"])
        if logo:
            st.session_state.config["logo_base64"] = base64.b64encode(logo.read()).decode()
        
        color = st.color_picker("Color de Botones", st.session_state.config["color_primario"])
        st.session_state.config["color_primario"] = color

    with col2:
        st.subheader("Conectividad IA")
        proveedor = st.selectbox("Proveedor de IA", 
            ["Groq", "ChatGPT", "Gemini", "Claude", "OpenRouter", "NVIDIA"])
        st.session_state.config["api_proveedor"] = proveedor
        
        key = st.text_input("API Key del Proveedor", value=st.session_state.config["api_key"], type="password")
        st.session_state.config["api_key"] = key

    st.markdown("---")
    st.subheader("📥 Carga de Base de Datos de Deyfor")
    
    # OPCIÓN 1: SUBIR EXCEL
    archivo_maestro = st.file_uploader("Sube tu matriz de Excel (.xlsx) o CSV", type=["xlsx", "csv"])
    if archivo_maestro:
        try:
            if archivo_maestro.name.endswith('.csv'):
                st.session_state.master_data = pd.read_csv(archivo_maestro)
            else:
                st.session_state.master_data = pd.read_excel(archivo_maestro)
            st.success(f"✅ Archivo Excel cargado correctamente. Total filas: {len(st.session_state.master_data)}")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

    # OPCIÓN 2: LISTAS MANUALES
    st.markdown("*(Opcional) Puedes configurar tus listas manualmente aquí:*")
    colA, colB, colC = st.columns(3)
    with colA:
        macros = st.text_area("1. Macroprocesos", "\n".join(st.session_state.config["macroprocesos"]), height=150)
    with colB:
        perfiles = st.text_area("2. Perfiles de Puesto", "\n".join(st.session_state.config["perfiles"]), height=150)
    with colC:
        personal = st.text_area("3. Lista de Personal", "\n".join(st.session_state.config["personal"]), height=150)

    if st.button("💾 Guardar Configuración"):
        st.session_state.config["macroprocesos"] = [x.strip() for x in macros.split('\n') if x.strip()]
        st.session_state.config["perfiles"] = [x.strip() for x in perfiles.split('\n') if x.strip()]
        st.session_state.config["personal"] = [x.strip() for x in personal.split('\n') if x.strip()]
        
        guardar_datos('config.json', st.session_state.config)
        st.success("✅ Configuración guardada exitosamente.")
        st.rerun()

# --- MÓDULO 2: ANÁLISIS INDIVIDUAL ---
elif menu == "👤 Análisis Individual":
    st.header("👤 Diagnóstico de Brechas Individual")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        nombre = st.selectbox("Colaborador", st.session_state.config["personal"])
    with col2:
        macro = st.selectbox("Macroproceso", st.session_state.config["macroprocesos"])
    with col3:
        perfil = st.selectbox("Perfil de Puesto", st.session_state.config["perfiles"])

    st.markdown("---")
    st.subheader("Competencias Actuales (Marca lo que ya domina)")
    
    competencias = ["Normativa ISO 45001", "Trabajos en Altura", "LOTO (Bloqueo y Etiquetado)", "Gestión Logística", "Liderazgo SSOMA", "Manejo Defensivo"]
    seleccionadas = {}
    
    c1, c2 = st.columns(2)
    for i, c in enumerate(competencias):
        if i % 2 == 0:
            with c1: seleccionadas[c] = st.checkbox(c)
        else:
            with c2: seleccionadas[c] = st.checkbox(c)

    if st.button("🧠 Analizar Brechas con IA"):
        with st.spinner("La IA está calculando las brechas..."):
            prompt = f"""Actúa como Consultor Experto en Talento de la empresa minera Deyfor.
            Analiza al colaborador: {nombre}.
            Macroproceso: {macro}. Perfil: {perfil}.
            Competencias que domina actualmente: {[k for k, v in seleccionadas.items() if v]}.
            Competencias de la lista que le faltan: {[k for k, v in seleccionadas.items() if not v]}.
            
            Genera un reporte gerencial que incluya:
            1. Porcentaje estimado de brecha de competencias.
            2. Riesgos operativos de no capacitarlo en lo que le falta.
            3. Recomendaciones y plan de acción."""
            
            reporte = llamar_ia(prompt)
            st.markdown(reporte)
            
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
    st.header("📦 Perfilamiento Estándar por Puesto")
    
    col1, col2 = st.columns(2)
    with col1:
        macro = st.selectbox("Seleccionar Macroproceso", st.session_state.config["macroprocesos"])
    with col2:
        perfil = st.selectbox("Seleccionar Perfil", st.session_state.config["perfiles"])
    
    if st.button("🏗️ Construir Matriz de Puesto con IA"):
        with st.spinner("Consultando estándares de la industria minera..."):
            prompt = f"""Eres el Gerente de Operaciones de Deyfor. 
            Define el perfil ideal de competencias duras y blandas para el puesto de '{perfil}' dentro del macroproceso de '{macro}'.
            Enfócate en requisitos de seguridad (SSOMA), eficiencia y normativas aplicables."""
            
            resultado = llamar_ia(prompt)
            st.markdown(resultado)

# --- MÓDULO 4: CALCULADORA ROI ---
elif menu == "💰 Calculadora ROI":
    st.header("💰 Cálculo de Retorno de Inversión (ROI)")
    
    with st.form("roi_form"):
        col1, col2 = st.columns(2)
        with col1:
            capacitacion = st.text_input("Nombre de la Capacitación")
            n_part = st.number_input("Número de Participantes", min_value=1)
        with col2:
            costo_total = st.number_input("Inversión Total (S/.)", min_value=0.0)
        
        st.markdown("---")
        st.subheader("Beneficios y Ahorros Esperados")
        acc = st.slider("Reducción de Accidentes / Incidentes (%)", 0, 100, 15)
        prod = st.slider("Incremento de Productividad Operativa (%)", 0, 100, 10)
        err = st.slider("Reducción de Errores / Reprocesos (%)", 0, 100, 20)
        
        if st.form_submit_button("📊 Calcular Impacto Financiero con IA"):
            with st.spinner("Procesando viabilidad financiera..."):
                prompt = f"""Actúa como Director Financiero (CFO). Calcula el ROI cualitativo y estimado cuantitativo para:
                Capacitación: {capacitacion}. Participantes: {n_part}. Costo: S/. {costo_total}.
                Proyección de impacto: Reducción accidentes ({acc}%), Aumento productividad ({prod}%), Reducción reprocesos ({err}%).
                
                Entrega un reporte con:
                1. Justificación de la inversión.
                2. Ahorros ocultos proyectados (evitar multas, horas hombre perdidas).
                3. Conclusión de viabilidad (Aprobado/Rechazado)."""
                
                analisis = llamar_ia(prompt)
                st.write(analisis)

# --- MÓDULO 5: HISTORIAL ---
elif menu == "📜 Historial":
    st.header("📜 Historial de Evaluaciones")
    if not st.session_state.historial:
        st.info("No hay registros guardados aún.")
    else:
        df_hist = pd.DataFrame(st.session_state.historial)
        st.dataframe(df_hist[["fecha", "tipo", "sujeto", "perfil"]], use_container_width=True)
        
        st.markdown("---")
        st.subheader("Ver Detalle Completo")
        idx = st.number_input("Ingresa el número de fila (índice) que deseas revisar:", min_value=0, max_value=len(df_hist)-1, step=1)
        
        if st.button("Ver Reporte"):
            st.markdown(f"### Reporte de: {df_hist.iloc[idx]['sujeto']} ({df_hist.iloc[idx]['fecha']})")
            st.markdown(df_hist.iloc[idx]["resultado"])
