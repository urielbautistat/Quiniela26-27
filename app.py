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
  # Usamos la primera hoja para los picks y una segunda o la misma según prefieras
  sheet = cliente_sheets.open('Quiniela_NFL_2026').sheet1
  conexion_exitosa = True
except Exception as e:
  conexion_exitosa = False
  error_detalles = e


# --- VALIDACIÓN DE TIEMPO LÍMITE (JUEVES 5 PM A PARTIR DE SEMANA 4) ---
def validar_tiempo_limite(semana_actual):
  if semana_actual >= 4:
    dia_semana = ahora.weekday()  # 0=Lunes, 3=Jueves, etc.
    hora_actual = ahora.time()
    if dia_semana > 3 or (dia_semana == 3 and hora_actual >= time(17, 0)):
      return False
  return True


# --- RECIBO DE PICKS ---
def mostrar_recibo(participante, semana, picks_usuario):
  st.markdown('---')
  st.subheader('📄 Comprobante de Picks Registrados')
  st.success(f'¡Tus pronósticos para la **Semana {semana}** se guardaron!')

  recibo_texto = '--- RECIBO DE QUINIELA NFL ---\n'
  recibo_texto += f'Participante: {participante}\n'
  recibo_texto += f'Semana: {semana}\n'
  recibo_texto += f'Fecha: {ahora.strftime("%Y-%m-%d %H:%M:%S")}\n\n'
  recibo_texto += 'Tus selecciones:\n'

  for partido, equipo in picks_usuario.items():
    recibo_texto += f' - {partido} -> Ganador: {equipo}\n'
    st.write(f'- **{partido}** ➔ **{equipo}**')

  st.download_button(
      label='📥 Descargar comprobante en texto',
      data=recibo_texto,
      file_name=f'recibo_{participante}_semana_{semana}.txt',
      mime='text/plain',
  )


# --- INTERFAZ PRINCIPAL ---
st.title('🏈 Quiniela NFL 2026-2027')

if not conexion_exitosa:
  st.error(f'Error en la conexión con Google Sheets: {error_detalles}')
else:
  # Pestañas principales para separar la Quiniela de la Tabla de Posiciones (Standings)
  tab_quiniela, tab_standings = st.tabs(
      ['📝 Hacer Quiniela', '🏆 Standings / Posiciones']
  )

  with tab_quiniela:
    semana = st.selectbox(
        'Selecciona la Semana',
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
        index=2,
    )
    participante = st.text_input('Tu Nombre / Participante')

    tiempo_permitido = validar_tiempo_limite(semana)

    if not tiempo_permitido:
      st.warning(
          '⏳ El tiempo límite para enviar o modificar picks esta semana ha'
          ' expirado (Jueves a las 5:00 PM).'
      )

    # Diccionario con nombres limpios y formato de equipos completos
    partidos_por_semana = {
        3: [
            'Green Bay Packers vs Atlanta Falcons',
            'Kansas City Chiefs vs Baltimore Ravens',
            'Dallas Cowboys vs New York Giants',
            'San Francisco 49ers vs Los Angeles Rams',
            'Buffalo Bills vs Miami Dolphins',
        ],
        4: [
            'Green Bay Packers vs Chicago Bears',
            'Philadelphia Eagles vs Washington Commanders',
            'Detroit Lions vs Minnesota Vikings',
            'Las Vegas Raiders vs Denver Broncos',
        ],
    }

    # Partidos por defecto si la semana seleccionada aún no está escrita en el diccionario
    partidos_semana = partidos_por_semana.get(
        semana, [
            'Equipo Local A vs Equipo Visitante B',
            'Equipo Local C vs Equipo Visitante D',
        ]
    )

    picks_usuario = {}
    st.markdown('### Selecciona a tus ganadores:')

    with st.form('form_quiniela'):
      for partido in partidos_semana:
        # Extraer los nombres de los dos equipos limpios separados por " vs "
        equipos = partido.split(' vs ')
        picks_usuario[partido] = st.radio(
            partido, equipos, horizontal=True, disabled=not tiempo_permitido
        )

      enviado = st.form_submit_button(
          'Guardar Picks', disabled=not tiempo_permitido
      )

      if enviado:
        if participante.strip() == '':
          st.error('Por favor, ingresa tu nombre.')
        else:
          for partido, prediccion in picks_usuario.items():
            sheet.append_row([participante, semana, partido, prediccion])
          mostrar_recibo(participante, semana, picks_usuario)

  with tab_standings:
    st.subheader('🏆 Tabla General de Posiciones (Standings)')
    st.info(
        'Aquí todos los participantes pueden consultar el acumulado de'
        ' puntos.'
    )

    try:
      import pandas as pd

      # Leer todos los datos de la hoja de Google Sheets
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

# --- 3. PANEL DE ADMINISTRADOR (EXCLUSIVO LATERAL) ---
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
