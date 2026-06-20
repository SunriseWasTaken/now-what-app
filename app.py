import geopandas as gpd
import pandas as pd
import pydeck as pdk
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="London Climate & Health Risk Dashboard",
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

/* ── Split view: two half-screen maps side by side ── */
.st-key-map_left [data-testid="stDeckGlJsonChart"] { left: 0 !important; width: 50vw !important; }
.st-key-map_left [data-testid="stDeckGlJsonChart"] iframe { width: 50vw !important; }
.st-key-map_right [data-testid="stDeckGlJsonChart"] { left: 50vw !important; width: 50vw !important; }
.st-key-map_right [data-testid="stDeckGlJsonChart"] iframe { width: 50vw !important; }
.split-divider {
    position: fixed; top: 0; left: 50vw; width: 3px; height: 100vh;
    background: #ffffff; box-shadow: 0 0 8px rgba(0,0,0,0.15);
    z-index: 3; transform: translateX(-1.5px);
}
.split-label {
    position: fixed; top: 18px; z-index: 5;
    background: rgba(255,255,255,0.94); border: 1px solid #e5e7eb; border-radius: 8px;
    padding: 6px 16px; font-size: 0.8rem; font-weight: 700; color: #1e1e1e;
    text-transform: uppercase; letter-spacing: 0.04em;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.split-label-left  { left: 25vw; transform: translateX(-50%); }
.split-label-right { left: 75vw; transform: translateX(-50%); }

/* ━━ TRUE FLOATING CONTAINER (targets st.container(key="float_panel")) ━━ */
.st-key-float_panel {
    position: fixed !important;
    right: 20px !important;
    top: 20px !important;
    height: 80vh !important;
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
    transition: opacity 0.3s ease, transform 0.3s ease !important;
}

/* Inner wrapper fills the panel as a flex column */
.st-key-float_panel > div {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    min-height: 0 !important;
    overflow: hidden !important;
}

/* Dark text inside panel (light mode) */
.st-key-float_panel,
.st-key-float_panel p,
.st-key-float_panel span,
.st-key-float_panel li,
.st-key-float_panel label { color: #1e1e1e !important; }

/* ━━ LEADERBOARD (right panel) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
/* Keep the header block at its natural height; only the leaderboard list grows. */
.st-key-float_panel > div:has(> .st-key-panel_header) { flex: 0 0 auto !important; }
/* Let the leaderboard markdown element fill the panel below the header so its
   internal list scrolls instead of the whole panel. */
.st-key-float_panel > div > [data-testid="stElementContainer"]:last-child {
    flex: 1 1 auto !important;
    min-height: 0 !important;
    display: flex !important;
    flex-direction: column !important;
}
.st-key-float_panel > div > [data-testid="stElementContainer"]:last-child [data-testid="stMarkdown"],
.st-key-float_panel > div > [data-testid="stElementContainer"]:last-child [data-testid="stMarkdown"] > div {
    flex: 1 1 auto !important;
    min-height: 0 !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Scroll container — scrollbar pinned to the LEFT via rtl, content stays ltr.
   Explicit max-height (panel is 80vh, header ≈ 64px) guarantees the list
   overflows and shows a scrollbar regardless of the flex chain. */
.lb-scroll {
    flex: 1 1 auto !important;
    min-height: 0 !important;
    max-height: calc(80vh - 64px) !important;
    overflow-y: auto !important;
    direction: rtl !important;
}
.lb-inner { direction: ltr !important; padding: 12px 14px 14px 14px !important; }
.lb-scroll::-webkit-scrollbar { width: 8px; }
.lb-scroll::-webkit-scrollbar-track { background: #f1f3f5; border-radius: 4px; }
.lb-scroll::-webkit-scrollbar-thumb { background: #6b7280; border-radius: 4px; }
.lb-scroll::-webkit-scrollbar-thumb:hover { background: #374151; }
.lb-scroll { scrollbar-color: #6b7280 #f1f3f5; scrollbar-width: thin; }

/* Featured #1 card — larger, emphasised */
.lb-feature {
    background: #f9fafb;
    border: 1px solid #eceef1;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 14px;
}
.lb-feat-top { display: flex; align-items: baseline; gap: 10px; }
.lb-feat-rank { font-size: 1.5rem; font-weight: 800; color: #0f766e; line-height: 1; }
.lb-eyebrow {
    font-size: 0.62rem; color: #6b7280; text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 700;
}
.lb-feat-ward { font-size: 1.35rem; font-weight: 800; color: #1e1e1e; margin: 8px 0 12px; line-height: 1.1; }
.lb-feat-stats { display: flex; gap: 2rem; }
.lb-stat-label { font-size: 0.6rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; margin: 0; }
.lb-feat-score { font-size: 1.1rem; font-weight: 800; color: #1e1e1e; margin: 2px 0 0; }

.lb-section {
    font-size: 0.62rem; color: #9ca3af; text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 700; margin: 0 2px 8px; 
}

/* Compact, equally-sized ranking rows */
.lb-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 10px;
    border-radius: 8px;
    margin-bottom: 4px;
    background: #ffffff;
    border: 1px solid #f1f3f5;
}
.lb-row:hover { background: #f9fafb; }
.lb-row-rank { font-size: 0.8rem; font-weight: 700; color: #9ca3af; width: 30px; flex: 0 0 auto; }
.lb-row-ward { font-size: 0.85rem; font-weight: 600; color: #1e1e1e; flex: 1 1 auto;
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lb-row-bar { width: 6px; height: 18px; border-radius: 3px; flex: 0 0 auto; }
.lb-row-score { font-size: 0.85rem; font-weight: 700; color: #1e1e1e; width: 42px; text-align: right; flex: 0 0 auto; }

/* ━━ LEFT FLOATING LEGEND PANEL (targets st.container(key="legend_panel")) ━━ */
@keyframes legendIn {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: none; }
}
.st-key-legend_panel {
    position: fixed !important;
    left: 20px !important;
    top: 20px !important;
    height: 75vh !important;
    width: 250px !important;
    background: rgba(255, 255, 255, 0.60) !important;
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

/* Borough selector inside the legend */
.st-key-borough_select { padding: 2px 12px 6px 12px !important; }
.st-key-borough_select label p {
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-weight: 600 !important;
    color: #6b7280 !important;
}
.st-key-borough_select [data-baseweb="select"] > div {
    background: #ffffff !important;
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
    color: #1e1e1e !important;
}

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

/* Layer segmented control — light mode (fix blacked-out unselected options) */
.st-key-layer_select [data-testid="stButtonGroup"],
.st-key-layer_select [data-baseweb="button-group"] {
    background: #f3f4f6 !important;
    border-radius: 8px !important;
    padding: 3px !important;
    gap: 2px !important;
}
/* Unselected options: transparent on the light track, dark readable text */
.st-key-layer_select button[data-testid="stBaseButton-segmented_control"] {
    background: transparent !important;
    color: #374151 !important;
    border: none !important;
    box-shadow: none !important;
}
.st-key-layer_select button[data-testid="stBaseButton-segmented_control"] p {
    color: #374151 !important;
}
/* Selected option: white pill */
.st-key-layer_select button[data-testid="stBaseButton-segmented_controlActive"] {
    background: #ffffff !important;
    color: #0f172a !important;
    border: none !important;
    border-radius: 6px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12) !important;
}
.st-key-layer_select button[data-testid="stBaseButton-segmented_controlActive"] p {
    color: #0f172a !important;
}

/* Reopen-legend toggle button (shown when legend closed) */
.st-key-open_legend {
    position: fixed !important;
    left: 20px !important;
    top: 20px !important;
    z-index: 999999 !important;
    animation: legendIn 0.22s ease-out !important;
}
.st-key-open_legend button {
    background: rgba(255,255,255,0.95) !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #1e1e1e !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

/* Reopen-panel toggle (shown when the whole right overlay is hidden) */
.st-key-open_panel {
    position: fixed !important;
    right: 20px !important;
    top: 20px !important;
    z-index: 999999 !important;
    animation: legendIn 0.22s ease-out !important;
}
.st-key-open_panel button {
    background: rgba(255,255,255,0.95) !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #1e1e1e !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    font-size: 1.0rem !important;
    font-weight: 600 !important;
    padding: 6px 12px !important;
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

/* Trim the default gap between panel sections to kill dead space */
.st-key-float_panel [data-testid="stVerticalBlock"] { gap: 0.35rem !important; }

/* Panel header row (title + functional menu button) */
.st-key-panel_header {
    padding: 0.8rem 1.1rem 0.55rem 1.1rem !important;
    border-bottom: 1px solid #e5e7eb !important;
}
.st-key-panel_header [data-testid="stHorizontalBlock"] { gap: 0 !important; align-items: center !important; min-height: 0 !important; }
.st-key-panel_header [data-testid="stColumn"] { min-height: 0 !important; }
.st-key-panel_header [data-testid="stColumn"]:last-child { display: flex !important; justify-content: flex-end !important; }
.st-key-panel_header [data-testid="stElementContainer"],
.st-key-panel_header [data-testid="stMarkdown"] { margin: 0 !important; }
.st-key-toggle_chat button {
    background: transparent !important;
    border: none !important;
    color: #6b7280 !important;
    padding: 2px 6px !important;
    min-height: 0 !important;
    font-size: 1.15rem !important;
    line-height: 1 !important;
    box-shadow: none !important;
}
.st-key-toggle_chat button:hover { color: #1e1e1e !important; background: rgba(0,0,0,0.05) !important; }

/* Chat input — light mode; send button rides at the right end of the pill */
.st-key-float_panel [data-testid="stChatInput"] {
    position: relative !important;
    bottom: auto !important;
    flex-shrink: 0 !important;
    padding: 0.6rem 1rem !important;
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
.st-key-float_panel [data-testid="stChatInput"] textarea {
    background: #f9fafb !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 22px !important;
    color: #1e1e1e !important;
    font-size: 0.85rem !important;
    padding: 0.55rem 3rem 0.55rem 1rem !important;  /* right room for the button */
}
.st-key-float_panel [data-testid="stChatInput"] textarea:focus {
    border-color: #9ca3af !important;
    box-shadow: 0 0 0 2px rgba(156, 163, 175, 0.2) !important;
    outline: none !important;
}
.st-key-float_panel [data-testid="stChatInput"] textarea::placeholder { color: #9ca3af !important; }
/* Send button — round, vertically centered at the right end of the input pill */
.st-key-float_panel [data-testid="stChatInputSubmitButton"] {
    position: absolute !important;
    right: 1.5rem !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 30px !important;
    height: 30px !important;
    min-height: 30px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #f3f4f6 !important;
    color: #1e1e1e !important;
    border-radius: 50% !important;
    z-index: 2 !important;
}
.st-key-float_panel [data-testid="stChatInputSubmitButton"]:hover { background: #e5e7eb !important; }
.st-key-float_panel [data-testid="stChatInputSubmitButton"] svg { fill: #1e1e1e !important; color: #1e1e1e !important; }

/* Suppress Streamlit's global bottom chat dock */
[data-testid="stBottomBlockContainer"] { display: none !important; }
</style>
""",
    unsafe_allow_html=True,
)

SHAPEFILE_PATH = "data/Wards_December_2022_Boundaries_UK_BGC_5935341910977814913.geojson"

# ── Borough config — each entry drives the risk CSV, the shapefile (LAD22NM)
# filter, and the default map view used when that borough is selected. ─────────
BOROUGHS: dict[str, dict] = {
    "Newham": {
        "csv": "data/newham_ward_risk_table_CDEM.csv",
        "lad_match": "Newham",             # matched against LAD22NM (contains)
        "fallback_center": [0.033, 51.527],
        "zoom": 12.2,
    },
    "Kensington & Chelsea": {
        "csv": "data/kc_ward_risk_table_FINAL.csv",
        "lad_match": "Kensington",         # "Kensington and Chelsea"
        "fallback_center": [-0.195, 51.500],
        "zoom": 12.6,
    },
}
DEFAULT_BOROUGH = "Newham"


def _normalize(s: pd.Series) -> pd.Series:
    """Min–max scale a Series to [0, 1] (flat → all zeros)."""
    rng = float(s.max() - s.min())
    if rng == 0:
        return s * 0.0
    return (s - s.min()) / rng


@st.cache_data
def load_risk_data(borough: str) -> pd.DataFrame:
    df = pd.read_csv(BOROUGHS[borough]["csv"])
    # Borough tables differ slightly in their columns; alias the ones the rest
    # of the app reads so everything downstream stays borough-agnostic.
    if "imd_score" not in df.columns and "imd_score_proxy" in df.columns:
        df["imd_score"] = df["imd_score_proxy"]
    if "rank_CDEM" not in df.columns and "rank" in df.columns:
        df["rank_CDEM"] = df["rank"]
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


def _blend_color(risk: float, eqt: float, rmin: float, rmax: float,
                 emin: float, emax: float) -> list[int]:
    """Bivariate blend: teal encodes risk, then the colour is pulled toward deep
    red as equity severity rises. A ward that is both high-risk and high-gap
    reads as a dark, saturated red-teal mix."""
    base = _teal_color(risk, rmin, rmax)
    span = (emax - emin) or 1.0
    t = max(0.0, min(1.0, (eqt - emin) / span))
    r = int(base[0] + t * (EQUITY_HIGH[0] - base[0]))
    g = int(base[1] + t * (EQUITY_HIGH[1] - base[1]))
    b = int(base[2] + t * (EQUITY_HIGH[2] - base[2]))
    alpha = int(base[3] + t * (205 - base[3]))
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
def load_ward_geometry(borough: str) -> tuple[list[dict], list[float]]:
    """
    Load the Dec 2022 UK wards boundaries once, reproject EPSG:27700 -> EPSG:4326,
    filter to the selected borough (LAD22NM), merge with that borough's risk CSV
    (WD22NM == ward), and return per-ring records carrying R_final and equity
    values so the active layer can be coloured without re-reading the geometry.

    Returns (records, [center_lon, center_lat]).
    """
    cfg = BOROUGHS[borough]
    gdf = gpd.read_file(SHAPEFILE_PATH)
    # CRITICAL: UK national grid -> WGS84 GPS coords for Pydeck
    gdf = gdf.to_crs(epsg=4326)
    sel = gdf[gdf["LAD22NM"].str.contains(cfg["lad_match"], case=False, na=False)].copy()

    df_local = load_risk_data(borough)
    merged = sel.merge(df_local, left_on="WD22NM", right_on="ward", how="inner")

    records: list[dict] = []
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

    if len(merged):
        center = merged.geometry.union_all().centroid
        center_ll = [float(center.x), float(center.y)]
    else:
        center_ll = cfg["fallback_center"]

    return records, center_ll


def build_leaderboard_html(df: pd.DataFrame, layer: str,
                           rfin_min: float, rfin_max: float,
                           esev_min: float, esev_max: float) -> str:
    """Full ranking leaderboard for the active layer: a large featured #1 card
    followed by compact, equally-sized rows for the rest. Scrolls on its own."""
    if layer == "Equity":
        metric, unit_label = "equity_severity", "Equity Severity"
        mn, mx = esev_min, esev_max
        ramp = _equity_color
    else:  # Risk and Both rank by Final Risk Score
        metric, unit_label = "R_final", "Risk Score"
        mn, mx = rfin_min, rfin_max
        ramp = _teal_color

    ranked = df.sort_values(metric, ascending=False).reset_index(drop=True)
    total = len(ranked)

    def _rgb(score: float) -> str:
        c = ramp(float(score), mn, mx)
        return f"rgb({c[0]},{c[1]},{c[2]})"

    top = ranked.iloc[0]
    top_accent = _rgb(top[metric])
    feature = f"""
<div class="lb-feature" style="border-left:5px solid {top_accent};">
  <div class="lb-feat-top">
    <span class="lb-feat-rank">#1</span>
    <span class="lb-eyebrow">Highest {unit_label}</span>
  </div>
  <p class="lb-feat-ward">{top['ward']}</p>
  <div class="lb-feat-stats">
    <div><p class="lb-stat-label">{unit_label}</p>
         <p class="lb-feat-score">{top[metric]:.2f}</p></div>
    <div><p class="lb-stat-label">Rank</p>
         <p class="lb-feat-score">#1 / {total}</p></div>
  </div>
</div>
"""

    rows = []
    for i in range(1, total):
        r = ranked.iloc[i]
        accent = _rgb(r[metric])
        rows.append(f"""
<div class="lb-row">
  <span class="lb-row-rank">#{i + 1}</span>
  <span class="lb-row-ward">{r['ward']}</span>
  <span class="lb-row-bar" style="background:{accent};"></span>
  <span class="lb-row-score">{r[metric]:.2f}</span>
</div>
""")

    return (
        '<div class="lb-scroll"><div class="lb-inner">'
        + feature
        + '<p class="lb-section">Full Ranking</p>'
        + "".join(rows)
        + "</div></div>"
    )


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
            color = _blend_color(
                rec["r_final"], rec["equity_severity"],
                rfin_min, rfin_max, esev_min, esev_max,
            )
            value = f"Risk {rec['r_final']:.2f} · Equity {rec['equity_severity']:.2f}"
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


# Selected borough (the selectbox in the legend writes to this key; read with a
# default so the very first run before the widget mounts still works).
selected_borough = st.session_state.get("borough_select", DEFAULT_BOROUGH)
df = load_risk_data(selected_borough)

# Active layer (widget below writes to this key; read with a default for first run)
active_layer = st.session_state.get("layer_select", "Risk")

rfin_min = float(df["R_final"].min())
rfin_max = float(df["R_final"].max())
esev_min = float(df["equity_severity"].min())
esev_max = float(df["equity_severity"].max())

now_str = datetime.now().strftime("%b %d, %Y at %-I:%M %p")

# Legend open/closed state
if "legend_open" not in st.session_state:
    st.session_state.legend_open = True

# Right overlay show/hide state (toggled by the panel header menu button)
if "panel_open" not in st.session_state:
    st.session_state.panel_open = True

# ── MAP (PolygonLayer, light basemap) ─────────────────────────────────────────
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


def make_deck(borough: str, layer: str) -> pdk.Deck:
    """Build a self-contained deck for a borough so the same renderer powers both
    the single full-screen map and each half of the split view."""
    bdf = load_risk_data(borough)
    brecords, bcenter = load_ward_geometry(borough)
    rmin, rmax = float(bdf["R_final"].min()), float(bdf["R_final"].max())
    emin, emax = float(bdf["equity_severity"].min()), float(bdf["equity_severity"].max())
    feats = build_features(brecords, layer, rmin, rmax, emin, emax)
    poly = pdk.Layer(
        "PolygonLayer",
        data=feats,
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
    return pdk.Deck(
        layers=[poly],
        initial_view_state=pdk.ViewState(
            longitude=bcenter[0],
            latitude=bcenter[1],
            zoom=BOROUGHS[borough]["zoom"],
            pitch=0,
            bearing=0,
        ),
        tooltip=tooltip,
        map_style="light",
    )


split_view = st.session_state.get("split_view", False)

if split_view:
    with st.container(key="map_left"):
        st.pydeck_chart(
            make_deck("Newham", active_layer),
            use_container_width=True, height=1200, key="deck_left",
        )
    with st.container(key="map_right"):
        st.pydeck_chart(
            make_deck("Kensington & Chelsea", active_layer),
            use_container_width=True, height=1200, key="deck_right",
        )
    st.markdown(
        '<div class="split-label split-label-left">Newham</div>'
        '<div class="split-label split-label-right">Kensington &amp; Chelsea</div>'
        '<div class="split-divider"></div>',
        unsafe_allow_html=True,
    )
else:
    st.pydeck_chart(
        make_deck(selected_borough, active_layer),
        use_container_width=True,
        height=1200,
        # Re-key per borough so the deck remounts and re-applies the centred view
        # when the borough toggle changes (initial_view_state only binds on mount).
        key=f"deck_{selected_borough}",
    )

# ── LEFT FLOATING LEGEND PANEL (or reopen toggle) ─────────────────────────────
def _render_legend_body(layer: str) -> None:
    if layer == "Both":
        st.markdown(
            f"""
<div style="padding:0.2rem 0.9rem 0.9rem;">
  <p style="font-size:0.68rem;color:#6b7280;margin:0 0 6px;text-transform:uppercase;
            letter-spacing:0.05em;font-weight:600;">Risk (teal)</p>
  <div style="height:10px;border-radius:5px;
              background:linear-gradient(90deg,#99f6e4,#0f766e);margin:0 0 4px;"></div>
  <div style="display:flex;justify-content:space-between;font-size:0.68rem;color:#6b7280;margin:0 0 12px;">
    <span>{rfin_min:.1f}</span>
    <span>{rfin_max:.1f}</span>
  </div>
  <p style="font-size:0.68rem;color:#6b7280;margin:0 0 6px;text-transform:uppercase;
            letter-spacing:0.05em;font-weight:600;">Equity gap (red)</p>
  <div style="height:10px;border-radius:5px;
              background:linear-gradient(90deg,#fed7aa,#991b1b);margin:0 0 4px;"></div>
  <div style="display:flex;justify-content:space-between;font-size:0.68rem;color:#6b7280;">
    <span>Lower</span>
    <span>Higher</span>
  </div>
  <p style="font-size:0.68rem;color:#9ca3af;margin:10px 0 0;line-height:1.4;">
    Bivariate blend: teal = risk, shifting to red where the equity gap is severe.
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

        st.selectbox(
            "Select Borough",
            options=list(BOROUGHS.keys()),
            key="borough_select",
            disabled=split_view,
            help="Disabled in split view (both boroughs are shown)." if split_view else None,
        )

        st.toggle("Split view · Newham vs K&C", key="split_view")

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
# Hidden in split view so it doesn't cover the right-hand (K&C) map.
if not split_view:
  panel = st.container(key="float_panel")
  with panel:
    with st.container(key="panel_header"):
        head_l, head_r = st.columns([6, 1])
        with head_l:
            st.markdown(
                f"""
<p style="font-size:0.68rem;color:#6b7280;margin:0;text-transform:uppercase;
          letter-spacing:0.05em;font-weight:600;">{selected_borough} Risk Dashboard</p>
<p style="font-size:0.72rem;color:#9ca3af;margin:4px 0 0;">{now_str}</p>
""",
                unsafe_allow_html=True,
            )
        with head_r:
            if st.button("☰", key="toggle_chat", help="Hide panel"):
                st.session_state.panel_open = False
                st.rerun()

    st.markdown(
        build_leaderboard_html(
            df, active_layer, rfin_min, rfin_max, esev_min, esev_max
        ),
        unsafe_allow_html=True,
    )

# Hide the ENTIRE right overlay (fade + slide) when closed; show a reopen toggle.
# The panel stays mounted so the transition animates; the toggle brings it back.
if not split_view and not st.session_state.panel_open:
    st.markdown(
        "<style>.st-key-float_panel{opacity:0 !important;"
        "transform:translateX(24px) scale(0.98) !important;pointer-events:none !important;}</style>",
        unsafe_allow_html=True,
    )
    if st.button("☰", key="open_panel", help="Show panel"):
        st.session_state.panel_open = True
        st.rerun()
