import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

st.set_page_config(page_title="Rifas María - Tabla de Números", page_icon="🎟️", layout="centered")

# ===== Colores marca =====
COLOR_DISP = "#FFD60A"    # Amarillo (disponible)
COLOR_VEND = "#E63946"    # Rojo (vendido)
TEXT_DARK   = "#000000"
TEXT_LIGHT  = "#FFFFFF"

# ===== Utilidades URL (persistencia) =====
def get_query_params():
    # Compatibilidad con versiones nuevas/antiguas de Streamlit
    try:
        qp = dict(st.query_params)
        # st.query_params devuelve valores tipo str (no listas)
        return {k: v for k, v in qp.items()}
    except Exception:
        qp = st.experimental_get_query_params()
        return {k: (v[0] if isinstance(v, list) else v) for k, v in qp.items()}

def set_query_params(**kwargs):
    try:
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**kwargs)

def parse_sold_param(s):
    if not s:
        return []
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p.isdigit() and len(p) in (1,2)]

# ===== Header =====
c1, c2, c3 = st.columns([1,3,1])
with c2:
    try:
        st.image("assets/logo_rifas_maria.png", width=180)
    except Exception:
        pass

st.markdown("<h2 style='text-align:center;'>Tabla de Números - Rifas María</h2>", unsafe_allow_html=True)
st.caption("Selecciona en la lista los números vendidos. La cuadrícula se actualiza al instante y se guarda en el enlace. Descarga la imagen para compartirla en WhatsApp.")

# ===== Cargar estado inicial desde URL =====
qp = get_query_params()
vendidos_init = [f"{int(x):02d}" for x in parse_sold_param(qp.get("sold", ""))]
rifa_init = qp.get("rifa", f"Rifa {datetime.now().date().isoformat()}")

# ===== Controles principales =====
rifa = st.text_input("Nombre de la rifa (se guarda en el enlace y en la imagen)", rifa_init)
nums = [f"{i:02d}" for i in range(100)]
vendidos = st.multiselect("Números vendidos", options=nums, default=vendidos_init, placeholder="Ej: 00, 04, 17, 24")
st.metric("Vendidos", len(vendidos))

# Sincronizar a URL (persistencia)
set_query_params(rifa=rifa, sold=",".join(vendidos))

# Botón Reiniciar
if st.button("🔄 Reiniciar tablero"):
    vendidos = []
    set_query_params(rifa=rifa, sold="")  # limpiar URL también
    st.rerun()

# ===== Render visual (solo lectura) =====
st.markdown(f"""
<style>
.grid {{
  display: grid; grid-template-columns: repeat(10, 1fr);
  gap: 10px; max-width: 680px; margin: 20px auto;
}}
.cell {{
  border: 2px solid #222; border-radius: 14px; padding: 10px 0;
  text-align:center; font-weight:800;
  background: {COLOR_DISP}; color: {TEXT_DARK};
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

# ===== Generar PNG bonito (centrado, sin cortes) =====
def build_image(vendidos_list, titulo):
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
    size = 64
    while True:
        f = tf(size, True)
        t_w = draw.textlength(titulo, font=f) if f else len(titulo)*24
        if t_w <= W - 2*margin or size <= 28:
            font_title = f
            break
        size -= 2
    draw.text(((W - t_w)//2, title_y), titulo, fill=(0,0,0), font=font_title)

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
    draw.rounded_rectangle([left, legend_y, left+30, legend_y+30],
                           radius=6, fill=(255,214,10), outline=(0,0,0), width=2)
    draw.text((left+40, legend_y-2), "Disponible", fill=(0,0,0), font=tf(34))
    lx = left + 260
    draw.rounded_rectangle([lx, legend_y, lx+30, legend_y+30],
                           radius=6, fill=(230,57,70), outline=(0,0,0), width=2)
    draw.text((lx+40, legend_y-2), "Vendido", fill=(0,0,0), font=tf(34))

    return img

titulo = f"Tabla de Números - {rifa}".strip()
img = build_image(vendidos, titulo)
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




