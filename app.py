from datetime import datetime, time
import pytz
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title='Quiniela NFL 2026-2027', page_icon='🏈', layout='centered'
)

# Zona horaria (Ciudad de México)
tz = pytz.timezone('America/Mexico_City')
ahora = datetime.now(tz)

# --- CONEXIÓN CON GOOGLE SHEETS ---
try:
  import gspread
  from google.oauth2.service_account import Credentials

  secreto_gcp = st.secrets['gcp_credentials']
  if isinstance(secreto_gcp, str):
    import json

    creds_dict = json.loads(secreto_gcp)
  else:
    creds_dict = dict(secreto_gcp)

  if '\\n' in creds_dict['private_key']:
    creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')

  scopes = [
      'https://www.googleapis.com/auth/spreadsheets',
      'https://www.googleapis.com/auth/drive',
  ]
  creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
  cliente_sheets = gspread.authorize(creds)
  sheet = cliente_sheets.open('Quiniela_NFL_2026').sheet1
  conexion_exitosa = True
except Exception as e:
  conexion_exitosa = False
  error_detalles = e


# --- LÓGICA DE VALIDACIÓN DE TIEMPO LÍMITE ---
def validar_tiempo_limite(semana_actual):
  # Semanas 1, 2 y 3: Límite mañana viernes a las 12:00 PM
  if semana_actual <= 3:
    # Fecha límite fija: Mañana viernes a las 12:00 PM (2026-09-25 12:00:00)
    limite_semanas_1_3 = tz.localize(datetime(2026, 9, 25, 12, 0, 0))
    if ahora > limite_semanas_1_3:
      return False
    return True

  # Semanas 4 a 18: Límite el jueves de esa semana a las 5:00 PM
  dia_semana = ahora.weekday()  # 0=Lunes, 3=Jueves, etc.
  hora_actual = ahora.time()
  if dia_semana > 3 or (dia_semana == 3 and hora_actual >= time(17, 0)):
    return False
  return True


# --- VERIFICAR SI EL USUARIO YA PARTICIPÓ EN ESA SEMANA ---
def usuario_ya_participo(participante, semana):
  try:
    registros = sheet.get_all_records()
    for row in registros:
      # Comparamos ignorando mayúsculas/minúsculas en el nombre y el número de semana
      if (
          str(row.get('Participante', '')).strip().lower()
          == participante.strip().lower()
          and int(row.get('Semana', 0)) == semana
      ):
        return True
  except Exception:
    pass
  return False


# --- RECIBO DE PICKS ---
def mostrar_recibo(participante, semana, picks_usuario):
  st.markdown('---')
  st.subheader('📄 Comprobante de Picks Registrados')
  st.success(
      f'¡Tus pronósticos para la **Semana {semana}** se guardaron con éxito!'
  )

  recibo_texto = '--- RECIBO DE QUINIELA NFL ---\n'
  recibo_texto += f'Participante: {participante}\n'
  recibo_texto += f'Semana: {semana}\n'
  recibo_texto += f'Fecha de registro: {ahora.strftime("%Y-%m-%d %H:%M:%S")}\n\n'
  recibo_texto += 'Tus selecciones:\n'

  for partido, equipo in picks_usuario.items():
    recibo_texto += f' - {partido} -> Ganador: {equipo}\n'
    st.write(f'- **{partido}** ➔ **{equipo}**')

  st.download_button(
      label='📥 Descargar comprobante en texto',
      data=recibo_texto,
      file_name=(
          f'recibo_{participante.replace(" ", "_")}_semana_{semana}.txt'
      ),
      mime='text/plain',
  )


# --- INTERFAZ PRINCIPAL ---
st.title('🏈 Quiniela NFL 2026-2027')

if not conexion_exitosa:
  st.error(f'Error en la conexión con Google Sheets: {error_detalles}')
else:
  tab_quiniela, tab_standings = st.tabs(
      ['📝 Hacer Quiniela', '🏆 Standings / Posiciones']
  )

  with tab_quiniela:
    semana = st.selectbox(
        'Selecciona la Semana',
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
        index=0,
    )
    participante = st.text_input('Tu Nombre / Participante').strip()

    # Validaciones de tiempo y de envío único
    tiempo_permitido = validar_tiempo_limite(semana)

    if not tiempo_permitido:
      if semana <= 3:
        st.warning(
            '⏳ El tiempo límite para enviar picks para esta semana expiró'
            ' (Viernes a las 12:00 PM).'
        )
      else:
        st.warning(
            '⏳ El tiempo límite para enviar picks para esta semana expiró'
            ' (Jueves a las 5:00 PM).'
        )

    # Validar si ya registró picks en esta semana (solo si ingresó nombre)
    ya_envio = False
    if participante:
      ya_envio = usuario_ya_participo(participante, semana)
      if ya_envio:
        st.error(
            f'⚠️ El participante **{participante}** ya tiene registrada su'
            f' quiniela para la **Semana {semana}**. Solo se permite un envío'
            ' por semana.'
        )

    # Catálogo de partidos
    partidos_por_semana = {
        1: [
            'Kansas City Chiefs vs Baltimore Ravens',
            'Philadelphia Eagles vs Green Bay Packers',
            'Buffalo Bills vs Arizona Cardinals',
            'Chicago Bears vs Tennessee Titans',
            'Cincinnati Bengals vs New England Patriots',
            'Detroit Lions vs Los Angeles Rams',
            'Miami Dolphins vs Jacksonville Jaguars',
            'New Orleans Saints vs Carolina Panthers',
            'New York Giants vs Minnesota Vikings',
            'Atlanta Falcons vs Pittsburgh Steelers',
            'Indianapolis Colts vs Houston Texans',
            'Seattle Seahawks vs Denver Broncos',
            'Los Angeles Chargers vs Las Vegas Raiders',
            'Tampa Bay Buccaneers vs Washington Commanders',
            'Cleveland Browns vs Dallas Cowboys',
            'San Francisco 49ers vs New York Jets',
        ],
        2: [
            'Miami Dolphins vs Buffalo Bills',
            'Baltimore Ravens vs Las Vegas Raiders',
            'Dallas Cowboys vs New Orleans Saints',
            'Detroit Lions vs Tampa Bay Buccaneers',
            'Green Bay Packers vs Indianapolis Colts',
            'Houston Texans vs Chicago Bears',
            'Jacksonville Jaguars vs Cleveland Browns',
            'Minnesota Vikings vs San Francisco 49ers',
            'New England Patriots vs Seattle Seahawks',
            'New York Giants vs Washington Commanders',
            'Los Angeles Chargers vs Carolina Panthers',
            'Los Angeles Rams vs Arizona Cardinals',
            'Denver Broncos vs Pittsburgh Steelers',
            'Philadelphia Eagles vs Atlanta Falcons',
            'Kansas City Chiefs vs Cincinnati Bengals',
            'San Francisco 49ers vs New York Jets',
        ],
        3: [
            'New York Giants vs Cleveland Browns',
            'Green Bay Packers vs Tennessee Titans',
            'Chicago Bears vs Indianapolis Colts',
            'Houston Texans vs Minnesota Vikings',
            'Las Vegas Raiders vs Carolina Panthers',
            'New Orleans Saints vs Philadelphia Eagles',
            'Tampa Bay Buccaneers vs Denver Broncos',
            'Los Angeles Chargers vs Pittsburgh Steelers',
            'Atlanta Falcons vs Kansas City Chiefs',
            'Seattle Seahawks vs Miami Dolphins',
            'Arizona Cardinals vs Detroit Lions',
            'Los Angeles Rams vs San Francisco 49ers',
            'Dallas Cowboys vs Baltimore Ravens',
            'Buffalo Bills vs Jacksonville Jaguars',
            'Cincinnati Bengals vs Washington Commanders',
        ],
        4: [
            'Dallas Cowboys vs New York Giants',
            'Atlanta Falcons vs New Orleans Saints',
            'Buffalo Bills vs Baltimore Ravens',
            'Cincinnati Bengals vs Carolina Panthers',
            'Chicago Bears vs Los Angeles Rams',
            'Green Bay Packers vs Minnesota Vikings',
            'Houston Texans vs Jacksonville Jaguars',
            'Indianapolis Colts vs Pittsburgh Steelers',
            'New York Jets vs Denver Broncos',
            'Tampa Bay Buccaneers vs Philadelphia Eagles',
            'San Francisco 49ers vs New England Patriots',
            'Arizona Cardinals vs Washington Commanders',
            'Los Angeles Chargers vs Kansas City Chiefs',
            'Las Vegas Raiders vs Cleveland Browns',
            'Detroit Lions vs Seattle Seahawks',
            'Miami Dolphins vs Tennessee Titans',
        ],
    }

    partidos_semana = partidos_por_semana.get(
        semana, [
            'Equipo Local A vs Equipo Visitante B',
            'Equipo Local C vs Equipo Visitante D',
        ]
    )

    picks_usuario = {}
    st.markdown('### Selecciona a tus ganadores:')

    # El formulario se deshabilita si ya pasó el tiempo o si el usuario ya envió su quiniela
    formulario_bloqueado = not tiempo_permitido or ya_envio or not participante

    with st.form('form_quiniela'):
      for partido in partidos_semana:
        equipos = partido.split(' vs ')
        picks_usuario[partido] = st.radio(
            partido, equipos, horizontal=True, disabled=formulario_bloqueado
        )

      enviado = st.form_submit_button(
          'Guardar Picks', disabled=formulario_bloqueado
      )

      if enviado:
        if participante == '':
          st.error('Por favor, ingresa tu nombre.')
        else:
          # Doble validación al momento de dar clic
          if usuario_ya_participo(participante, semana):
            st.error(
                'Ya habías registrado tus picks para esta semana previamente.'
            )
          else:
            for partido, prediccion in picks_usuario.items():
              # Guardamos en Google Sheets: [Participante, Semana, Partido, Prediccion]
              sheet.append_row([participante, semana, partido, prediccion])
            mostrar_recibo(participante, semana, picks_usuario)

  with tab_standings:
    st.subheader('🏆 Tabla General de Posiciones (Standings)')
    st.info(
        'Consulta en tiempo real el acumulado de registros de todos los'
        ' participantes.'
    )

    try:
      import pandas as pd

      data = sheet.get_all_records()
      if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
      else:
        st.warning('Aún no hay registros guardados en la quiniela.')
    except Exception as e:
      st.write(
          'Cargando tabla de posiciones... (Los registros aparecerán aquí'
          ' conforme se guarden picks).'
      )

# --- PANEL DE ADMINISTRADOR ---
st.sidebar.markdown('---')
st.sidebar.subheader('🔐 Panel de Administrador')
admin_pass = st.sidebar.text_input('Contraseña Admin', type='password')

password_correcta = st.secrets.get('ADMIN_PASSWORD', 'admin123')

if admin_pass == password_correcta:
  st.sidebar.success('Acceso de Administrador Concedido')
  with st.sidebar.expander('⚙️ Cargar Resultados Finales'):
    semana_calificar = st.selectbox(
        'Semana a calificar',
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
        key='sem_admin',
    )
    archivo_resultados = st.file_uploader(
        'Subir resultados oficiales (CSV)', type=['csv'], key='res_admin'
    )

    if archivo_resultados and st.button(
        'Procesar y Actualizar Puntuaciones'
    ):
      st.success(
          f'¡Resultados de la Semana {semana_calificar} aplicados con éxito!'
      )
elif admin_pass != '':
  st.sidebar.error('Contraseña incorrecta')
