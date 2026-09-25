import streamlit as st
import pandas as pd
import gspread
import nfl_data_py as nfl
import datetime
import pytz
import json

# --- CONFIGURACIÓN DE GOOGLE SHEETS (SECRETS) ---
# Carga las credenciales de forma segura desde los Secrets de Streamlit
creds_dict = json.loads(st.secrets["gcp_credentials"])

# Asegura que los saltos de línea tengan el formato exacto que pide Google
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

# Autenticación directa y moderna (sin oauth2client)
cliente_sheets = gspread.service_account_from_dict(creds_dict)
sheet = cliente_sheets.open("Quiniela_NFL_2026").sheet1

# --- OBTENER DATOS DE LA NFL ---
@st.cache_data(ttl=3600) 
def cargar_datos_nfl(semana_actual):
    df_nfl = nfl.import_schedules([2026])
    df_semana = df_nfl[df_nfl['week'] == semana_actual]
    
    partidos = []
    resultados_oficiales = {}
    
    for index, row in df_semana.iterrows():
        equipo_local = row['home_team']
        equipo_visitante = row['away_team']
        nombre_partido = f"{equipo_visitante} @ {equipo_local}"
        partidos.append(nombre_partido)
        
        # Validar quién ganó (si el partido ya terminó)
        if pd.notna(row['home_score']) and pd.notna(row['away_score']):
            if row['home_score'] > row['away_score']:
                resultados_oficiales[nombre_partido] = equipo_local
            elif row['away_score'] > row['home_score']:
                resultados_oficiales[nombre_partido] = equipo_visitante
            else:
                resultados_oficiales[nombre_partido] = "Empate"
                
    return partidos, resultados_oficiales

# --- DISEÑO DE LA PÁGINA (STREAMLIT) ---
st.title("🏈 Quiniela NFL - Temporada 2026/27")

semana_elegida = st.sidebar.number_input("Selecciona la Semana", min_value=1, max_value=18, value=3)
partidos, resultados_reales = cargar_datos_nfl(semana_elegida)

tab1, tab2 = st.tabs(["✍️ Hacer Predicciones", "🏆 Tabla de Posiciones"])

# --- LÓGICA DE TIEMPO LÍMITE ---
# Fecha límite: 24 de septiembre de 2026 a las 23:59:59 (Hora de Ciudad de México)
zona_horaria = pytz.timezone("America/Mexico_City")
fecha_limite = zona_horaria.localize(datetime.datetime(2026, 9, 24, 23, 59, 59))
hora_actual = datetime.datetime.now(zona_horaria)

with tab1:
    st.subheader(f"Predicciones Semana {semana_elegida}")
    
    # Bloquear el formulario si es semana 2 o 3 y ya pasó la fecha límite
    if semana_elegida in [2, 3] and hora_actual > fecha_limite:
        st.error("⚠️ El tiempo para subir o modificar los picks de esta semana ha terminado.")
    else:
        with st.form("form_quiniela"):
            usuario = st.text_input("Ingresa tu nombre:")
            
            predicciones_usuario = {}
            st.write("Selecciona a los ganadores:")
            
            for partido in partidos:
                equipos = partido.split(" @ ")
                eleccion = st.radio(partido, equipos, horizontal=True)
                predicciones_usuario[partido] = eleccion
                
            enviado = st.form_submit_button("Guardar Quiniela")
            
            if enviado:
                if usuario == "":
                    st.error("¡No olvides poner tu nombre!")
                else:
                    for partido, prediccion in predicciones_usuario.items():
                        fila_a_insertar = [usuario, semana_elegida, partido, prediccion]
                        sheet.append_row(fila_a_insertar)
                    st.success(f"¡Predicciones guardadas, {usuario}! Revisa la tabla de posiciones cuando terminen los juegos.")

with tab2:
    st.subheader(f"Posiciones Semana {semana_elegida}")
    
    registros = sheet.get_all_records()
    if registros:
        df_predicciones = pd.DataFrame(registros)
        df_semana = df_predicciones[df_predicciones['Semana'] == semana_elegida]
        
        if not df_semana.empty:
            puntos_usuarios = {}
            
            # Inicializar a todos los usuarios que participaron en esta semana con 0 puntos
            for usr in df_semana['Usuario'].unique():
                puntos_usuarios[usr] = 0
            
            # Calcular puntos comparando con resultados reales
            for index, row in df_semana.iterrows():
                usr = row['Usuario']
                partido = row['Partido']
                pred = row['Prediccion']
                
                if partido in resultados_reales:
                    if pred == resultados_reales[partido]:
                        puntos_usuarios[usr] += 1
                        
            df_posiciones = pd.DataFrame(list(puntos_usuarios.items()), columns=['Usuario', 'Puntos'])
            df_posiciones = df_posiciones.sort_values(by='Puntos', ascending=False).reset_index(drop=True)
            
            df_posiciones.index = df_posiciones.index + 1 
            st.dataframe(df_posiciones, use_container_width=True)
            
            if len(resultados_reales) == 0:
                st.warning("Aún no hay resultados oficiales procesados para esta semana.")
        else:
            st.info("Aún no hay predicciones guardadas para esta semana.")
    else:
        st.info("No hay registros en la base de datos.")
