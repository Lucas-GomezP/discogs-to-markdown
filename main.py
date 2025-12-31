import requests
import streamlit as st
from datetime import date

# Configuración de la página (Opcional, pero queda mejor)
st.set_page_config(page_title="Discogs to Markdown", page_icon="🎵")

# --- SIDEBAR: CONFIGURACIÓN ---
with st.sidebar:
  st.header("⚙️ Configuración")
  
  st.info("Para usar esta app necesitas un Personal Access Token de Discogs.")
  
  # Input del Token (tipo password para que no se vea en pantalla)
  api_token = st.text_input("Ingresá tu Discogs Token:", type="password")
  
  st.markdown("[👉 Generar Token en Discogs](https://www.discogs.com/settings/developers)")
  
  st.divider()
  st.write("Esta herramienta busca información en Discogs y genera un archivo Markdown (.md) listo para usar en tu sitio web personal.")

# --- CUERPO PRINCIPAL ---
st.title("🎵 Búsqueda de vinilos por Barcode")

# --- INICIALIZAR SESSION STATE ---
if 'search_results' not in st.session_state:
  st.session_state.search_results = None
if 'masters_data' not in st.session_state:
  st.session_state.masters_data = None

# --- FORMULARIO DE BÚSQUEDA ---
with st.form("barcode_form"):
  barcode_input = st.text_input("Ingresá el código de barras del disco")
  submitted = st.form_submit_button("Buscar 🔎")

# --- LÓGICA DE BÚSQUEDA ---
if submitted:
  # 1. Validaciones antes de buscar
  if not api_token:
    st.error("⚠️ Por favor, ingresa tu Token de Discogs en el menú de la izquierda (sidebar) antes de buscar.")
    st.stop()
  
  if not barcode_input:
    st.warning("⚠️ Por favor ingresa un código de barras.")
    st.stop()

  # 2. Proceso de búsqueda
  clean_barcode = barcode_input.replace(" ", "").replace("-", "")
  search_url = "https://api.discogs.com/database/search"
  search_params = {
    "barcode": clean_barcode,
    "type": "release",
    "token": api_token # Usamos el token del input
  }

  with st.spinner("Conectando con Discogs..."):
    try:
      search_response = requests.get(search_url, params=search_params)
      
      # Manejo de error si el token es inválido
      if search_response.status_code == 401:
        st.error("❌ El Token ingresado no es válido o no tiene permisos.")
        st.stop()
          
      search_data = search_response.json()
      results = search_data.get("results", [])

      if results:
        st.session_state.search_results = results[0] 
        
        master_id = results[0].get("master_id")
        if master_id:
          res = requests.get(
            f"https://api.discogs.com/masters/{master_id}",
            headers={"Authorization": f"Discogs token={api_token}"}
          )
          if res.status_code == 200:
            st.session_state.masters_data = res.json()
          else:
            st.session_state.masters_data = None
        else:
          st.session_state.masters_data = None
          
        # Éxito:
        st.success("¡Disco encontrado!")
      else:
          st.warning("No se encontraron resultados para ese código de barras.")
          st.session_state.search_results = None
          st.session_state.masters_data = None

    except Exception as e:
      st.error(f"Error de conexión: {e}")

# --- MOSTRAR RESULTADOS Y EDICIÓN ---
if st.session_state.search_results:
  
  result = st.session_state.search_results
  masters = st.session_state.masters_data

  # Variables
  title = result.get("title", "Sin título")
  cover_image = result.get("cover_image", "")
  country = result.get("country", "Desconocido")
  year = result.get("year", "Desconocido")
  fmt = result.get("format", [])
  tipo = result.get("type", "")
  genre = result.get("genre", [])
  style = result.get("style", [])

  st.divider()
  
  # Layout de resultados
  col_img, col_info = st.columns([1, 2])
  
  with col_img:
    if cover_image:
      st.image(cover_image, caption="Carátula Discogs", width="stretch")
    else:
      st.info("Sin imagen disponible")

  with col_info:
    st.subheader(title)
    st.markdown(f"**País:** {country} | **Año:** {year}")
    st.markdown(f"**Formato:** {', '.join(fmt)}")
    st.markdown(f"**Género:** {', '.join(genre)}")
    st.markdown(f"**Estilo:** {', '.join(style)}")

  # Master Data Section
  artist_master = "N/A"
  title_master = "N/A"
  original_year = "N/A"
  tracklist_parsed = []

  if masters:
    with st.expander("💿 Ver Datos del Master (Tracklist, Artista Original)", expanded=False):
      artist_master = masters.get("artists", [{}])[0].get("name", "N/A")
      st.write(f"**Artista Master:** {artist_master}")
      title_master = masters.get("title", "N/A")
      original_year = masters.get("year", "N/A")
      st.write(f"**Año Original:** {original_year}")
      
      tracklist = masters.get("tracklist", [])
      tracklist_parsed = [f"{t.get('title')} ({t.get('position')}) - {t.get('duration')}" for t in tracklist]
      st.text("\n".join(tracklist_parsed))

  st.divider()
  st.subheader("📝 Información Personal & Notas")

  # Inputs de usuario
  c1, c2 = st.columns(2)
  with c1:
    estado = st.selectbox("Estado del Disco (Media)", 
                          ["Mint (M)", "Near Mint (NM)", "Very Good Plus (VG+)", "Very Good (VG)", "Good (G)", "Poor (P)"])
    fecha_adquisicion = st.date_input("Fecha de adquisición", date.today())
      
  with c2:
    estado_portada = st.selectbox("Estado de Portada (Sleeve)", 
                                  ["Mint (M)", "Near Mint (NM)", "Very Good Plus (VG+)", "Very Good (VG)", "Good (G)", "Poor (P)"])
    tipo_adquisicion = st.selectbox("Origen", ["Compra", "Regalo", "Herencia", "Hallazgo"], key="tipo_adquisicion")
  
  advertencias = st.text_area("Advertencias / Detalles", placeholder="Ej: Salta en el track 3...", key="advertencias")
  historia = st.text_area("La Historia / Reseña", placeholder="Escribe aquí tu reseña o recuerdos asociados...", key="historia", height=150)

  # Preparación del archivo
  file_slug = title.replace(" ", "").lower() if title else "disco"
  # Limpiamos caracteres raros para el nombre del archivo
  file_slug = "".join(x for x in file_slug if x.isalnum())
  filename_md = f"{file_slug}.md"

  str_format = ", ".join(fmt) if fmt else ""
  str_genre = ", ".join(genre) if genre else ""
  str_style = ", ".join(style) if style else ""

  md_content = f"""---
complete_title: {title}
artist: {artist_master}
title: {title_master}
year: {year}
original_year: {original_year}
country: {country}
format: {str_format}
type: {tipo}
genre: {str_genre}
style: {str_style}
tracklist: {tracklist_parsed}
estado: {estado}
estado_portada: {estado_portada}
image: {cover_image}
fecha_adquisicion: {fecha_adquisicion}
tipo_adquisicion: {tipo_adquisicion}
advertencias: {advertencias}
---
{historia}
"""

  st.download_button(
    label="📥 Descargar archivo .md",
    data=md_content,
    file_name=filename_md,
    mime="text/markdown",
    type="primary",
    width="stretch"
  )

# --- FOOTER / PIE DE PÁGINA ---
st.markdown("---")
st.markdown("### 👨‍💻 Sobre el Desarrollador")

# Aquí debes reemplazar las URLs con las tuyas reales
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
  st.markdown("**[🌐 Mi Colección de Vinilos](https://punk-records-pi.vercel.app)**")
with col_f2:
  st.markdown("**[🐙 Github](https://github.com/Lucas-GomezP)**")
with col_f3:
  st.markdown("**[📸 Instagram](https://www.instagram.com/lucas.gomezp)**")
with col_f4:
  st.markdown("**📧 gomezplucas@gmail.com**")

st.markdown("""
<div style="text-align: center; margin-top: 20px; color: gray; font-size: 0.8em;">
    Desarrollado con ❤️ usando Streamlit y la API de Discogs.<br>
    <a href="https://github.com/Lucas-GomezP/discogs-to-markdown" target="_blank">Ver código fuente de esta App</a>
</div>
""", unsafe_allow_html=True)