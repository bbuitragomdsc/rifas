import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

st.set_page_config(page_title="Rifas María - Tabla de Números", page_icon="🎟️", layout="centered")

# Colores
COLOR_DISP = "#FFD60A"   # Amarillo
COLOR_VEND = "#E63946"   # Rojo
TEXT_ON_YELLOW = "#000000"
TEXT_ON_RED = "#FFFFFF"

# Logo en la cabecera
col1, col2, col3 = st.columns([1,3,1])
with col2:
    try:
        logo = Image.open("assets/logo_rifas_maria.png")
        st.image(logo, width=180)
    except Exception:
        st.write("")

st.markdown("<h2 style='text-align:center; margin-top:0;'>Tabla de Números - Rifas María</h2>", unsafe_allow_html=True)
st.caption("Toca los números para marcar Vendido/Disponible. Usa el botón de descarga para compartir en WhatsApp.")

# Estado de los números
numbers = [f"{i:02d}" for i in range(100)]
if "estado" not in st.session_state:
    st.session_state.estado = {n: 'D' for n in numbers}

# Controles
c1, c2, c3 = st.columns([1,1,1])
with c1:
    if st.button("🔄 Reiniciar tablero"):
        st.session_state.estado = {n: 'D' for n in numbers}
with c3:
    vendidos_total = sum(1 for v in st.session_state.estado.values() if v == 'V')
    st.metric("Vendidos", vendidos_total)

# Cuadrícula de números
for fila in range(10):
    cols = st.columns(10, gap="small")
    for col_idx in range(10):
        n = f"{fila*10 + col_idx:02d}"
        is_v = st.session_state.estado[n] == 'V'
        bg = COLOR_VEND if is_v else COLOR_DISP
        fg = TEXT_ON_RED if is_v else TEXT_ON_YELLOW
        clicked = cols[col_idx].button(n, key=f"btn_{n}")
        if clicked:
            st.session_state.estado[n] = 'D' if is_v else 'V'

# Generar imagen para descarga
def build_image(estado_dict):
    W, H = 1080, 1280
    img = Image.new("RGB", (W, H), (255, 214, 10))
    draw = ImageDraw.Draw(img)
    title = "Tabla de Números - Rifas María"

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 56)
        small = ImageFont.truetype("DejaVuSans.ttf", 36)
    except:
        font = None
        small = None

    # Logo
    try:
        logo = Image.open("assets/logo_rifas_maria.png").convert("RGBA")
        max_w = 240
        ratio = max_w / logo.width
        logo = logo.resize((int(logo.width*ratio), int(logo.height*ratio)))
        img.paste(logo, (int((W - logo.width)//2), 20), logo)
        title_y = 20 + logo.height + 10
    except Exception:
        title_y = 30

    # Título
    w = draw.textlength(title, font=font) if font else len(title)*20
    draw.text(((W - w)//2, title_y), title, fill=(0,0,0), font=font)

    # Cuadrícula
    top = title_y + 80
    left = 60
    cell = 90
    gap = 18
    for i in range(10):
        for j in range(10):
            num = f"{i*10 + j:02d}"
            vend = estado_dict.get(num) == 'V'
            fill = (230,57,70) if vend else (255,214,10)
            text = (255,255,255) if vend else (0,0,0)
            x = left + j*(cell + gap)
            y = top + i*(cell + gap)
            draw.rounded_rectangle([x, y, x+cell, y+cell], radius=20, fill=fill)
            tw = draw.textlength(num, font=font) if font else 20
            tx = x + (cell - tw)//2
            ty = y + (cell - 40)//2
            draw.text((tx, ty), num, fill=text, font=font)

    # Leyenda
    legend_y = top + 10*(cell+gap) + 30
    draw.rounded_rectangle([left, legend_y, left+30, legend_y+30], radius=8, fill=(255,214,10))
    draw.text((left+40, legend_y), "Disponible", fill=(0,0,0), font=small)
    off_x = left + 240
    draw.rounded_rectangle([off_x, legend_y, off_x+30, legend_y+30], radius=8, fill=(230,57,70))
    draw.text((off_x+40, legend_y), "Vendido", fill=(0,0,0), font=small)

    return img

img = build_image(st.session_state.estado)
buf = io.BytesIO()
img.save(buf, format="PNG")
buf.seek(0)
filename = f"rifa_maria_{datetime.now().date().isoformat()}.png"
st.download_button("📥 Descargar imagen del tablero", data=buf, file_name=filename, mime="image/png")

st.caption("© Rifas María")
