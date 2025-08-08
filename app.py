import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io, base64

st.set_page_config(page_title="Rifas María - Tabla de Números", page_icon="🎟️", layout="centered")

# ===== Colores marca =====
COLOR_DISP = "#FFD60A"    # Amarillo (disponible)
COLOR_VEND = "#E63946"    # Rojo (vendido)
TEXT_DARK   = "#000000"
TEXT_LIGHT  = "#FFFFFF"

# =========================
#  Helpers URL (persistencia sin DB)
# =========================
def get_query_params():
    try:
        qp = dict(st.query_params)  # streamlit >= 1.36
        return {k: v for k, v in qp.items()}
    except Exception:
        qp = st.experimental_get_query_params()
        return {k: (v[0] if isinstance(v, list) else v) for k, v in qp.items()}

def set_query_params(**kwargs):
    try:
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**kwargs)

def parse_sold_param(s: str):
    if not s:
        return []
    out = []
    for p in s.replace(",", " ").split():
        if p.isdigit():
            out.append(f"{int(p):02d}")
    return out

# =========================
#  Header
# =========================
c1, c2, c3 = st.columns([1,3,1])
with c2:
    try:
        st.image("assets/logo_rifas_maria.png", width=180)
    except Exception:
        pass

st.markdown("<h2 style='text-align:center;'>Tabla de Números - Rifas María</h2>", unsafe_allow_html=True)
st.caption("Selecciona o pega números vendidos. El estado se guarda en el enlace. Comparte la imagen directo a WhatsApp.")

# =========================
#  Estado desde URL
# =========================
nums = [f"{i:02d}" for i in range(100)]
qp = get_query_params()
vendidos_init = [n for n in parse_sold_param(qp.get("sold", "")) if n in nums]
rifa_init = qp.get("rifa", f"Rifa {datetime.now().date().isoformat()}")

if "vendidos" not in st.session_state:
    st.session_state.vendidos = vendidos_init
if "rifa" not in st.session_state:
    st.session_state.rifa = rifa_init

# =========================
#  Controles compactos
# =========================
st.session_state.rifa = st.text_input("Nombre de la rifa", st.session_state.rifa)

cA, cB, cC = st.columns([2,1,1])
with cA:
    sel = st.selectbox("Número", options=nums, index=0, help="Busca y elige un número (00–99)")
with cB:
    if st.button("➕ Agregar", use_container_width=True):
        if sel not in st.session_state.vendidos:
            st.session_state.vendidos.append(sel)
with cC:
    if st.button("➖ Quitar", use_container_width=True):
        if sel in st.session_state.vendidos:
            st.session_state.vendidos.remove(sel)

# Pegar varios a la vez
with st.form("bulk", clear_on_submit=True):
    bulk = st.text_input("Agregar varios (separados por coma o espacio)", placeholder="Ej: 00, 04 17 24 33")
    apply_bulk = st.form_submit_button("✅ Aplicar")
    if apply_bulk and bulk.strip():
        nuevos = [n for n in parse_sold_param(bulk) if n in nums]
        s = set(st.session_state.vendidos)
        s.update(nuevos)
        st.session_state.vendidos = sorted(s)

# Métricas y acciones
m1, m2, m3 = st.columns([1,1,2])
with m1:
    st.metric("Vendidos", len(st.session_state.vendidos))
with m2:
    if st.button("🔄 Reiniciar tablero", use_container_width=True):
        st.session_state.vendidos = []
        set_query_params(rifa=st.session_state.rifa, sold="")
        st.rerun()
with m3:
    set_query_params(rifa=st.session_state.rifa, sold=",".join(st.session_state.vendidos))
    st.caption("Estado guardado en el enlace.")

# Lista de vendidos colapsable
with st.expander(f"Ver/editar vendidos ({len(st.session_state.vendidos)})", expanded=False):
    if st.session_state.vendidos:
        cols = st.columns(10)
        for idx, n in enumerate(sorted(st.session_state.vendidos)):
            with cols[idx % 10]:
                if st.button(f"✖ {n}", key=f"rm_{n}", use_container_width=True):
                    st.session_state.vendidos.remove(n)
                    set_query_params(rifa=st.session_state.rifa, sold=",".join(st.session_state.vendidos))
                    st.rerun()
    else:
        st.write("_Sin vendidos por ahora_")

# =========================
#  Cuadrícula visual (solo lectura)
# =========================
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
.cell.vendido {{ background: {COLOR_VEND}; color: {TEXT_LIGHT}; }}
</style>
""", unsafe_allow_html=True)

vendidos_set = set(st.session_state.vendidos)
html = ["<div class='grid'>"]
for i in range(100):
    n = f"{i:02d}"
    cls = "cell vendido" if n in vendidos_set else "cell"
    html.append(f"<div class='{cls}'>{n}</div>")
html.append("</div>")
st.markdown("".join(html), unsafe_allow_html=True)

# =========================
#  PNG bonito (centrado, sin cortes)
# =========================
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
    draw.text((left+40, legend_y-2), "Disponible", fill=(0,0,0), font=font_small)
    lx = left + 260
    draw.rounded_rectangle([lx, legend_y, lx+30, legend_y+30],
                           radius=6, fill=(230,57,70), outline=(0,0,0), width=2)
    draw.text((lx+40, legend_y-2), "Vendido", fill=(0,0,0), font=font_small)

    return img

titulo = f"Tabla de Números - {st.session_state.rifa}".strip()
img = build_image(st.session_state.vendidos, titulo)
buf = io.BytesIO()
img.save(buf, format="PNG")
png_bytes = buf.getvalue()
buf.seek(0)

# ====== BOTÓN DE COMPARTIR (Web Share API) con fallback a descarga ======
b64 = base64.b64encode(png_bytes).decode("utf-8")
data_url = f"data:image/png;base64,{b64}"
filename = f"rifa_maria_{datetime.now().date().isoformat()}.png"

st.html(f"""
<div style="display:flex; gap:12px; align-items:center; justify-content:center; margin-top:10px;">
  <button id="shareBtn" style="
      background:#25D366; color:white; border:none; border-radius:10px;
      padding:10px 14px; font-weight:700; cursor:pointer;">
    📤 Compartir imagen
  </button>
  <a id="downloadLink" href="{data_url}" download="{filename}" style="
      background:#374151; color:white; text-decoration:none; border-radius:10px;
      padding:10px 14px; font-weight:700;">
    ⬇️ Descargar
  </a>
</div>
<script>
async function shareImage() {{
  try {{
    const res = await fetch("{data_url}");
    const blob = await res.blob();
    const file = new File([blob], "{filename}", {{ type: "image/png" }});

    if (navigator.canShare && navigator.canShare({{ files: [file] }})) {{
      await navigator.share({{
        files: [file],
        title: "Rifas María",
        text: "{titulo}"
      }});
    }} else {{
      // Fallback: dispara descarga y explica
      document.getElementById('downloadLink').click();
      alert("Tu navegador no permite compartir directamente. Se descargó la imagen; compártela desde WhatsApp.");
    }}
  }} catch (e) {{
    console.error(e);
    document.getElementById('downloadLink').click();
    alert("No se pudo compartir. Se descargó la imagen; envíala desde la galería.");
  }}
}}
document.getElementById("shareBtn").addEventListener("click", shareImage);
</script>
""")

st.caption("© Rifas María")










