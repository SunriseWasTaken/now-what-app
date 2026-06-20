import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from datetime import datetime
from scipy.spatial import Voronoi
from shapely.geometry import MultiPoint, Point, Polygon

st.set_page_config(
    page_title="Newham Risk Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global light theme + floating container CSS ────────────────────────────────
st.markdown(
    """
<style>
/* ── Strict light mode ── */
:root { color-scheme: light !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="block-container"], html, body {
    background: #f5f6f8 !important;
    color: #1e1e1e !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

html, body {
    height: 100vh !important;
    overflow: hidden !important;
    margin: 0 !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"] {
    height: 100vh !important;
    max-width: 100% !important;
    padding: 0 !important;
    overflow: hidden !important;
}

/* ── Full-screen map (deck.gl canvas) ── */
[data-testid="stDeckGlJsonChart"],
.stDeckGlJsonChart {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 1 !important;
}
[data-testid="stDeckGlJsonChart"] iframe,
.stDeckGlJsonChart iframe {
    width: 100vw !important;
    height: 100vh !important;
    border: none !important;
}

/* ━━ TRUE FLOATING CONTAINER (targets st.container(key="float_panel")) ━━ */
.st-key-float_panel {
    position: fixed !important;
    right: 20px !important;
    top: 20px !important;
    bottom: 20px !important;
    width: 350px !important;
    background: #ffffff !important;
    z-index: 999999 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    border: 1px solid #e5e7eb !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    padding: 0 !important;
}

/* Panel inner wrapper fills height for bottom-pinned chat */
.st-key-float_panel > div {
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    overflow: hidden !important;
}

/* Dark text inside panel (light mode) */
.st-key-float_panel,
.st-key-float_panel p,
.st-key-float_panel span,
.st-key-float_panel li,
.st-key-float_panel label { color: #1e1e1e !important; }

/* Scrollable chat history area */
.panel-scroll {
    flex: 1 1 auto !important;
    overflow-y: auto !important;
    padding: 0 18px 4px 18px !important;
}
.panel-scroll::-webkit-scrollbar { width: 4px; }
.panel-scroll::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }

/* Chat messages — light mode */
.st-key-float_panel [data-testid="stChatMessage"] {
    background: #f9fafb !important;
    border: 1px solid #eceef1 !important;
    border-radius: 10px !important;
    padding: 0.55rem 0.8rem !important;
    margin-bottom: 0.4rem !important;
}
.st-key-float_panel [data-testid="stChatMessage"] p,
.st-key-float_panel [data-testid="stChatMessage"] li {
    font-size: 0.85rem !important;
    line-height: 1.5 !important;
    color: #1e1e1e !important;
}

/* Chat input — pinned at bottom of the floating container, light mode */
.st-key-float_panel [data-testid="stChatInput"] {
    position: relative !important;
    bottom: auto !important;
    flex-shrink: 0 !important;
    padding: 0.6rem 1rem 1rem 1rem !important;
    border-top: 1px solid #e5e7eb !important;
    background: #ffffff !important;
    margin: 0 !important;
}
.st-key-float_panel [data-testid="stChatInput"] textarea {
    background: #f9fafb !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 22px !important;
    color: #1e1e1e !important;
    font-size: 0.85rem !important;
    padding: 0.6rem 1rem !important;
}
.st-key-float_panel [data-testid="stChatInput"] textarea:focus {
    border-color: #9ca3af !important;
    box-shadow: 0 0 0 2px rgba(156, 163, 175, 0.2) !important;
    outline: none !important;
}
.st-key-float_panel [data-testid="stChatInput"] textarea::placeholder { color: #9ca3af !important; }

/* Suppress Streamlit's global bottom chat dock */
[data-testid="stBottomBlockContainer"] { display: none !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Ward centroids ─────────────────────────────────────────────────────────────
WARD_COORDS: dict[str, tuple[float, float]] = {
    "Canning Town North":                (0.009,  51.514),
    "Custom House":                      (0.030,  51.511),
    "East Ham South":                    (0.053,  51.525),
    "Plaistow South":                    (0.020,  51.527),
    "Wall End":                          (0.056,  51.537),
    "Beckton":                           (0.068,  51.510),
    "Forest Gate South":                 (0.038,  51.543),
    "Canning Town South":                (0.012,  51.507),
    "West Ham":                          (0.009,  51.536),
    "Plaistow West & Canning Town East": (0.010,  51.522),
    "Royal Albert":                      (0.043,  51.503),
    "Plaistow North":                    (0.020,  51.534),
    "Stratford Olympic Park":            (0.014,  51.545),
    "Boleyn":                            (0.040,  51.536),
    "Maryland":                          (0.018,  51.548),
    "Manor Park":                        (0.060,  51.543),
    "East Ham":                          (0.048,  51.537),
    "Royal Victoria":                    (0.022,  51.503),
    "Little Ilford":                     (0.058,  51.549),
    "Forest Gate North":                 (0.038,  51.549),
    "Green Street East":                 (0.050,  51.536),
    "Green Street West":                 (0.044,  51.534),
    "Stratford":                         (0.003,  51.542),
    "Plashet":                           (0.046,  51.539),
}


@st.cache_data
def load_risk_data() -> pd.DataFrame:
    return pd.read_csv("data/newham_ward_risk_table_CDEM.csv")


@st.cache_data
def build_polygon_layer_data(df: pd.DataFrame) -> list[dict]:
    """Voronoi-tessellate ward centroids into flat polygons coloured by Final Risk Score."""
    risk = {
        row["ward"]: (float(row["R_final_CDEM"]), int(row["rank_CDEM"]))
        for _, row in df.iterrows()
    }
    ward_names = list(WARD_COORDS.keys())
    pts = np.array(list(WARD_COORDS.values()))
    clip = MultiPoint([Point(p) for p in pts]).convex_hull.buffer(0.014)

    far = 0.30
    mirrors = np.concatenate(
        [pts + [far, 0], pts - [far, 0], pts + [0, far], pts - [0, far]]
    )
    vor = Voronoi(np.vstack([pts, mirrors]))

    scores = [risk[w][0] for w in ward_names if w in risk]
    min_s, max_s = min(scores), max(scores)

    def score_color(score: float) -> list[int]:
        """Semi-transparent fill: cool blue (low risk) → warm red (high risk)."""
        t = max(0.0, min(1.0, (score - min_s) / (max_s - min_s)))
        r = int(59 + t * (239 - 59))
        g = int(130 + t * (68 - 130))
        b = int(246 + t * (68 - 246))
        alpha = int(90 + t * 80)
        return [r, g, b, alpha]

    features = []
    for i, name in enumerate(ward_names):
        region = vor.regions[vor.point_region[i]]
        if not region or -1 in region:
            continue
        poly = Polygon([vor.vertices[j] for j in region]).intersection(clip)
        if poly.is_empty:
            continue
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda p: p.area)

        score, rank = risk.get(name, (0.0, 0))
        features.append(
            {
                "polygon":    [[x, y] for x, y in poly.exterior.coords],
                "ward":       name,
                "score":      round(score, 2),
                "rank":       rank,
                "fill_color": score_color(score),
            }
        )
    return features


df = load_risk_data()
polygon_data = build_polygon_layer_data(df)

top1 = df.nlargest(1, "R_final_CDEM").iloc[0]
low1 = df.nsmallest(1, "R_final_CDEM").iloc[0]
avg_s = df["R_final_CDEM"].mean()
now_str = datetime.now().strftime("%b %d, %Y at %-I:%M %p")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                f"Welcome to the Newham Risk Dashboard. The highest-risk ward is "
                f"**{top1['ward']}** (Final Risk Score **{top1['R_final_CDEM']:.2f}**). "
                f"Ask me about any ward or risk factor."
            ),
        }
    ]


def analyst_reply(prompt: str) -> str:
    p = prompt.lower()
    for ward in df["ward"].tolist():
        if ward.lower() in p:
            r = df[df["ward"] == ward].iloc[0]
            return (
                f"**{ward}** — Final Risk Score **{r['R_final_CDEM']:.2f}** "
                f"(rank #{int(r['rank_CDEM'])}/24).  \n"
                f"IMD {r['imd_score']:,.0f} · Air quality {r['air_quality_combined']:.2f}."
            )
    if any(k in p for k in ["highest", "worst", "top", "most"]):
        return f"Highest risk: **{top1['ward']}** (score **{top1['R_final_CDEM']:.2f}**)."
    if any(k in p for k in ["lowest", "safest", "least"]):
        return f"Lowest risk: **{low1['ward']}** (score **{low1['R_final_CDEM']:.2f}**)."
    if any(k in p for k in ["average", "mean", "borough"]):
        return f"Borough average Final Risk Score: **{avg_s:.2f}**."
    return "Try asking about a specific ward, e.g. *'Tell me about Beckton'*."


# ── FULL-SCREEN MAP (PolygonLayer, light basemap) ─────────────────────────────
poly_layer = pdk.Layer(
    "PolygonLayer",
    data=polygon_data,
    get_polygon="polygon",
    get_fill_color="fill_color",
    get_line_color=[255, 255, 255],
    line_width_min_pixels=1,
    line_width_max_pixels=1,
    stroked=True,
    filled=True,
    extruded=False,
    pickable=True,
    auto_highlight=True,
    highlight_color=[255, 255, 255, 100],
)

tooltip = {
    "html": (
        "<div style='font-family:system-ui;font-size:13px;background:#fff;"
        "color:#1e1e1e;border:1px solid #e5e7eb;border-radius:8px;"
        "padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.08);'>"
        "<b>{ward}</b><br/>"
        "<span style='color:#6b7280;font-size:11px'>Rank #{rank}</span><br/>"
        "Final Risk Score: <b>{score}</b>"
        "</div>"
    ),
    "style": {"backgroundColor": "transparent"},
}

st.pydeck_chart(
    pdk.Deck(
        layers=[poly_layer],
        initial_view_state=pdk.ViewState(
            longitude=0.033,
            latitude=51.527,
            zoom=12.2,
            pitch=0,
            bearing=0,
        ),
        tooltip=tooltip,
        map_style="light",
    ),
    use_container_width=True,
    height=1200,
)

# ── TRUE FLOATING CONTAINER (right-side UI) ────────────────────────────────────
panel = st.container(key="float_panel")
with panel:
    st.markdown(
        f"""
<div style="padding:1.1rem 1.1rem 0.85rem;border-bottom:1px solid #e5e7eb;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <p style="font-size:0.68rem;color:#6b7280;margin:0;text-transform:uppercase;
                letter-spacing:0.05em;font-weight:600;">Newham Risk Dashboard</p>
      <p style="font-size:0.72rem;color:#9ca3af;margin:4px 0 0;">{now_str}</p>
    </div>
    <span style="font-size:1.1rem;color:#6b7280;cursor:pointer;line-height:1;">☰</span>
  </div>
</div>

<div style="padding:0.9rem 1.1rem;border-bottom:1px solid #e5e7eb;">
  <p style="font-size:0.68rem;color:#6b7280;margin:0 0 4px;text-transform:uppercase;
            letter-spacing:0.05em;font-weight:600;">Highest Risk Ward</p>
  <p style="font-size:1rem;font-weight:700;color:#1e1e1e;margin:0 0 8px;">{top1['ward']}</p>
  <div style="display:flex;gap:1.4rem;">
    <div>
      <p style="font-size:0.62rem;color:#9ca3af;margin:0;text-transform:uppercase;">Risk Score</p>
      <p style="font-size:0.95rem;font-weight:700;color:#1e1e1e;margin:2px 0 0;">{top1['R_final_CDEM']:.2f}</p>
    </div>
    <div>
      <p style="font-size:0.62rem;color:#9ca3af;margin:0;text-transform:uppercase;">Rank</p>
      <p style="font-size:0.95rem;font-weight:700;color:#1e1e1e;margin:2px 0 0;">#1 / 24</p>
    </div>
    <div>
      <p style="font-size:0.62rem;color:#9ca3af;margin:0;text-transform:uppercase;">Borough Avg</p>
      <p style="font-size:0.95rem;font-weight:700;color:#1e1e1e;margin:2px 0 0;">{avg_s:.2f}</p>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="panel-scroll">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Ask about this map…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": analyst_reply(prompt)})
        st.rerun()
