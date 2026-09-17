import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
# Usamos SQLite para desarrollo. 
conn = sqlite3.connect('quiniela_nfl.db', check_same_thread=False)
c = conn.cursor()

# Crear tablas si no existen
c.execute('''
    CREATE TABLE IF NOT EXISTS predicciones (
        usuario TEXT,
        jornada INTEGER,
        partido TEXT,
        prediccion TEXT,
        fecha TIMESTAMP
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS resultados_oficiales (
        jornada INTEGER,
        partido TEXT,
        ganador TEXT
    )
''')
conn.commit()

# --- 2. FUNCIONES LÓGICAS ---
def guardar_prediccion(usuario, jornada, partido, prediccion):
    c.execute("INSERT INTO predicciones VALUES (?, ?, ?, ?, ?)", 
              (usuario, jornada, partido, prediccion, datetime.now()))
    conn.commit()

def actualizar_resultados_api(jornada):
    # MOCKUP: Aquí conectarías una API real (ej. nfl-data-py o ESPN API)
    # Por ahora, simulamos los resultados oficiales de la semana.
    resultados = [
        (jornada, "Chiefs vs Ravens", "Chiefs"),
        (jornada, "Eagles vs Packers", "Eagles"),
        (jornada, "Cowboys vs Browns", "Cowboys")
    ]
    c.executemany("INSERT OR IGNORE INTO resultados_oficiales VALUES (?, ?, ?)", resultados)
    conn.commit()

def calcular_puntos(jornada):
    df_pred = pd.read_sql(f"SELECT * FROM predicciones WHERE jornada={jornada}", conn)
    df_res = pd.read_sql(f"SELECT * FROM resultados_oficiales WHERE jornada={jornada}", conn)
    
    if df_pred.empty or df_res.empty:
        return pd.DataFrame()
        
    # Cruza las predicciones con los resultados oficiales
    df_merged = pd.merge(df_pred, df_res, on=['jornada', 'partido'], how='inner')
    
    # 1 Punto si la predicción coincide con el ganador
    df_merged['acierto'] = (df_merged['prediccion'] == df_merged['ganador']).astype(int)
    
    # Sumar puntos por amigo
    puntos = df_merged.groupby('usuario')['acierto'].sum().reset_index()
    puntos.columns = ['Jugador', 'Puntos']
    return puntos.sort_values(by='Puntos', ascending=False)

# --- 3. INTERFAZ WEB (STREAMLIT) ---
st.set_page_config(page_title="Quiniela NFL 2026", page_icon="🏈")
st.title("🏈 Quiniela NFL 2026/27")

# Menú lateral de navegación
menu = st.sidebar.radio("Navegación", ["📝 Hacer Picks", "🏆 Standings", "⚙️ Admin Resultados"])

if menu == "📝 Hacer Picks":
    st.header("Ingresa tus predicciones de la semana")
    usuario = st.text_input("Tu Nombre:")
    jornada = st.number_input("Jornada (Semana):", min_value=1, max_value=18, value=1)
    
    st.subheader(f"Partidos de la Semana {jornada}")
    # En la versión final, esta lista de partidos la sacarías de tu API.
    partidos = ["Chiefs vs Ravens", "Eagles vs Packers", "Cowboys vs Browns"]
    
    predicciones = {}
    for partido in partidos:
        equipos = partido.split(" vs ")
        predicciones[partido] = st.radio(f"¿Quién gana en el {partido}?", equipos, key=partido)
        
    if st.button("Guardar Mis Picks"):
        if usuario:
            for partido, pick in predicciones.items():
                guardar_prediccion(usuario, jornada, partido, pick)
            st.success(f"¡Listo {usuario}! Tus picks fueron registrados.")
            st.balloons()
        else:
            st.error("Por favor ingresa tu nombre antes de guardar.")

elif menu == "🏆 Standings":
    st.header("Tabla de Posiciones")
    jornada_ver = st.number_input("Ver puntos de la Jornada:", min_value=1, max_value=18, value=1)
    
    tabla = calcular_puntos(jornada_ver)
    if not tabla.empty:
        st.dataframe(tabla, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay resultados calculados para esta jornada.")

elif menu == "⚙️ Admin Resultados":
    st.header("Sincronizar con la NFL")
    st.write("Solo el administrador debe usar esto para jalar los resultados oficiales al terminar la jornada.")
    jornada_admin = st.number_input("Jornada a actualizar:", min_value=1, max_value=18, value=1)
    
    if st.button("Descargar Resultados Oficiales"):
        actualizar_resultados_api(jornada_admin)
        st.success("¡Resultados actualizados y puntos calculados!")
