import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

st.set_page_config(page_title="Rifas María - Tabla de Números", page_icon="🎟️", layout="centered")

# ===== Colores marca =====
COLOR_DISP = "#FFD60A"    # Amarillo
COLOR_VEND = "#E63946"    # Rojo
TEXT_ON_YELLOW = "#000000"
TEXT_ON_RED = "#FFFFFF"

# ===== Logo =====
c1, c2, c3 = st.columns([1,3,1])
with c2:
    try:
        st.image("assets/logo_rifas_maria.png", width=180)
    except Exception:
        pass

st.markdown("<h2 style='text-align:center;'>Tabla de Números - Rifas María</h2>", unsafe_allow_html=True)
st.caption("Toca los números para marcar Vendido/Disponible. Usa el botón de descarga para compartir en WhatsApp.")

# ===== Estado =====
nums = [f"{i:02d}" for i in range(100)]
if "estado" not in st.session_state:
    st.session_state.estado = {n: False for n in nums}  # False=Disponible, True=Vendido

# ===== Controles =====
c1, c2, c3 = st.columns([1,1,1])
with c1:
    if st.button("🔄 Reiniciar tablero"):
        st.session_state.estado = {n: False for n in nums}
with c3:
    st.metric("Vendidos", sum(st.session_state.estado.values()))

# ===== CSS: pinta los toggles como píldoras alineadas =====
st.markdown(f"""
<style>
/* quita etiqueta a la izquierda del toggle */
div[data-testid="stTickBar"] {{ display:none; }}
/* contenedor de cada toggle */
.pill {{
  display:flex; justify-content:center; align-items:center;
  width:100%; margin:2px 0;
}}
/* input checkbox nativo oculto */
.pill input {{ display:none; }}
/* la “pastilla” clickeable */
.pill label {{
  width:100%; text-align:center; font-weight:800; padding:10px 0;
  border-radius:14px; border:2px solid #222;
  background:{COLOR_DISP}; color:{TEXT_ON_YELLOW};
  cursor:pointer; user-select:none;
}}
/* estado vendido */
.pill input:checked + label {{
  background:{COLOR_VEND}; color:{TEXT_ON_RED}; border-color:#000;
}}
</style>
""", unsafe_allow_html=True)

# ===== Grilla 10 x 10 con toggles nativos (rápidos) =====
for fila in range(10):
    cols = st.columns(10, gap="small")
    for j in range(10):
        n = f"{fila*10 + j:02d}"
        # usamos checkbox oculto + label como pill
        checked = st.session_state.estado[n]
        with cols[j]:
            # HTML de toggle sin JS: el click envía el form implícito y Streamlit reevalúa
            # Para sincronizar estado, usamos un form mini por celda con un submit implícito:
            form_key = f"form_{n}"
            with st.form(form_key):
                st.markdown(
                    f"<div class='pill'>"
                    f"<input id='t_{n}' name='t_{n}' type='checkbox' {'checked' if checked else ''}>"
                    f"<label for='t_{n}'>{n}</label>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                submitted = st.form_submit_button(" ", use_container_width=True)
                if submitted:
                    st.session_state.estado[n] = not checked

# ===== Generador de PNG (centrado + título auto-fit + borde guía) =====
def build_image(estado):
    W, H = 1080, 1580
    margin = 60
    img = Image.new("RGB", (W, H), (255, 214, 10))
    draw = ImageDraw.Draw(img)

    # fuentes (con fallback)
    def tf(size, bold=False):
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
        except:
            return None
    font_title = tf(64, True)
    font_num   = tf(48, True)
    font_small = tf(34, False)

    # logo
    title_y = 30
    try:
        logo = Image.open("assets/logo_rifas_maria.png").convert("RGBA")
        r = 240 / logo.width
        logo = logo.resize((int(logo.width*r), int(logo.height*r)))
        img.paste(logo, (int((W - logo.width)//2), 30), logo)
        title_y = 30 + logo.height + 20
    except:
        pass

    # título con auto-ajuste (no cortar)
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

    # grid centrado
    top = title_y + 80
    left = margin
    cols = 10
    gaps = cols - 1
    gap = 16
    grid_w = W - 2*margin
    cell = (grid_w - gaps*gap) / cols
    real_w = cols*cell + gaps*gap
    left = int((W - real_w)//2)
    grid_h = 10*cell + 9*gap

    # borde guía
    draw.rounded_rectangle([left-12, top-12, left+real_w+12, top+grid_h+12], radius=18, outline=(0,0,0), width=4)

    # celdas
    for i in range(10):
        for j in range(10):
            num = f"{i*10 + j:02d}"
            sell = estado.get(num, False)
            fill = (230,57,70) if sell else (255,214,10)
            text = (255,255,255) if sell else (0,0,0)
            x = int(left + j*(cell + gap))
            y = int(top  + i*(cell + gap))
            draw.rounded_rectangle([x, y, int(x+cell), int(y+cell)], radius=20, fill=fill, outline=(0,0,0), width=2)
            tw = draw.textlength(num, font=font_num) if font_num else 20
            th = 40
            draw.text((int(x + (cell - tw)/2), int(y + (cell - th)/2)), num, fill=text, font=font_num)

    # leyenda
    legend_y = int(top + grid_h + 30)
    draw.rounded_rectangle([left, legend_y, left+30, legend_y+30], radius=6, fill=(255,214,10), outline=(0,0,0), width=2)
    draw.text((left+40, legend_y-2), "Disponible", fill=(0,0,0), font=font_small)
    lx = left + 260
    draw.rounded_rectangle([lx, legend_y, lx+30, legend_y+30], radius=6, fill=(230,57,70), outline=(0,0,0), width=2)
    draw.text((lx+40, legend_y-2), "Vendido", fill=(0,0,0), font=font_small)

    return img

img = build_image(st.session_state.estado)
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


