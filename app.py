import geopandas as gpd
import pandas as pd
import pydeck as pdk
import streamlit as st
from datetime import datetime

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

/* Scrollable chat history area (nested st.container(key="chat_log")) */
.st-key-chat_log {
    flex: 1 1 auto !important;
    overflow-y: auto !important;
    padding: 0 18px 4px 18px !important;
    min-height: 0 !important;
}
.st-key-chat_log::-webkit-scrollbar { width: 4px; }
.st-key-chat_log::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }

/* ━━ LEFT FLOATING LEGEND PANEL (targets st.container(key="legend_panel")) ━━ */
.st-key-legend_panel {
    position: fixed !important;
    left: 20px !important;
    top: 20px !important;
    width: 230px !important;
    background: #ffffff !important;
    z-index: 999999 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    border: 1px solid #e5e7eb !important;
    overflow: hidden !important;
    padding: 0 !important;
}
.st-key-legend_panel,
.st-key-legend_panel p,
.st-key-legend_panel span { color: #1e1e1e !important; }

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
/* Force the inner chat-input wrapper white (Streamlit's default is dark) */
.st-key-float_panel [data-testid="stChatInput"] > div,
.st-key-float_panel [data-testid="stChatInput"] [data-baseweb="textarea"],
.st-key-float_panel [data-testid="stChatInput"] [data-baseweb="base-input"] {
    background: #ffffff !important;
}
/* Send button — light mode */
.st-key-float_panel [data-testid="stChatInputSubmitButton"] {
    background: #f3f4f6 !important;
    color: #1e1e1e !important;
    border-radius: 8px !important;
}
.st-key-float_panel [data-testid="stChatInputSubmitButton"]:hover { background: #e5e7eb !important; }
.st-key-float_panel [data-testid="stChatInputSubmitButton"] svg { fill: #1e1e1e !important; color: #1e1e1e !important; }
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

SHAPEFILE_PATH = "data/Wards_December_2022_Boundaries_UK_BGC_5935341910977814913.geojson"
RISK_CSV_PATH = "data/newham_ward_risk_table_CDEM.csv"


@st.cache_data
def load_risk_data() -> pd.DataFrame:
    return pd.read_csv(RISK_CSV_PATH)


def _score_color(score: float, min_s: float, max_s: float) -> list[int]:
    """Semi-transparent teal fill: pale teal (low risk) → deep teal (high risk).

    Single-hue teal ramp keeps red/orange free for a future equity layer.
    """
    span = (max_s - min_s) or 1.0
    t = max(0.0, min(1.0, (score - min_s) / span))
    # #99f6e4 (pale teal) → #0f766e (deep teal)
    r = int(153 + t * (15 - 153))
    g = int(246 + t * (118 - 246))
    b = int(228 + t * (110 - 228))
    alpha = int(150 + t * 30)
    return [r, g, b, alpha]


def _geom_to_polygons(geom) -> list[list[list[float]]]:
    """Return a list of exterior rings ([[lon, lat], ...]) for Polygon/MultiPolygon."""
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [[[x, y] for x, y in geom.exterior.coords]]
    if geom.geom_type == "MultiPolygon":
        return [[[x, y] for x, y in part.exterior.coords] for part in geom.geoms]
    return []


@st.cache_data
def build_polygon_layer_data() -> tuple[list[dict], list[str], list[float]]:
    """
    Load the Dec 2022 UK wards boundaries, reproject EPSG:27700 -> EPSG:4326,
    filter to Newham (LAD22NM), merge with the CDEM risk CSV on ward name
    (WD22NM == ward), and emit flat PolygonLayer features coloured by
    Final Risk Score (R_final_CDEM).

    Returns (features, unmatched_csv_wards, [center_lon, center_lat]).
    """
    gdf = gpd.read_file(SHAPEFILE_PATH)
    # CRITICAL: UK national grid -> WGS84 GPS coords for Pydeck
    gdf = gdf.to_crs(epsg=4326)
    newham = gdf[gdf["LAD22NM"] == "Newham"].copy()

    df = load_risk_data()
    merged = newham.merge(df, left_on="WD22NM", right_on="ward", how="inner")

    min_s = float(df["R_final_CDEM"].min())
    max_s = float(df["R_final_CDEM"].max())

    features: list[dict] = []
    for _, row in merged.iterrows():
        score = float(row["R_final_CDEM"])
        rank = int(row["rank_CDEM"])
        color = _score_color(score, min_s, max_s)
        for ring in _geom_to_polygons(row.geometry):
            features.append(
                {
                    "polygon":    ring,
                    "ward":       row["ward"],
                    "score":      round(score, 2),
                    "rank":       rank,
                    "fill_color": color,
                }
            )

    matched = set(merged["ward"])
    unmatched = sorted(set(df["ward"]) - matched)

    if len(merged):
        center = merged.geometry.union_all().centroid
        center_ll = [float(center.x), float(center.y)]
    else:
        center_ll = [0.033, 51.527]

    return features, unmatched, center_ll


df = load_risk_data()
polygon_data, unmatched_wards, map_center = build_polygon_layer_data()

top1 = df.nlargest(1, "R_final_CDEM").iloc[0]
low1 = df.nsmallest(1, "R_final_CDEM").iloc[0]
avg_s = df["R_final_CDEM"].mean()
min_score = float(df["R_final_CDEM"].min())
max_score = float(df["R_final_CDEM"].max())
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
            longitude=map_center[0],
            latitude=map_center[1],
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

# ── LEFT FLOATING LEGEND PANEL ─────────────────────────────────────────────────
legend = st.container(key="legend_panel")
with legend:
    st.markdown(
        f"""
<div style="padding:0.9rem 1rem 1rem;">
  <p style="font-size:0.95rem;font-weight:700;color:#1e1e1e;margin:0 0 10px;">Legend</p>
  <p style="font-size:0.68rem;color:#6b7280;margin:0 0 6px;text-transform:uppercase;
            letter-spacing:0.05em;font-weight:600;">Final Risk Score (CDEM)</p>
  <div style="height:12px;border-radius:6px;
              background:linear-gradient(90deg,#99f6e4,#0f766e);margin:0 0 5px;"></div>
  <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#6b7280;">
    <span>{min_score:.1f}</span>
    <span>{max_score:.1f}</span>
  </div>
  <p style="font-size:0.68rem;color:#9ca3af;margin:10px 0 0;line-height:1.4;">
    Deeper teal = higher climate &amp; health risk.
  </p>
</div>
""",
        unsafe_allow_html=True,
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

    n_mapped = len(df) - len(unmatched_wards)
    if unmatched_wards:
        st.markdown(
            f"""
<div style="padding:0.55rem 1.1rem;background:#fffbeb;border-bottom:1px solid #fde68a;">
  <p style="font-size:0.68rem;color:#92400e;margin:0;line-height:1.4;">
    Showing {n_mapped} of {len(df)} wards as polygons. {len(unmatched_wards)} wards in the
    risk table have no boundary match in the 2018 shapefile
    (e.g. {', '.join(unmatched_wards[:3])}…).
  </p>
</div>
""",
            unsafe_allow_html=True,
        )

    with st.container(key="chat_log"):
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about this map…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": analyst_reply(prompt)})
        st.rerun()
