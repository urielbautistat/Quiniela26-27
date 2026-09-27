import streamlit as st
import pandas as pd
from datetime import datetime, time
import pytz
import json
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title='Quiniela NFL 2026-2027', page_icon='🏈', layout='centered')

# --- ZONA HORARIA Y FECHA ACTUAL ---
tz = pytz.timezone('America/Mexico_City')
ahora = datetime.now(tz)

# --- CONEXIÓN CON GOOGLE SHEETS ---
try:
    secreto_gcp = st.secrets['gcp_credentials']
    if isinstance(secreto_gcp, str):
        creds_dict = json.loads(secreto_gcp)
    else:
        creds_dict = dict(secreto_gcp)
        
    if '\\n' in creds_dict['private_key']:
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    cliente_sheets = gspread.authorize(creds)
    
    # Abrimos el documento y las dos hojas de trabajo
    doc = cliente_sheets.open('Quiniela_NFL_2026')
    sheet_picks = doc.worksheet('Picks')
    sheet_resultados = doc.worksheet('Resultados')
    conexion_exitosa = True
except Exception as e:
    conexion_exitosa = False
    error_detalles = e

# --- LÓGICA DE TIEMPO LÍMITE ---
def validar_tiempo_limite(semana_actual):
    # Prórroga para semanas 1, 2 y 3: Hoy domingo 27 de septiembre a las 9:00 PM (21:00)
    if semana_actual <= 3:
        limite_semanas_1_3 = tz.localize(datetime(2026, 9, 27, 21, 0, 0))
        if ahora > limite_semanas_1_3:
            return False
        return True
        
    # Semanas 4 a 18: Límite el jueves de esa semana a las 4:00 PM (16:00)
    dia_semana = ahora.weekday() # 0=Lunes, 3=Jueves, 4=Viernes, etc.
    hora_actual = ahora.time()
    
    # Si es viernes, sábado o domingo (días 4, 5, 6), ya cerró para la semana en curso
    if dia_semana > 3:
        return False
    # Si es jueves (día 3) y ya pasaron las 4:00 PM, cierra
    if dia_semana == 3 and hora_actual >= time(16, 0):
        return False
        
    return True

# --- VERIFICAR PARTICIPACIÓN ÚNICA ---
def usuario_ya_participo(participante, semana):
    try:
        registros = sheet_picks.get_all_records()
        for row in registros:
            if (str(row.get('Participante', '')).strip().lower() == participante.strip().lower() 
                and int(row.get('Semana', 0)) == semana):
                return True
    except Exception:
        pass
    return False

# --- CALENDARIO NFL 2026-2027 (18 Semanas) ---
# He estructurado las 18 semanas. Ajusta los enfrentamientos exactos según el bye-week de la NFL.
partidos_por_semana = {
    1: ['Chiefs vs Ravens', 'Eagles vs Packers', 'Falcons vs Steelers', 'Bills vs Cardinals', 'Bears vs Titans', 'Bengals vs Patriots', 'Colts vs Texans', 'Dolphins vs Jaguars', 'Saints vs Panthers', 'Giants vs Vikings', 'Chargers vs Raiders', 'Seahawks vs Broncos', 'Browns vs Cowboys', 'Buccaneers vs Commanders', 'Lions vs Rams', '49ers vs Jets'],
    2: ['Dolphins vs Bills', 'Ravens vs Raiders', 'Panthers vs Chargers', 'Cowboys vs Saints', 'Lions vs Buccaneers', 'Packers vs Colts', 'Jaguars vs Browns', 'Vikings vs 49ers', 'Patriots vs Seahawks', 'Titans vs Jets', 'Commanders vs Giants', 'Cardinals vs Rams', 'Broncos vs Steelers', 'Chiefs vs Bengals', 'Texans vs Bears', 'Eagles vs Falcons'],
    3: ['Jets vs Patriots', 'Browns vs Giants', 'Titans vs Packers', 'Colts vs Bears', 'Vikings vs Texans', 'Saints vs Eagles', 'Steelers vs Chargers', 'Buccaneers vs Broncos', 'Raiders vs Panthers', 'Seahawks vs Dolphins', 'Cowboys vs Ravens', 'Rams vs 49ers', 'Cardinals vs Lions', 'Falcons vs Chiefs', 'Bills vs Jaguars', 'Bengals vs Commanders'],
    4: ['Giants vs Cowboys', 'Falcons vs Saints', 'Bears vs Rams', 'Packers vs Vikings', 'Colts vs Steelers', 'Jets vs Broncos', 'Buccaneers vs Eagles', 'Bengals vs Panthers', 'Texans vs Jaguars', 'Packers vs Vikings', 'Raiders vs Browns', 'Cardinals vs Commanders', '49ers vs Patriots', 'Chargers vs Chiefs', 'Ravens vs Bills', 'Dolphins vs Titans', 'Lions vs Seahawks'],
    5: ['Falcons vs Buccaneers', 'Bears vs Panthers', 'Bengals vs Ravens', 'Texans vs Bills', 'Jaguars vs Colts', 'Patriots vs Dolphins', 'Commanders vs Browns', 'Broncos vs Raiders', '49ers vs Cardinals', 'Rams vs Packers', 'Seahawks vs Giants', 'Steelers vs Cowboys', 'Chiefs vs Saints'], # Semanas con equipos descansando
    6: ['Seahawks vs 49ers', 'Bears vs Jaguars', 'Ravens vs Commanders', 'Packers vs Cardinals', 'Patriots vs Texans', 'Saints vs Buccaneers', 'Eagles vs Browns', 'Titans vs Colts', 'Broncos vs Chargers', 'Raiders vs Steelers', 'Panthers vs Falcons', 'Cowboys vs Lions', 'Giants vs Bengals', 'Jets vs Bills'],
    7: ['Saints vs Broncos', 'Falcons vs Seahawks', 'Bills vs Titans', 'Browns vs Bengals', 'Packers vs Texans', 'Colts vs Dolphins', 'Vikings vs Lions', 'Giants vs Eagles', 'Rams vs Raiders', 'Commanders vs Panthers', '49ers vs Chiefs', 'Steelers vs Jets', 'Buccaneers vs Ravens', 'Cardinals vs Chargers'],
    8: ['Rams vs Vikings', 'Browns vs Ravens', 'Lions vs Titans', 'Dolphins vs Cardinals', 'Patriots vs Jets', 'Buccaneers vs Falcons', 'Jaguars vs Packers', 'Texans vs Colts', 'Bengals vs Eagles', 'Chargers vs Saints', 'Seahawks vs Bills', 'Commanders vs Bears', 'Broncos vs Panthers', 'Raiders vs Chiefs', '49ers vs Cowboys', 'Steelers vs Giants'],
    9: ['Jets vs Texans', 'Falcons vs Cowboys', 'Bills vs Dolphins', 'Panthers vs Saints', 'Bengals vs Raiders', 'Browns vs Chargers', 'Titans vs Patriots', 'Giants vs Commanders', 'Eagles vs Jaguars', 'Cardinals vs Bears', 'Packers vs Lions', 'Seahawks vs Rams', 'Vikings vs Colts', 'Chiefs vs Buccaneers'],
    10: ['Ravens vs Bengals', 'Panthers vs Giants', 'Bears vs Patriots', 'Colts vs Bills', 'Chiefs vs Broncos', 'Saints vs Falcons', 'Buccaneers vs 49ers', 'Commanders vs Steelers', 'Jaguars vs Vikings', 'Chargers vs Titans', 'Cowboys vs Eagles', 'Cardinals vs Jets', 'Texans vs Lions', 'Rams vs Dolphins'],
    11: ['Eagles vs Commanders', 'Bears vs Packers', 'Lions vs Jaguars', 'Dolphins vs Raiders', 'Patriots vs Rams', 'Saints vs Browns', 'Jets vs Colts', 'Steelers vs Ravens', 'Titans vs Vikings', 'Broncos vs Falcons', '49ers vs Seahawks', 'Bills vs Chiefs', 'Chargers vs Bengals', 'Cowboys vs Texans'],
    12: ['Browns vs Steelers', 'Panthers vs Chiefs', 'Bears vs Vikings', 'Texans vs Titans', 'Colts vs Lions', 'Dolphins vs Patriots', 'Giants vs Buccaneers', 'Commanders vs Cowboys', 'Raiders vs Broncos', 'Packers vs 49ers', 'Seahawks vs Cardinals', 'Eagles vs Rams', 'Chargers vs Ravens'],
    13: ['Lions vs Bears', 'Cowboys vs Giants', 'Packers vs Dolphins', 'Falcons vs Chargers', 'Bengals vs Steelers', 'Patriots vs Colts', 'Vikings vs Cardinals', 'Commanders vs Titans', 'Jets vs Seahawks', 'Buccaneers vs Panthers', 'Saints vs Rams', 'Eagles vs Ravens', 'Chiefs vs Raiders', 'Bills vs 49ers', 'Broncos vs Browns'],
    14: ['Lions vs Packers', 'Bears vs 49ers', 'Bengals vs Cowboys', 'Dolphins vs Jets', 'Vikings vs Falcons', 'Giants vs Saints', 'Panthers vs Eagles', 'Steelers vs Browns', 'Titans vs Jaguars', 'Cardinals vs Seahawks', 'Buccaneers vs Raiders', 'Rams vs Bills', '49ers vs Bears', 'Chiefs vs Chargers'],
    15: ['Seahawks vs Packers', 'Jaguars vs Jets', 'Ravens vs Eagles', 'Panthers vs Cowboys', 'Browns vs Chiefs', 'Lions vs Bills', 'Texans vs Dolphins', 'Saints vs Commanders', 'Buccaneers vs Chargers', 'Titans vs Bengals', 'Cardinals vs Patriots', 'Broncos vs Colts', 'Raiders vs Falcons', '49ers vs Rams', 'Vikings vs Bears'],
    16: ['Bengals vs Browns', 'Bears vs Lions', 'Ravens vs Steelers', 'Bills vs Patriots', 'Panthers vs Cardinals', 'Cowboys vs Buccaneers', 'Packers vs Saints', 'Texans vs Ravens', 'Colts vs Titans', 'Jaguars vs Raiders', 'Chiefs vs Texans', 'Dolphins vs 49ers', 'Eagles vs Commanders', 'Rams vs Seahawks', 'Chargers vs Broncos'],
    17: ['Bears vs Seahawks', 'Browns vs Dolphins', 'Cowboys vs Eagles', 'Packers vs Vikings', 'Texans vs Chiefs', 'Colts vs Jaguars', 'Patriots vs Bills', 'Saints vs Raiders', 'Giants vs Colts', 'Steelers vs Bengals', 'Titans vs Panthers', 'Commanders vs Falcons', 'Cardinals vs Rams', 'Broncos vs Jets', 'Chargers vs Buccaneers', '49ers vs Lions'],
    18: ['Falcons vs Panthers', 'Ravens vs Browns', 'Bills vs Jets', 'Bears vs Packers', 'Bengals vs Steelers', 'Cowboys vs Commanders', 'Broncos vs Chiefs', 'Lions vs Vikings', 'Texans vs Titans', 'Colts vs Jaguars', 'Dolphins vs Patriots', 'Saints vs Buccaneers', 'Giants vs Eagles', 'Eagles vs Giants', 'Cardinals vs 49ers', 'Rams vs Seahawks']
}

# --- INTERFAZ PRINCIPAL ---
st.title('🏈 Quiniela NFL 2026-2027')

if not conexion_exitosa:
    st.error(f'Error en la conexión con Google Sheets: {error_detalles}')
else:
    tab_quiniela, tab_standings = st.tabs(['📝 Hacer Quiniela', '🏆 Standings / Posiciones'])

    # --- PESTAÑA 1: HACER QUINIELA ---
    with tab_quiniela:
        semana = st.selectbox('Selecciona la Semana', list(range(1, 19)), index=0)
        participante = st.text_input('Tu Nombre / Participante').strip()
        
        tiempo_permitido = validar_tiempo_limite(semana)
        
        if not tiempo_permitido:
            if semana <= 3:
                st.warning('El tiempo límite para enviar picks para esta semana expiró (Domingo 27 de Sep a las 9:00 PM).')
            else:
                st.warning('El tiempo límite para enviar picks para esta semana expiró (Jueves a las 4:00 PM).')
                
        ya_envio = False
        if participante:
            ya_envio = usuario_ya_participo(participante, semana)
            if ya_envio:
                st.error(f'¡El participante **{participante}** ya tiene registrada su quiniela para la **Semana {semana}**! Solo se permite un envío por semana.')

        partidos_semana = partidos_por_semana.get(semana, [])
        picks_usuario = {}
        
        st.markdown('### Selecciona a tus ganadores:')
        formulario_bloqueado = not tiempo_permitido or ya_envio or not participante

        if 'mostrar_recibo_exito' not in st.session_state:
            st.session_state.mostrar_recibo_exito = False
            st.session_state.datos_recibo = None

        with st.form('form_quiniela'):
            for partido in partidos_semana:
                equipos = partido.split(' vs ')
                picks_usuario[partido] = st.radio(partido, equipos, horizontal=True, disabled=formulario_bloqueado)
                
            enviado = st.form_submit_button('Guardar Picks', disabled=formulario_bloqueado)
            
            if enviado:
                if participante == "":
                    st.error('Por favor, ingresa tu nombre.')
                elif usuario_ya_participo(participante, semana):
                    st.error('Ya habías registrado tus picks para esta semana previamente.')
                else:
                    # Guardar en Google Sheets (Hoja de Picks)
                    for partido, prediccion in picks_usuario.items():
                        sheet_picks.append_row([participante, semana, partido, prediccion])
                    
                    st.session_state.mostrar_recibo_exito = True
                    st.session_state.datos_recibo = {
                        'participante': participante,
                        'semana': semana,
                        'picks': picks_usuario.copy(),
                    }
                    st.rerun()

        # Mostrar recibo fuera del formulario si fue guardado con éxito
        if st.session_state.mostrar_recibo_exito:
            d = st.session_state.datos_recibo
            st.markdown('---')
            st.subheader('✅ Comprobante de Picks Registrados')
            st.success(f'¡Tus pronósticos para la **Semana {d["semana"]}** se guardaron con éxito!')
            
            recibo_texto = f'--- RECIBO DE QUINIELA NFL ---\n'
            recibo_texto += f'Participante: {d["participante"]}\n'
            recibo_texto += f'Semana: {d["semana"]}\n'
            recibo_texto += f'Fecha de registro: {ahora.strftime("%Y-%m-%d %H:%M:%S")}\n\n'
            recibo_texto += 'Tus selecciones:\n'
            for partido, equipo in d['picks'].items():
                recibo_texto += f' - {partido} -> Ganador: {equipo}\n'
                st.write(f'**{partido}** ➔ **{equipo}**')
                
            st.download_button(
                label='📄 Descargar comprobante en texto',
                data=recibo_texto,
                file_name=f'recibo_{d["participante"].replace(" ", "_")}_semana_{d["semana"]}.txt',
                mime='text/plain',
            )

    # --- PESTAÑA 2: STANDINGS (PODIO Y PUNTOS) ---
    with tab_standings:
        st.subheader('🏆 Tabla General de Posiciones (Podio)')
        st.info('1 Acierto = 1 Punto. Los standings para las semanas 1, 2 y 3 se actualizarán el lunes después del último partido.')
        
        try:
            data_picks = sheet_picks.get_all_records()
            data_resultados = sheet_resultados.get_all_records()
            
            if data_picks:
                df_picks = pd.DataFrame(data_picks)
                
                if data_resultados:
                    # Hacemos merge (cruce) entre los picks y los resultados oficiales para validar si acertaron
                    df_res = pd.DataFrame(data_resultados)
                    df_cruce = pd.merge(df_picks, df_res, on=['Semana', 'Partido'], how='left')
                    
                    # Se suma 1 punto si la predicción es exactamente igual al ganador
                    df_cruce['Puntos'] = (df_cruce['Prediccion'] == df_cruce['Ganador']).astype(int)
                    
                    # Agrupar por participante y sumar sus puntos totales
                    df_standings = df_cruce.groupby('Participante')['Puntos'].sum().reset_index()
                    df_standings = df_standings.sort_values(by='Puntos', ascending=False).reset_index(drop=True)
                    
                    # Ajustar el índice para que sea 1, 2, 3... (El Podio)
                    df_standings.index = df_standings.index + 1
                    df_standings.index.name = 'Posición'
                    
                    st.dataframe(df_standings.style.highlight_max(subset=['Puntos'], color='lightgreen'), use_container_width=True)
                else:
                    st.warning('Los administradores aún no han subido los resultados oficiales. Aún no hay puntos calculados.')
                    # Muestra solo cuántos picks ha metido cada quien
                    st.dataframe(df_picks['Participante'].value_counts().reset_index().rename(columns={'count': 'Partidos Pronosticados'}))
            else:
                st.warning('Aún no hay registros guardados en la quiniela.')
        except Exception as e:
            st.write('Cargando tabla de posiciones... (Asegúrate de que las hojas "Picks" y "Resultados" existan en tu Google Sheets).')

# --- PANEL DE ADMINISTRADOR ---
st.sidebar.markdown('---')
st.sidebar.subheader('⚙️ Panel de Administrador')
admin_pass = st.sidebar.text_input('Contraseña Admin', type='password')

password_correcta = st.secrets.get('ADMIN_PASSWORD', 'admin123')

if admin_pass == password_correcta:
    st.sidebar.success('Acceso de Administrador Concedido')
    with st.sidebar.expander('📊 Cargar Resultados Finales'):
        st.write('Asegúrate de subir un CSV con columnas: `Semana`, `Partido`, `Ganador`')
        archivo_resultados = st.file_uploader('Subir resultados oficiales (CSV)', type=['csv'], key='res_admin')
        
        if archivo_resultados and st.button('Actualizar Resultados Oficiales'):
            df_nuevos_res = pd.read_csv(archivo_resultados)
            # Guardamos los resultados iterando en la hoja "Resultados"
            for index, row in df_nuevos_res.iterrows():
                sheet_resultados.append_row([row['Semana'], row['Partido'], row['Ganador']])
            st.success('¡Resultados subidos y podio actualizado con éxito!')
elif admin_pass != '':
    st.sidebar.error('Contraseña incorrecta')
