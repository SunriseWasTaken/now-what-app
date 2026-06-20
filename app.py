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
    max-height: calc(100vh - 40px) !important;
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

/* Panel hugs its content; inner wrapper stays a flex column without forcing height */
.st-key-float_panel > div {
    display: flex !important;
    flex-direction: column !important;
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
    flex: 0 1 auto !important;
    max-height: 45vh !important;
    overflow-y: auto !important;
    padding: 0 18px 4px 18px !important;
    min-height: 0 !important;
}
.st-key-chat_log::-webkit-scrollbar { width: 4px; }
.st-key-chat_log::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }

/* ━━ LEFT FLOATING LEGEND PANEL (targets st.container(key="legend_panel")) ━━ */
@keyframes legendIn {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: none; }
}
.st-key-legend_panel {
    position: fixed !important;
    left: 20px !important;
    top: 20px !important;
    width: 250px !important;
    background: rgba(255, 255, 255, 0.60) !important;
    backdrop-filter: blur(10px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(10px) saturate(140%) !important;
    z-index: 999999 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    border: 1px solid rgba(229, 231, 235, 0.8) !important;
    overflow: hidden !important;
    padding: 0 !important;
    animation: legendIn 0.22s ease-out !important;
}
.st-key-legend_panel,
.st-key-legend_panel p,
.st-key-legend_panel span { color: #1e1e1e !important; }
.st-key-legend_panel [data-testid="stHorizontalBlock"] { gap: 0.25rem !important; align-items: center !important; }

/* Legend title-bar icon buttons (share + close) */
.st-key-share_legend button,
.st-key-close_legend button {
    background: transparent !important;
    border: none !important;
    color: #6b7280 !important;
    padding: 7px 6px 3px !important;
    min-height: 0 !important;
    font-size: 1rem !important;
    line-height: 1 !important;
    box-shadow: none !important;
}
.st-key-share_legend button:hover,
.st-key-close_legend button:hover { color: #1e1e1e !important; background: rgba(0,0,0,0.05) !important; }

/* Layer segmented control — light mode */
.st-key-layer_select [data-baseweb="button-group"] { background: #f3f4f6 !important; border-radius: 8px !important; }
.st-key-layer_select button { color: #374151 !important; }

/* Reopen-legend toggle button (shown when legend closed) */
.st-key-open_legend {
    position: fixed !important;
    left: 20px !important;
    top: 20px !important;
    z-index: 999999 !important;
    animation: legendIn 0.22s ease-out !important;
}
.st-key-open_legend button {
    background: rgba(255,255,255,0.9) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #1e1e1e !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

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


def _normalize(s: pd.Series) -> pd.Series:
    """Min–max scale a Series to [0, 1] (flat → all zeros)."""
    rng = float(s.max() - s.min())
    if rng == 0:
        return s * 0.0
    return (s - s.min()) / rng


@st.cache_data
def load_risk_data() -> pd.DataFrame:
    df = pd.read_csv(RISK_CSV_PATH)
    # ── Continuous "Equity Severity" ──────────────────────────────────────────
    # The PRD defines the equity gap as the COLLISION of high deprivation (D)
    # and low mental-health service capacity. In this table M is the inverse
    # capacity term (higher M = fewer services per capita), so a ward is severe
    # only when BOTH D and M are high. A product captures that collision and
    # gives a continuous number that actually supports a gradient.
    dep = _normalize(df["D"])   # 0 = least deprived → 1 = most deprived
    cap = _normalize(df["M"])   # 0 = most capacity  → 1 = least capacity
    df["equity_severity"] = _normalize(dep * cap)
    return df


# ── Layer config ───────────────────────────────────────────────────────────────
# Risk: continuous R_final, teal ramp. Equity: continuous severity, amber→red ramp.
TEAL_LOW = (153, 246, 228)   # #99f6e4
TEAL_HIGH = (15, 118, 110)   # #0f766e
EQUITY_LOW = (254, 215, 170)  # #fed7aa  pale amber  (low equity gap)
EQUITY_HIGH = (153, 27, 27)   # #991b1b  deep red    (severe equity gap)


def _ramp_color(score: float, min_s: float, max_s: float,
                low: tuple, high: tuple, a_lo: int = 150, a_hi: int = 190) -> list[int]:
    """Semi-transparent fill interpolated between two RGB endpoints."""
    span = (max_s - min_s) or 1.0
    t = max(0.0, min(1.0, (score - min_s) / span))
    r = int(low[0] + t * (high[0] - low[0]))
    g = int(low[1] + t * (high[1] - low[1]))
    b = int(low[2] + t * (high[2] - low[2]))
    alpha = int(a_lo + t * (a_hi - a_lo))
    return [r, g, b, alpha]


def _teal_color(score: float, min_s: float, max_s: float) -> list[int]:
    return _ramp_color(score, min_s, max_s, TEAL_LOW, TEAL_HIGH, 150, 180)


def _equity_color(score: float, min_s: float, max_s: float) -> list[int]:
    return _ramp_color(score, min_s, max_s, EQUITY_LOW, EQUITY_HIGH, 150, 195)


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
def load_ward_geometry() -> tuple[list[dict], list[dict], list[float]]:
    """
    Load the Dec 2022 UK wards boundaries once, reproject EPSG:27700 -> EPSG:4326,
    filter to Newham (LAD22NM), merge with the risk CSV (WD22NM == ward), and
    return per-ring records plus one centroid per ward so the active layer can be
    coloured (and the equity pins placed) without re-reading the geometry.

    Returns (records, centroids, [center_lon, center_lat]).
    """
    gdf = gpd.read_file(SHAPEFILE_PATH)
    # CRITICAL: UK national grid -> WGS84 GPS coords for Pydeck
    gdf = gdf.to_crs(epsg=4326)
    newham = gdf[gdf["LAD22NM"] == "Newham"].copy()

    df_local = load_risk_data()
    merged = newham.merge(df_local, left_on="WD22NM", right_on="ward", how="inner")

    records: list[dict] = []
    centroids: list[dict] = []
    for _, row in merged.iterrows():
        for ring in _geom_to_polygons(row.geometry):
            records.append(
                {
                    "polygon":          ring,
                    "ward":             row["ward"],
                    "r_final":          float(row["R_final"]),
                    "equity_flag":      bool(row["equity_flag"]),
                    "equity_severity":  float(row["equity_severity"]),
                }
            )
        c = row.geometry.centroid
        centroids.append(
            {
                "ward":             row["ward"],
                "lon":              float(c.x),
                "lat":              float(c.y),
                "equity_severity":  float(row["equity_severity"]),
            }
        )

    if len(merged):
        center = merged.geometry.union_all().centroid
        center_ll = [float(center.x), float(center.y)]
    else:
        center_ll = [0.033, 51.527]

    return records, centroids, center_ll


def build_pins(centroids: list[dict], esev_min: float, esev_max: float) -> list[dict]:
    """Red/orange equity pins at ward centroids; radius + colour scale with the
    continuous equity-severity score."""
    span = (esev_max - esev_min) or 1.0
    pins: list[dict] = []
    for c in centroids:
        sev = c["equity_severity"]
        t = max(0.0, min(1.0, (sev - esev_min) / span))
        pins.append(
            {
                "position":   [c["lon"], c["lat"]],
                "ward":       c["ward"],
                "value":      f"Equity severity: {sev:.2f}",
                "fill_color": _equity_color(sev, esev_min, esev_max),
                "radius":     120 + t * 480,  # metres
            }
        )
    return pins


def build_features(records: list[dict], layer: str, rfin_min: float, rfin_max: float,
                   esev_min: float, esev_max: float) -> list[dict]:
    """Colour each ward ring for the active layer (cheap; runs every rerun)."""
    features: list[dict] = []
    for rec in records:
        if layer == "Equity":
            sev = rec["equity_severity"]
            color = _equity_color(sev, esev_min, esev_max)
            value = f"Equity severity: {sev:.2f}"
        elif layer == "Both":
            # Polygons stay teal (risk); equity rides on the pin overlay.
            color = _teal_color(rec["r_final"], rfin_min, rfin_max)
            value = f"Risk {rec['r_final']:.2f}"
        else:  # Risk
            color = _teal_color(rec["r_final"], rfin_min, rfin_max)
            value = f"Final Risk Score: {rec['r_final']:.2f}"
        features.append(
            {
                "polygon":    rec["polygon"],
                "ward":       rec["ward"],
                "value":      value,
                "fill_color": color,
            }
        )
    return features


df = load_risk_data()
ward_records, ward_centroids, map_center = load_ward_geometry()

# Active layer (widget below writes to this key; read with a default for first run)
active_layer = st.session_state.get("layer_select", "Risk")

rfin_min = float(df["R_final"].min())
rfin_max = float(df["R_final"].max())
esev_min = float(df["equity_severity"].min())
esev_max = float(df["equity_severity"].max())
polygon_data = build_features(
    ward_records, active_layer, rfin_min, rfin_max, esev_min, esev_max
)
pin_data = build_pins(ward_centroids, esev_min, esev_max)

top1 = df.nlargest(1, "R_final").iloc[0]
low1 = df.nsmallest(1, "R_final").iloc[0]
avg_s = df["R_final"].mean()
now_str = datetime.now().strftime("%b %d, %Y at %-I:%M %p")

# Legend open/closed state
if "legend_open" not in st.session_state:
    st.session_state.legend_open = True

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                f"Welcome to the Newham Risk Dashboard. The highest-risk ward is "
                f"**{top1['ward']}** (Final Risk Score **{top1['R_final']:.2f}**). "
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
                f"**{ward}** — Final Risk Score **{r['R_final']:.2f}** "
                f"(rank #{int(r['rank_CDEM'])}/24).  \n"
                f"IMD {r['imd_score']:,.0f} · Air quality {r['air_quality_combined']:.2f} · "
                f"Equity flagged: {'Yes' if r['equity_flag'] else 'No'}."
            )
    if any(k in p for k in ["highest", "worst", "top", "most"]):
        return f"Highest risk: **{top1['ward']}** (score **{top1['R_final']:.2f}**)."
    if any(k in p for k in ["lowest", "safest", "least"]):
        return f"Lowest risk: **{low1['ward']}** (score **{low1['R_final']:.2f}**)."
    if any(k in p for k in ["equity", "flag", "deprivation", "capacity"]):
        top_eq = df.nlargest(3, "equity_severity")["ward"].tolist()
        return (
            "Equity severity = collision of high deprivation (D) and low service "
            f"capacity (M). Most severe gaps: **{', '.join(top_eq)}**."
        )
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

pin_layer = pdk.Layer(
    "ScatterplotLayer",
    data=pin_data,
    get_position="position",
    get_radius="radius",
    get_fill_color="fill_color",
    radius_min_pixels=5,
    radius_max_pixels=42,
    stroked=True,
    get_line_color=[255, 255, 255],
    line_width_min_pixels=1,
    pickable=True,
)

map_layers = [poly_layer]
if active_layer == "Both":
    map_layers.append(pin_layer)

tooltip = {
    "html": (
        "<div style='font-family:system-ui;font-size:13px;background:#fff;"
        "color:#1e1e1e;border:1px solid #e5e7eb;border-radius:8px;"
        "padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.08);'>"
        "<b>{ward}</b><br/>"
        "<span style='color:#374151'>{value}</span>"
        "</div>"
    ),
    "style": {"backgroundColor": "transparent"},
}

st.pydeck_chart(
    pdk.Deck(
        layers=map_layers,
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

# ── LEFT FLOATING LEGEND PANEL (or reopen toggle) ─────────────────────────────
def _render_legend_body(layer: str) -> None:
    if layer == "Both":
        st.markdown(
            f"""
<div style="padding:0.2rem 0.9rem 0.9rem;">
  <p style="font-size:0.68rem;color:#6b7280;margin:0 0 6px;text-transform:uppercase;
            letter-spacing:0.05em;font-weight:600;">Risk (fill)</p>
  <div style="height:10px;border-radius:5px;
              background:linear-gradient(90deg,#99f6e4,#0f766e);margin:0 0 4px;"></div>
  <div style="display:flex;justify-content:space-between;font-size:0.68rem;color:#6b7280;margin:0 0 12px;">
    <span>{rfin_min:.1f}</span>
    <span>{rfin_max:.1f}</span>
  </div>
  <p style="font-size:0.68rem;color:#6b7280;margin:0 0 6px;text-transform:uppercase;
            letter-spacing:0.05em;font-weight:600;">Equity gap (pins)</p>
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="width:9px;height:9px;border-radius:50%;background:#fed7aa;
                 border:1px solid #fff;display:inline-block;flex-shrink:0;"></span>
    <span style="width:15px;height:15px;border-radius:50%;background:#991b1b;
                 border:1px solid #fff;display:inline-block;flex-shrink:0;"></span>
    <span style="font-size:0.72rem;color:#374151;">smaller/pale to larger/red</span>
  </div>
  <p style="font-size:0.68rem;color:#9ca3af;margin:10px 0 0;line-height:1.4;">
    Teal wards show risk; red pins mark the equity gap (size + colour = severity).
  </p>
</div>
""",
            unsafe_allow_html=True,
        )
    elif layer == "Equity":
        st.markdown(
            """
<div style="padding:0.2rem 0.9rem 0.9rem;">
  <p style="font-size:0.68rem;color:#6b7280;margin:0 0 6px;text-transform:uppercase;
            letter-spacing:0.05em;font-weight:600;">Equity Severity</p>
  <div style="height:12px;border-radius:6px;
              background:linear-gradient(90deg,#fed7aa,#991b1b);margin:0 0 5px;"></div>
  <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#6b7280;">
    <span>Lower</span>
    <span>Higher</span>
  </div>
  <p style="font-size:0.68rem;color:#9ca3af;margin:10px 0 0;line-height:1.4;">
    Deeper red = collision of high deprivation (D) and low service capacity (M).
  </p>
</div>
""",
            unsafe_allow_html=True,
        )
    else:  # Risk
        st.markdown(
            f"""
<div style="padding:0.2rem 0.9rem 0.9rem;">
  <p style="font-size:0.68rem;color:#6b7280;margin:0 0 6px;text-transform:uppercase;
            letter-spacing:0.05em;font-weight:600;">Final Risk Score</p>
  <div style="height:12px;border-radius:6px;
              background:linear-gradient(90deg,#99f6e4,#0f766e);margin:0 0 5px;"></div>
  <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#6b7280;">
    <span>{rfin_min:.1f}</span>
    <span>{rfin_max:.1f}</span>
  </div>
  <p style="font-size:0.68rem;color:#9ca3af;margin:10px 0 0;line-height:1.4;">
    Deeper teal = higher climate &amp; health risk.
  </p>
</div>
""",
            unsafe_allow_html=True,
        )


if st.session_state.legend_open:
    legend = st.container(key="legend_panel")
    with legend:
        bar_title, bar_share, bar_close = st.columns([6, 1, 1])
        with bar_title:
            st.markdown(
                "<p style='font-size:0.95rem;font-weight:700;color:#1e1e1e;"
                "margin:0;padding:6px 0 0 4px;'>Legend</p>",
                unsafe_allow_html=True,
            )
        with bar_share:
            if st.button(":material/ios_share:", key="share_legend", help="Share this dashboard"):
                st.toast("Dashboard link copied to clipboard.")
        with bar_close:
            if st.button("✕", key="close_legend", help="Hide legend"):
                st.session_state.legend_open = False
                st.rerun()

        st.segmented_control(
            "Layer",
            options=["Risk", "Equity", "Both"],
            default="Risk",
            key="layer_select",
            label_visibility="collapsed",
        )
        _render_legend_body(active_layer)
else:
    if st.button("☰  Legend", key="open_legend"):
        st.session_state.legend_open = True
        st.rerun()

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
      <p style="font-size:0.95rem;font-weight:700;color:#1e1e1e;margin:2px 0 0;">{top1['R_final']:.2f}</p>
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

    with st.container(key="chat_log"):
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about this map…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": analyst_reply(prompt)})
        st.rerun()
