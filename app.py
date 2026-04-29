import streamlit as st
import pandas as pd
from groq import Groq

# Configuración visual
st.set_page_config(page_title="DNC Analytics | DEYFOR", layout="wide")
st.title("📊 Diagnóstico de Capacitación con IA - DEYFOR")
st.markdown("Plataforma exclusiva para el análisis de brechas operativas.")

# Subir archivo
archivo = st.file_uploader("Sube la matriz Excel (.xlsx o .csv)", type=["csv", "xlsx"])

if archivo:
    if archivo.name.endswith('.csv'):
        df = pd.read_csv(archivo)
    else:
        df = pd.read_excel(archivo)
        
    st.success(f"✅ Archivo cargado: {len(df)} perfiles listos para análisis.")
    st.dataframe(df.head(5))
    
    if st.button("🚀 Generar Diagnóstico Gerencial"):
        with st.spinner("La Inteligencia Artificial está procesando... (toma unos segundos)"):
            try:
                # Se conecta a la llave secreta que pondremos en la nube
                api_key = st.secrets["GROQ_API_KEY"]
                client = Groq(api_key=api_key)
                
                datos = df.to_csv(index=False)
                
                prompt_sistema = "Eres el Director de Talento de Deyfor. Analiza esta matriz y genera un Diagnóstico de Necesidades de Capacitación (DNC) enfocado en seguridad ISO 45001, operaciones y logística."
                
                respuesta = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": f"Matriz a analizar:\n{datos}"}
                    ],
                    model="llama3-70b-8192",
                    temperature=0.3
                )
                
                resultado = respuesta.choices[0].message.content
                st.markdown("---")
                st.markdown(resultado)
                
            except Exception as e:
                st.error(f"❌ Error al conectar con IA. Revisa la clave. Detalle: {e}")