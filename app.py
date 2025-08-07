import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

st.set_page_config(page_title="Rifas María - Tabla de Números", page_icon="🎟️", layout="centered")

# ====== Colores de marca ======
COLOR_DISP = "#FFD60A"   # Amarillo
COLOR_VEND = "#E63946"   # Rojo
TEXT_ON_YELLOW = "#000000"
TEXT_ON_RED = "#FFFFFF"
BG_PAGE = st.get_option("theme.backgroundColor") or "#0E1117"

# ====== Encabezado con logo ======
c1, c2, c3 = st.columns([1,3,1])
with c2:
    try:
        logo = Image.open("assets/logo_rifas_maria.png")
        st.image(logo, width=180)
    except Exception:
        st.write("")

st.markdown("<h2 style='text-align:center; margin-top:0;'>Tabla de Números - Rifas María</h2>", unsafe_allow_html=True)
st.caption("Toca los números para marcar Vendido/Disponible. El color se actualiza al instante. Usa el botón de descarga para compartir en WhatsApp.")

# ====== Estado ======
nums = [f"{i:02d}" for i in range(100)]
if "estado" not in st.session_state:
    st.session_state.estado = {n: "D" for n in nums}  # D=Disponible, V=Vendido

# ====== Controles ======
c1, c2, c3 = st.columns([1,1,1])
with c1:
    if st.button("🔄 Reiniciar tablero"):
        st.session_state.estado = {n: "D" for n in nums}
with c3:
    vendidos_total = sum(1 for v in st.session_state.estado.values() if v == "V")
    st.metric("Vendidos", vendidos_total)

# ====== CSS para los “pills” ======
st.markdown(f"""
<style>
.pill {{
  border-radius:14px; padding:10px 0; font-weight:800; text-align:center;
  width:100%;
}}
.pill-d {{ background:{COLOR_DISP}; color:{TEXT_ON_YELLOW}; }}
.pill-v {{ background:{COLOR_VEND}; color:{TEXT_ON_RED}; }}
.btn-clear > div > button {{ visibility:hidden; height:0; padding:0; margin:0; }}
</style>
""", unsafe_allow_html=True)

# ====== Cuadrícula 10x10 ======
# Truco: mostramos el “pill” coloreado y debajo un botón invisible que hace el toggle.
for fila in range(10):
    cols = st.columns(10, gap="small")
    for j in range(10):
        n = f"{fila*10 + j:02d}"
        vendido = st.session_state.estado[n] == "V"
        pill_class = "pill-v" if vendido else "pill-d"
        cols[j].markdown(f"<div class='pill {pill_class}'>{n}</div>", unsafe_allow_html=True)
        # Botón invisible (mismo ancho) que cambia estado
        with cols[j].container():
            if st.button(" ", key=f"btn_{n}", help=f"Toggle {n}", type="secondary"):
                st.session_state.estado[n] = "D" if vendido else "V"
        cols[j].markdown("<div class='btn-clear'></div>", unsafe_allow_html=True)

# ====== Generador de PNG mejorado (centrado + sin corte + guía) ======
def build_image(estado):
    W, H = 1080, 1580   # un poco más alto para encabezado/leyenda
    margin = 60
    img = Image.new("RGB", (W, H), (255, 214, 10))  # fondo amarillo
    draw = ImageDraw.Draw(img)

    # Tipografías
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
        font_num   = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 36)
    except:
        font_title = font_num = font_small = None

    # Logo
    title_y = 30
    try:
        logo = Image.open("assets/logo_rifas_maria.png").convert("RGBA")
        max_w = 240
        r = max_w / logo.width
        logo = logo.resize((int(logo.width*r), int(logo.height*r)))
        img.paste(logo, (int((W - logo.width)//2), 30), logo)
        title_y = 30 + logo.height + 20
    except:
        pass

    # Título
    title = "Tabla de Números - Rifas María"
    t_w = draw.textlength(title, font=font_title) if font_title else len(title)*24
    draw.text(((W - t_w)//2, title_y), title, fill=(0,0,0), font=font_title)

    # Cálculo dinámico de celdas para NO cortar columnas
    top = title_y + 80
    left = margin
    right = W - margin
    grid_w = right - left
    cols = 10
    gaps = cols - 1
    gap = 16
    cell = (grid_w - gaps*gap) / cols
    # centrar exacto
    real_w = cols*cell + gaps*gap
    left = int((W - real_w)//2)

    # Dibujar borde guía alrededor de la grilla
    grid_h = 10*cell + 9*gap
    draw.rounded_rectangle([left-12, top-12, left+real_w+12, top+grid_h+12], radius=18, outline=(0,0,0), width=4)

    # Celdas
    for i in range(10):
        for j in range(10):
            num = f"{i*10 + j:02d}"
            vend = estado.get(num) == "V"
            fill = (230,57,70) if vend else (255,214,10)   # rojo/amarillo
            text = (255,255,255) if vend else (0,0,0)
            x = int(left + j*(cell + gap))
            y = int(top  + i*(cell + gap))
            draw.rounded_rectangle([x, y, int(x+cell), int(y+cell)], radius=20, fill=fill, outline=(0,0,0), width=2)
            # número centrado
            tw = draw.textlength(num, font=font_num) if font_num else 20
            th = 40
            tx = int(x + (cell - tw)/2)
            ty = int(y + (cell - th)/2)
            draw.text((tx, ty), num, fill=text, font=font_num)

    # Leyenda
    legend_y = int(top + grid_h + 30)
    # disponible
    draw.rounded_rectangle([left, legend_y, left+30, legend_y+30], radius=6, fill=(255,214,10), outline=(0,0,0), width=2)
    draw.text((left+40, legend_y-2), "Disponible", fill=(0,0,0), font=font_small)
    # vendido
    lx = left + 240
    draw.rounded_rectangle([lx, legend_y, lx+30, legend_y+30], radius=6, fill=(230,57,70), outline=(0,0,0), width=2)
    draw.text((lx+40, legend_y-2), "Vendido", fill=(0,0,0), font=font_small)

    return img

img = build_image(st.session_state.estado)
buf = io.BytesIO()
img.save(buf, format="PNG")
buf.seek(0)
filename = f"rifa_maria_{datetime.now().date().isoformat()}.png"
st.download_button("📥 Descargar imagen del tablero", data=buf, file_name=filename, mime="image/png")

st.caption("© Rifas María")
