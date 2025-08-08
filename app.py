import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

st.set_page_config(page_title="Rifas María - Tabla de Números", page_icon="🎟️", layout="centered")

# ===== Colores marca =====
COLOR_DISP = "#FFD60A"    # Amarillo (fondo / disponible)
COLOR_VEND = "#E63946"    # Rojo (vendido)
TEXT_DARK   = "#000000"
TEXT_LIGHT  = "#FFFFFF"

# ===== Header =====
c1, c2, c3 = st.columns([1,3,1])
with c2:
    try:
        st.image("assets/logo_rifas_maria.png", width=180)
    except Exception:
        pass

st.markdown("<h2 style='text-align:center;'>Tabla de Números - Rifas María</h2>", unsafe_allow_html=True)
st.caption("Selecciona en la lista los números vendidos. La cuadrícula se actualiza al instante. Descarga la imagen para compartirla en WhatsApp.")

# ===== Estado simplificado: UN SOLO widget =====
nums = [f"{i:02d}" for i in range(100)]
vendidos = st.multiselect("Números vendidos", options=nums, default=[], placeholder="Ej: 00, 04, 17, 24")

st.metric("Vendidos", len(vendidos))

# ===== Render visual (solo lectura) =====
# CSS de la cuadrícula: disponibles = borde; vendidos = rojo
st.markdown(f"""
<style>
.grid {{
  display: grid; grid-template-columns: repeat(10, 1fr);
  gap: 10px; max-width: 680px; margin: 20px auto;
}}
.cell {{
  border: 2px solid #222; border-radius: 14px; padding: 10px 0;
  text-align:center; font-weight:800; background: transparent; color: {TEXT_DARK};
}}
.cell.vendido {{
  background: {COLOR_VEND}; color: {TEXT_LIGHT};
}}
</style>
""", unsafe_allow_html=True)

html = ["<div class='grid'>"]
vendidos_set = set(vendidos)
for i in range(100):
    n = f"{i:02d}"
    cls = "cell vendido" if n in vendidos_set else "cell"
    html.append(f"<div class='{cls}'>{n}</div>")
html.append("</div>")
st.markdown("".join(html), unsafe_allow_html=True)

# ===== Generar PNG idéntico al estilo “bonito” =====
def build_image(vendidos_list):
    vendidos_set = set(vendidos_list)
    W, H = 1080, 1580
    margin = 60
    img = Image.new("RGB", (W, H), (255, 214, 10))  # fondo amarillo
    draw = ImageDraw.Draw(img)

    def tf(size, bold=False):
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
        except:
            return None

    font_title = tf(64, True)
    font_num   = tf(48, True)
    font_small = tf(34, False)

    # Logo
    title_y = 30
    try:
        logo = Image.open("assets/logo_rifas_maria.png").convert("RGBA")
        r = 240 / logo.width
        logo = logo.resize((int(logo.width*r), int(logo.height*r)))
        img.paste(logo, (int((W - logo.width)//2), 30), logo)
        title_y = 30 + logo.height + 20
    except:
        pass

    # Título auto-fit
    title = "Tabla de Números - Rifas María"
    size = 64
    while True:
        f = tf(size, True)
        t_w = draw.textlength(title, font=f) if f else len(title)*24
        if t_w <= W - 2*margin or size <= 28:
            font_title = f
            break
        size -= 2
    draw.text(((W - t_w)//2, title_y), title, fill=(0,0,0), font=font_title)

    # Grid centrado
    top = title_y + 80
    cols = 10
    gap = 16
    grid_w = W - 2*margin
    cell = (grid_w - (cols-1)*gap) / cols
    real_w = cols*cell + (cols-1)*gap
    left = int((W - real_w)//2)
    grid_h = 10*cell + 9*gap

    # Borde guía
    draw.rounded_rectangle([left-12, top-12, left+real_w+12, top+grid_h+12],
                           radius=18, outline=(0,0,0), width=4)

    # Celdas
    for i in range(10):
        for j in range(10):
            n = f"{i*10 + j:02d}"
            sold = n in vendidos_set
            fill = (230,57,70) if sold else (255,214,10)
            text = (255,255,255) if sold else (0,0,0)
            x = int(left + j*(cell + gap))
            y = int(top  + i*(cell + gap))
            draw.rounded_rectangle([x, y, int(x+cell), int(y+cell)],
                                   radius=20, fill=fill, outline=(0,0,0), width=2)
            tw = draw.textlength(n, font=font_num) if font_num else 20
            th = 40
            draw.text((int(x + (cell - tw)/2), int(y + (cell - th)/2)),
                      n, fill=text, font=font_num)

    # Leyenda
    legend_y = int(top + grid_h + 30)
    # disponible
    draw.rounded_rectangle([left, legend_y, left+30, legend_y+30],
                           radius=6, fill=(255,214,10), outline=(0,0,0), width=2)
    draw.text((left+40, legend_y-2), "Disponible", fill=(0,0,0), font=font_small)
    # vendido
    lx = left + 260
    draw.rounded_rectangle([lx, legend_y, lx+30, legend_y+30],
                           radius=6, fill=(230,57,70), outline=(0,0,0), width=2)
    draw.text((lx+40, legend_y-2), "Vendido", fill=(0,0,0), font=font_small)

    return img

img = build_image(vendidos)
buf = io.BytesIO()
img.save(buf, format="PNG")
buf.seek(0)
st.download_button(
    "📥 Descargar imagen del tablero",
    data=buf,
    file_name=f"rifa_maria_{datetime.now().date().isoformat()}.png",
    mime="image/png"
)

st.caption("© Rifas María")
