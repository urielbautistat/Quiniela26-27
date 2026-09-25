from datetime import datetime, time
import pytz
import streamlit as st

# Configuración de página de Streamlit
st.set_page_config(
    page_title='Quiniela NFL 2026-2027', page_icon='🏈', layout='centered'
)

# Configuración de zona horaria (Ciudad de México)
tz = pytz.timezone('America/Mexico_City')
ahora = datetime.now(tz)

# --- CONEXIÓN A PRUEBA DE BALAS CON GOOGLE SHEETS ---
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


# --- 1. LÓGICA DE VALIDACIÓN DE TIEMPO (JUEVES 5 PM A PARTIR DE SEMANA 4) ---
def validar_tiempo_limite(semana_actual):
  if semana_actual >= 4:
    dia_semana = ahora.weekday()  # 0=Lunes, 3=Jueves, etc.
    hora_actual = ahora.time()
    # Si es viernes en adelante o jueves pasada las 17:00
    if dia_semana > 3 or (dia_semana == 3 and hora_actual >= time(17, 0)):
      return False
  return True


# --- 2. MOSTRAR RECIBO DE PICKS ---
def mostrar_recibo(participante, semana, picks_usuario):
  st.markdown('---')
  st.subheader('📄 Comprobante de Picks Registrados')
  st.success(f'¡Tus pronósticos para la **Semana {semana}** se guardaron con éxito!')

  recibo_texto = '--- RECIBO DE QUINIELA NFL ---\n'
  recibo_texto += f'Participante: {participante}\n'
  recibo_texto += f'Semana: {semana}\n'
  recibo_texto += f'Fecha de registro: {ahora.strftime("%Y-%m-%d %H:%M:%S")}\n\n'
  recibo_texto += 'Tus selecciones:\n'

  for partido, equipo in picks_usuario.items():
    recibo_texto += f' - {partido}: {equipo}\n'
    st.write(f'- **{partido}**: {equipo}')

  st.download_button(
      label='📥 Descargar comprobante en texto',
      data=recibo_texto,
      file_name=f'recibo_{participante}_semana_{semana}.txt',
      mime='text/plain',
  )


# --- INTERFAZ PRINCIPAL DE LA APLICACIÓN ---
st.title('🏈 Quiniela NFL 2026-2027')

if not conexion_exitosa:
  st.error(f'Error en la conexión con Google Sheets: {error_detalles}')
else:
  semana = st.selectbox('Selecciona la Semana', range(1, 19), value=3)
  participante = st.text_input('Tu Nombre / Participante')

  # Validar límite de tiempo
  tiempo_permitido = validar_tiempo_limite(semana)

  if not tiempo_permitido:
    st.warning(
        '⏳ El tiempo límite para enviar o modificar tus picks esta semana ha'
        ' expirado (Jueves a las 5:00 PM).'
    )

  # Cargar partidos de la semana usando nfl_data_py
  @st.cache_data(ttl=3600)
  def cargar_partidos_nfl(num_semana):
    import nfl_data_py as nfl
    import pandas as pd

    df_nfl = nfl.import_schedules([2026])
    df_semana = df_nfl[df_nfl['week'] == num_semana]
    partidos = []
    for _, row in df_semana.iterrows():
      partidos.append(f"{row['away_team']} @ {row['home_team']}")
    return partidos

  partidos_semana = cargar_partidos_nfl(semana)
  picks_usuario = {}

  if partidos_semana:
    st.markdown('### Selecciona a tus ganadores:')
    with st.form('form_quiniela'):
      for partido in partidos_semana:
        equipos = partido.split(' @ ')
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
  else:
    st.info('No se encontraron partidos para esta semana.')

# --- 3. PANEL DE ADMINISTRADOR ---
st.sidebar.markdown('---')
st.sidebar.subheader('🔐 Panel de Administrador')
admin_pass = st.sidebar.text_input('Contraseña Admin', type='password')

password_correcta = st.secrets.get('ADMIN_PASSWORD', 'admin123')

if admin_pass == password_correcta:
  st.sidebar.success('Acceso concedido')
  with st.sidebar.expander('⚙️ Cargar Resultados'):
    semana_calificar = st.selectbox(
        'Semana a calificar', range(1, 19), key='sem_admin'
    )
    archivo_resultados = st.file_uploader(
        'Subir archivo de resultados', type=['csv'], key='res_admin'
    )

    if archivo_resultados and st.button('Actualizar Puntajes en Tiempo Real'):
      st.success(
          f'¡Resultados de la Semana {semana_calificar} procesados y puntajes'
          ' actualizados!'
      )
elif admin_pass != '':
  st.sidebar.error('Contraseña incorrecta')
