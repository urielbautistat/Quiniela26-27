import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import pytz
import requests

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
conn = sqlite3.connect('quiniela_nfl.db', check_same_thread=False)
c = conn.cursor()

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

# --- 2. CONFIGURACIÓN DEL CALENDARIO (SOLO FECHAS LÍMITE) ---
tz_mx = pytz.timezone('America/Mexico_City')

CALENDARIO_LIMITES = {
    1: tz_mx.localize(datetime(2026, 9, 10, 17, 0)),
    2: tz_mx.localize(datetime(2026, 9, 17, 17, 0)),
    3: tz_mx.localize(datetime(2026, 9, 24, 17, 0)),
    4: tz_mx.localize(datetime(2026, 10, 1, 17, 0)),
    5: tz_mx.localize(datetime(2026, 10, 8, 17, 0)),
    6: tz_mx.localize(datetime(2026, 10, 15, 17, 0)),
    7: tz_mx.localize(datetime(2026, 10, 22, 17, 0)),
    8: tz_mx.localize(datetime(2026, 10, 29, 17, 0)),
    9: tz_mx.localize(datetime(2026, 11, 5, 17, 0)),
    10: tz_mx.localize(datetime(2026, 11, 12, 17, 0)),
    11: tz_mx.localize(datetime(2026, 11, 19, 17, 0)),
    12: tz_mx.localize(datetime(2026, 11, 26, 17, 0)),
    13: tz_mx.localize(datetime(2026, 12, 3, 17, 0)),
    14: tz_mx.localize(datetime(2026, 12, 10, 17, 0)),
    15: tz_mx.localize(datetime(2026, 12, 17, 17, 0)),
    16: tz_mx.localize(datetime(2026, 12, 24, 17, 0)),
    17: tz_mx.localize(datetime(2026, 12, 31, 17, 0)),
    18: tz_mx.localize(datetime(2027, 1, 7, 17, 0))
}

# --- 3. FUNCIONES DE AUTOMATIZACIÓN CON ESPN API ---
def obtener_partidos_api(jornada):
    url = f"http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2026&seasontype=2&week={jornada}"
    try:
        respuesta = requests.get(url)
        datos = respuesta.json()
        partidos = []
        for evento in datos.get('events', []):
            equipos = evento['competitions'][0]['competitors']
            eq1 = equipos[0]['team']['name'] 
            eq2 = equipos[1]['team']['name']
            partidos.append(f"{eq1} vs {eq2}")
        return partidos
    except:
        return []

def actualizar_resultados_api(jornada):
    url = f"http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2026&seasontype=2&week={jornada}"
    try:
        respuesta = requests.get(url).json()
        resultados = []
        for evento in respuesta.get('events', []):
            equipos = evento['competitions'][0]['competitors']
            eq1 = equipos[0]
            eq2 = equipos[1]
            
            nombre_partido = f"{eq1['team']['name']} vs {eq2['team']['name']}"
            
            ganador = None
            if eq1.get('winner') == True:
                ganador = eq1['team']['name']
            elif eq2.get('winner') == True:
                ganador = eq2['team']['name']
            
            if ganador:
                resultados.append((jornada, nombre_partido, ganador))
                
        if resultados:
            c.executemany("INSERT OR IGNORE INTO resultados_oficiales VALUES (?, ?, ?)", resultados)
            conn.commit()
            return len(resultados)
        return 0
    except:
        return -1

# --- 4. FUNCIONES LÓGICAS DE BASE DE DATOS ---
ahora = datetime.now(tz_mx)
jornada_activa = 1
for j in range(1, 19):
    if ahora < CALENDARIO_LIMITES[j]:
        jornada_activa = j
        break
else:
    jornada_activa = 18

def ya_participo(usuario, jornada):
    c.execute("SELECT COUNT(*) FROM predicciones WHERE LOWER(usuario)=? AND jornada=?", (usuario.lower(), jornada))
    return c.fetchone()[0] > 0

def guardar_prediccion(usuario, jornada, partido, prediccion):
    c.execute("INSERT INTO predicciones VALUES (?, ?, ?, ?, ?)", 
              (usuario, jornada, partido, prediccion, datetime.now(tz_mx)))
    conn.commit()

def calcular_puntos(jornada):
    df_pred = pd.read_sql(f"SELECT * FROM predicciones WHERE jornada={jornada}", conn)
    df_res = pd.read_sql(f"SELECT * FROM resultados_oficiales WHERE jornada={jornada}", conn)
    
    if df_pred.empty or df_res.empty:
        return pd.DataFrame()
        
    df_merged = pd.merge(df_pred, df_res, on=['jornada', 'partido'], how='inner')
    df_merged['acierto'] = (df_merged['prediccion'] == df_merged['ganador']).astype(int)
    puntos = df_merged.groupby('usuario')['acierto'].sum().reset_index()
    puntos.columns = ['Jugador', 'Puntos']
    return puntos.sort_values(by='Puntos', ascending=False)

# --- 5. INTERFAZ WEB (STREAMLIT) ---
st.set_page_config(page_title="Quiniela NFL 2026", page_icon="🏈")
st.title("🏈 Quiniela NFL 2026/27")

menu = st.sidebar.radio("Navegación", ["📝 Hacer Picks", "🏆 Standings", "⚙️ Admin Resultados"])

if menu == "📝 Hacer Picks":
    st.header("Ingresa tus predicciones de la semana")
    usuario = st.text_input("Tu Nombre (usa siempre el mismo):")
    jornada = st.number_input("Jornada (Semana):", min_value=1, max_value=18, value=jornada_activa) 
    
    limite = CALENDARIO_LIMITES[jornada]
    st.info(f"Tienes hasta el **{limite.strftime('%d/%m/%Y a las %H:%M')} hrs (CDMX)** para meter tus picks.")
    
    if ahora > limite:
        st.error("⚠️ El tiempo para meter quinielas en esta jornada ha terminado.")
    else:
        if usuario and ya_participo(usuario, jornada):
            st.warning(f"Oye {usuario}, ya registraste tus picks para la Jornada {jornada}. ¡Suerte!")
        else:
            partidos = obtener_partidos_api(jornada)
            
            if not partidos:
                st.warning("Cargando partidos oficiales... si esto no cambia, revisa tu conexión.")
            else:
                st.subheader(f"Partidos Oficiales de la Semana {jornada}")
                predicciones = {}
                
                for partido in partidos:
                    equipos = partido.split(" vs ")
                    predicciones[partido] = st.selectbox(f"{partido}", ["Selecciona ganador..."] + equipos, key=partido)
                    
                if st.button("Guardar Mis Picks"):
                    if not usuario:
                        st.error("Por favor ingresa tu nombre antes de guardar.")
                    else:
                        if "Selecciona ganador..." in predicciones.values():
                            st.error("¡Te falta seleccionar el ganador de algunos partidos!")
                        else:
                            for partido, pick in predicciones.items():
                                guardar_prediccion(usuario, jornada, partido, pick)
                            
                            st.success(f"¡Listo {usuario}! Tus picks fueron registrados exitosamente.")
                            st.balloons()
                            
                            # --- NUEVA SECCIÓN: COMPROBANTE ---
                            st.divider()
                            st.subheader("🧾 Tu Comprobante Oficial")
                            st.write("Tómale captura de pantalla a esto o descarga tu recibo.")
                            
                            df_comprobante = pd.DataFrame(list(predicciones.items()), columns=["Partido", "Tu Elección"])
                            st.table(df_comprobante)
                            
                            fecha_hora = datetime.now(tz_mx).strftime('%d/%m/%Y a las %H:%M:%S')
                            texto_recibo = f"--- QUINIELA NFL 2026/27 ---\n"
                            texto_recibo += f"Jugador: {usuario}\n"
                            texto_recibo += f"Jornada: {jornada}\n"
                            texto_recibo += f"Registrado el: {fecha_hora} (CDMX)\n"
                            texto_recibo += f"----------------------------\n\n"
                            for p, eleccion in predicciones.items():
                                texto_recibo += f"{p}  👉  {eleccion}\n"
                            texto_recibo += f"\n¡Mucha suerte!"
                            
                            st.download_button(
                                label="📥 Descargar recibo de picks",
                                data=texto_recibo,
                                file_name=f"Quiniela_{usuario}_Jornada{jornada}.txt",
                                mime="text/plain"
                            )

elif menu == "🏆 Standings":
    st.header("Tabla de Posiciones")
    jornada_ver = st.number_input("Ver puntos de la Jornada:", min_value=1, max_value=18, value=jornada_activa)
    tabla = calcular_puntos(jornada_ver)
    if not tabla.empty:
        st.dataframe(tabla, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay resultados para esta jornada (quizás los partidos no han terminado o el Admin no los ha actualizado).")

elif menu == "⚙️ Admin Resultados":
    st.header("Sincronizar con la NFL (ESPN API)")
    st.write("Al hacer clic, el sistema buscará los ganadores reales en la base de datos de ESPN y calculará los puntos.")
    
    jornada_admin = st.number_input("Jornada a actualizar:", min_value=1, max_value=18, value=jornada_activa)
    if st.button("Buscar y Guardar Resultados"):
        partidos_terminados = actualizar_resultados_api(jornada_admin)
        if partidos_terminados > 0:
            st.success(f"¡Éxito! Se actualizaron los resultados de {partidos_terminados} partidos terminados. Revisa los Standings.")
            st.balloons()
        elif partidos_terminados == 0:
            st.warning("No se encontraron partidos terminados para esta semana todavía.")
        else:
            st.error("Hubo un error conectándose a ESPN.")
