import streamlit as st
import pandas as pd
from datetime import datetime
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
    
    doc = cliente_sheets.open('Quiniela_NFL_2026')
    sheet_picks = doc.worksheet('Picks')
    sheet_resultados = doc.worksheet('Resultados')
    conexion_exitosa = True
except Exception as e:
    conexion_exitosa = False
    error_detalles = e

# --- LÓGICA DE FECHAS LÍMITE EXACTAS POR SEMANA ---
def obtener_limite_semana(semana_actual):
    # Fechas y horas exactas de cierre (17:00 hrs = 5:00 PM para los jueves)
    limites = {
        1: datetime(2026, 9, 27, 21, 0, 0),
        2: datetime(2026, 9, 27, 21, 0, 0),
        3: datetime(2026, 9, 27, 21, 0, 0),
        4: datetime(2026, 10, 1, 17, 0, 0),
        5: datetime(2026, 10, 8, 17, 0, 0),
        6: datetime(2026, 10, 15, 17, 0, 0),
        7: datetime(2026, 10, 22, 17, 0, 0),
        8: datetime(2026, 10, 29, 17, 0, 0),
        9: datetime(2026, 11, 5, 17, 0, 0),
        10: datetime(2026, 11, 12, 17, 0, 0),
        11: datetime(2026, 11, 19, 17, 0, 0),
        12: datetime(2026, 11, 26, 17, 0, 0),
        13: datetime(2026, 12, 3, 17, 0, 0),
        14: datetime(2026, 12, 10, 17, 0, 0),
        15: datetime(2026, 12, 17, 17, 0, 0),
        16: datetime(2026, 12, 24, 17, 0, 0),
        17: datetime(2026, 12, 31, 17, 0, 0),
        18: datetime(2027, 1, 7, 17, 0, 0)
    }
    return tz.localize(limites.get(semana_actual, limites[18]))

def validar_tiempo_limite(semana_actual):
    limite = obtener_limite_semana(semana_actual)
    return ahora <= limite

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

# --- CALENDARIO OFICIAL NFL 2026-2027 (Completo 18 Semanas) ---
partidos_por_semana = {
    1: ['Patriots vs Seahawks', 'Rams vs 49ers', 'Buccaneers vs Bengals', 'Saints vs Lions', 'Jets vs Titans', 'Ravens vs Colts', 'Falcons vs Steelers', 'Bears vs Panthers', 'Browns vs Jaguars', 'Bills vs Texans', 'Dolphins vs Raiders', 'Packers vs Vikings', 'Commanders vs Eagles', 'Cardinals vs Chargers', 'Cowboys vs Giants', 'Broncos vs Chiefs'],
    2: ['Lions vs Bills', 'Panthers vs Falcons', 'Vikings vs Bears', 'Eagles vs Titans', 'Steelers vs Patriots', 'Packers vs Jets', 'Browns vs Buccaneers', 'Saints vs Ravens', 'Bengals vs Texans', 'Jaguars vs Broncos', 'Raiders vs Chargers', 'Commanders vs Cowboys', 'Seahawks vs Cardinals', 'Dolphins vs 49ers', 'Colts vs Chiefs', 'Giants vs Rams'],
    3: ['Falcons vs Packers', 'Chargers vs Bills', 'Panthers vs Browns', 'Jets vs Lions', 'Texans vs Colts', 'Chiefs vs Dolphins', 'Titans vs Giants', 'Bengals vs Steelers', 'Seahawks vs Commanders', 'Patriots vs Jaguars', 'Cardinals vs 49ers', 'Vikings vs Buccaneers', 'Ravens vs Cowboys', 'Raiders vs Saints', 'Rams vs Broncos', 'Eagles vs Bears'],
    4: ['Steelers vs Browns', 'Colts vs Commanders', 'Patriots vs Bills', 'Jets vs Bears', 'Jaguars vs Bengals', 'Cardinals vs Giants', 'Rams vs Eagles', 'Packers vs Buccaneers', 'Titans vs Ravens', 'Cowboys vs Texans', 'Dolphins vs Vikings', 'Chiefs vs Raiders', 'Broncos vs 49ers', 'Chargers vs Seahawks', 'Lions vs Panthers', 'Falcons vs Saints'],
    5: ['Buccaneers vs Cowboys', 'Eagles vs Jaguars', 'Texans vs Titans', 'Bengals vs Dolphins', 'Raiders vs Patriots', 'Vikings vs Saints', 'Browns vs Giants', 'Colts vs Steelers', 'Jets vs Commanders', 'Broncos vs Rams', 'Bears vs Packers', 'Lions vs Cardinals', '49ers vs Seahawks', 'Ravens vs Falcons', 'Bills vs Chargers'],
    6: ['Seahawks vs Broncos', 'Jaguars vs Texans', 'Bears vs Falcons', 'Ravens vs Browns', 'Titans vs Colts', 'Jets vs Patriots', 'Saints vs Giants', 'Panthers vs Eagles', 'Steelers vs Buccaneers', 'Cardinals vs Chargers', 'Rams vs Chiefs', 'Bills vs Raiders', 'Cowboys vs Packers', 'Commanders vs 49ers'],
    7: ['Patriots vs Bears', 'Steelers vs Saints', '49ers vs Falcons', 'Browns vs Titans', 'Colts vs Vikings', 'Dolphins vs Giants', 'Buccaneers vs Panthers', 'Bengals vs Ravens', 'Jets vs Texans', 'Broncos vs Cardinals', 'Packers vs Lions', 'Chargers vs Raiders', 'Chiefs vs Seahawks', 'Cowboys vs Eagles'],
    8: ['Panthers vs Packers', 'Ravens vs Bills', 'Titans vs Bengals', 'Cardinals vs Cowboys', 'Vikings vs Lions', 'Raiders vs Giants', 'Browns vs Steelers', 'Falcons vs Buccaneers', 'Colts vs Jaguars', 'Rams vs Chargers', 'Chiefs vs Broncos', 'Patriots vs Dolphins', 'Eagles vs Commanders', 'Bears vs Seahawks'],
    9: ['Jaguars vs Ravens', 'Bengals vs Falcons', 'Cowboys vs Colts', 'Jets vs Chiefs', 'Lions vs Dolphins', 'Browns vs Saints', 'Giants vs Eagles', 'Chargers vs Commanders', 'Broncos vs Panthers', 'Texans vs Rams', 'Raiders vs 49ers', 'Packers vs Patriots', 'Cardinals vs Seahawks', 'Buccaneers vs Bears', 'Bills vs Vikings'],
    10: ['Commanders vs Giants', 'Patriots vs Lions', 'Chiefs vs Falcons', 'Texans vs Browns', 'Vikings vs Packers', 'Jaguars vs Titans', 'Dolphins vs Colts', 'Panthers vs Saints', 'Bills vs Jets', 'Seahawks vs Raiders', 'Cardinals vs Chargers', '49ers vs Cowboys', 'Steelers vs Bengals', 'Rams vs Ravens'],
    11: ['Colts vs Texans', 'Dolphins vs Bills', 'Saints vs Bears', 'Titans vs Cowboys', 'Buccaneers vs Lions', 'Cardinals vs Chiefs', 'Jaguars vs Giants', 'Ravens vs Panthers', 'Jets vs Rams', 'Raiders vs Broncos', 'Steelers vs Eagles', 'Vikings vs 49ers', 'Bengals vs Commanders'],
    12: ['Bears vs Lions', 'Eagles vs Cowboys', 'Chiefs vs Bills', 'Broncos vs Steelers', 'Saints vs Bengals', 'Raiders vs Browns', 'Giants vs Colts', 'Jets vs Dolphins', 'Falcons vs Vikings', 'Ravens vs Texans', 'Titans vs Jaguars', 'Commanders vs Cardinals', 'Seahawks vs 49ers', 'Patriots vs Chargers', 'Panthers vs Buccaneers'],
    13: ['Chiefs vs Chargers', 'Lions vs Falcons', 'Jaguars vs Bears', 'Bengals vs Browns', 'Commanders vs Titans', 'Packers vs Saints', '49ers vs Giants', 'Rams vs Buccaneers', 'Dolphins vs Broncos', 'Eagles vs Cardinals', 'Panthers vs Vikings', 'Bills vs Patriots', 'Texans vs Steelers', 'Cowboys vs Seahawks'],
    14: ['Vikings vs Patriots', 'Falcons vs Browns', 'Titans vs Lions', 'Bears vs Dolphins', 'Broncos vs Jets', 'Colts vs Eagles', 'Texans vs Commanders', 'Saints vs Panthers', 'Buccaneers vs Ravens', 'Chargers vs Raiders', 'Chiefs vs Bengals', 'Rams vs 49ers', 'Giants vs Seahawks', 'Bills vs Packers', 'Steelers vs Jaguars'],
    15: ['49ers vs Rams', 'Seahawks vs Eagles', 'Bears vs Bills', 'Dolphins vs Packers', 'Colts vs Titans', 'Browns vs Jets', 'Ravens vs Steelers', 'Saints vs Buccaneers', 'Falcons vs Commanders', 'Bengals vs Panthers', 'Jaguars vs Texans', 'Giants vs Cardinals', 'Broncos vs Raiders', 'Cowboys vs Chargers', 'Lions vs Vikings', 'Patriots vs Chiefs'],
    16: ['Texans vs Eagles', 'Packers vs Bears', 'Bills vs Broncos', 'Chargers vs Seahawks', 'Rams vs Dolphins', 'Cardinals vs Saints', 'Patriots vs Jets', 'Browns vs Ravens', 'Titans vs Raiders', '49ers vs Chiefs', 'Jaguars vs Cowboys', 'Giants vs Lions', 'Buccaneers vs Falcons', 'Bengals vs Colts', 'Commanders vs Vikings', 'Panthers vs Steelers'],
    17: ['Ravens vs Bengals', 'Saints vs Falcons', 'Colts vs Browns', 'Giants vs Cowboys', 'Steelers vs Titans', 'Bills vs Dolphins', 'Vikings vs Jets', 'Seahawks vs Panthers', 'Raiders vs Cardinals', 'Lions vs Bears', 'Eagles vs 49ers', 'Texans vs Packers', 'Broncos vs Patriots', 'Chiefs vs Chargers', 'Rams vs Buccaneers', 'Commanders vs Jaguars'],
    18: ['Jets vs Bills', 'Browns vs Bengals', 'Chargers vs Broncos', 'Lions vs Packers', 'Jaguars vs Colts', 'Raiders vs Chiefs', 'Seahawks vs Rams', 'Bears vs Vikings', 'Dolphins vs Patriots', 'Buccaneers vs Saints', 'Eagles vs Giants', '49ers vs Cardinals', 'Cowboys vs Commanders', 'Falcons vs Panthers', 'Steelers vs Ravens', 'Titans vs Texans']
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
        limite_str = obtener_limite_semana(semana).strftime('%d/%m/%Y a las %H:%M')
        
        if not tiempo_permitido:
            st.warning(f'El tiempo límite para enviar picks para la semana {semana} expiró el {limite_str}.')
        else:
            st.info(f'Tienes hasta el {limite_str} para enviar tus picks de esta semana.')
                
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
                    for partido, prediccion in picks_usuario.items():
                        sheet_picks.append_row([participante, semana, partido, prediccion])
                    
                    st.session_state.mostrar_recibo_exito = True
                    st.session_state.datos_recibo = {
                        'participante': participante,
                        'semana': semana,
                        'picks': picks_usuario.copy(),
                    }
                    st.rerun()

        # Mostrar recibo
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

    # --- PESTAÑA 2: STANDINGS ---
    with tab_standings:
        st.subheader('🏆 Tabla General de Posiciones (Podio)')
        st.info('1 Acierto = 1 Punto. Los standings para las semanas 1, 2 y 3 se actualizarán cuando se suban los resultados finales.')
        
        try:
            data_picks = sheet_picks.get_all_records()
            data_resultados = sheet_resultados.get_all_records()
            
            if data_picks:
                df_picks = pd.DataFrame(data_picks)
                
                if data_resultados:
                    df_res = pd.DataFrame(data_resultados)
                    df_cruce = pd.merge(df_picks, df_res, on=['Semana', 'Partido'], how='left')
                    
                    df_cruce['Puntos'] = (df_cruce['Prediccion'] == df_cruce['Ganador']).astype(int)
                    
                    df_standings = df_cruce.groupby('Participante')['Puntos'].sum().reset_index()
                    df_standings = df_standings.sort_values(by='Puntos', ascending=False).reset_index(drop=True)
                    
                    df_standings.index = df_standings.index + 1
                    df_standings.index.name = 'Posición'
                    
                    st.dataframe(df_standings.style.highlight_max(subset=['Puntos'], color='lightgreen'), use_container_width=True)
                else:
                    st.warning('Los administradores aún no han subido los resultados oficiales. Aún no hay puntos calculados.')
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
            try:
                # Lee el CSV detectando separadores en automático
                df_nuevos_res = pd.read_csv(archivo_resultados, sep=None, engine='python')
                df_nuevos_res.columns = df_nuevos_res.columns.str.strip()
                
                # --- SOLUCIÓN: Convertir celdas vacías (NaN) en texto en blanco ---
                df_nuevos_res = df_nuevos_res.fillna("")
                
                # Convertimos la información a una lista masiva
                valores = df_nuevos_res[['Semana', 'Partido', 'Ganador']].values.tolist()
                
                # Subimos TODOS los resultados en 1 sola petición a Google Sheets
                sheet_resultados.append_rows(valores)
                
                st.success('¡Resultados subidos y podio actualizado con éxito!')
                
            except KeyError as e:
                st.error(f'Error de columnas: No se encontró exactamente la columna {e}. Tus columnas actuales son: {list(df_nuevos_res.columns)}')
            except Exception as e:
                st.error(f'Ocurrió un error al procesar el archivo: {e}')
elif admin_pass != '':
    st.sidebar.error('Contraseña incorrecta')
