import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from scipy.spatial import Voronoi
from shapely.geometry import MultiPoint, Point, Polygon

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Newham Risk Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Streamlit chrome ── */
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── Full-viewport canvas ── */
html, body { height: 100vh; overflow: hidden; background: #e8ecf0; margin: 0; }
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"] {
    height: 100vh !important;
    max-width: 100% !important;
    padding: 0 !important;
    overflow: hidden !important;
    background: transparent !important;
}
[data-testid="stHorizontalBlock"] {
    height: 100vh !important;
    gap: 0 !important;
    flex-wrap: nowrap !important;
    align-items: stretch !important;
}

/* ── Map column — full-screen background ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 1 !important;
    padding: 0 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child iframe,
[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child .stDeckGlJsonChart {
    height: 100vh !important;
    width: 100vw !important;
    border: none !important;
    display: block !important;
}

/* ── Floating panel ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    bottom: 20px !important;
    width: 360px !important;
    min-width: 360px !important;
    max-width: 360px !important;
    z-index: 999 !important;
    background: #ffffff !important;
    border-radius: 18px !important;
    box-shadow:
        0 1px 2px rgba(0,0,0,0.04),
        0 4px 16px rgba(0,0,0,0.08),
        0 20px 56px rgba(0,0,0,0.12) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding: 0 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child::-webkit-scrollbar { width: 3px; }
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child::-webkit-scrollbar-thumb {
    background: #e2e8f0; border-radius: 3px;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child > div {
    padding: 22px 20px 32px 20px !important;
}

/* ── Panel typography ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child * { color: #1e293b !important; }

/* ── Metric cards ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stMetric"] {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 11px !important;
    padding: 10px 14px !important;
    margin-bottom: 6px !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stMetricValue"] {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    line-height: 1.3 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stMetricLabel"] {
    font-size: 0.67rem !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.55px !important;
}

/* ── Divider ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child hr {
    border-color: #f1f5f9 !important;
    margin: 14px 0 !important;
}

/* ── Caption ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child .stCaption p {
    color: #94a3b8 !important;
    font-size: 0.7rem !important;
}

/* ── Chat messages ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stChatMessage"] {
    background: #f8fafc !important;
    border: 1px solid #f1f5f9 !important;
    border-radius: 10px !important;
    padding: 8px 12px !important;
    margin-bottom: 4px !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stChatMessage"] p {
    font-size: 0.83rem !important;
    line-height: 1.5 !important;
    color: #334155 !important;
}

/* ── Chat form input ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stTextInput"] input {
    border-radius: 22px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: #f8fafc !important;
    padding: 8px 16px !important;
    font-size: 0.83rem !important;
    color: #1e293b !important;
    transition: border-color 0.15s !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stTextInput"] input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    outline: none !important;
}

/* ── Chat send button ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stFormSubmitButton"] button {
    border-radius: 22px !important;
    background: #3b82f6 !important;
    color: #fff !important;
    border: none !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stFormSubmitButton"] button:hover {
    background: #2563eb !important;
}

/* form border reset */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Ward centroids (lon, lat) ──────────────────────────────────────────────────
WARD_COORDS: dict[str, tuple[float, float]] = {
    "Canning Town North":               (0.009,  51.514),
    "Custom House":                     (0.030,  51.511),
    "East Ham South":                   (0.053,  51.525),
    "Plaistow South":                   (0.020,  51.527),
    "Wall End":                         (0.056,  51.537),
    "Beckton":                          (0.068,  51.510),
    "Forest Gate South":                (0.038,  51.543),
    "Canning Town South":               (0.012,  51.507),
    "West Ham":                         (0.009,  51.536),
    "Plaistow West & Canning Town East":(0.010,  51.522),
    "Royal Albert":                     (0.043,  51.503),
    "Plaistow North":                   (0.020,  51.534),
    "Stratford Olympic Park":           (0.014,  51.545),
    "Boleyn":                           (0.040,  51.536),
    "Maryland":                         (0.018,  51.548),
    "Manor Park":                       (0.060,  51.543),
    "East Ham":                         (0.048,  51.537),
    "Royal Victoria":                   (0.022,  51.503),
    "Little Ilford":                    (0.058,  51.549),
    "Forest Gate North":                (0.038,  51.549),
    "Green Street East":                (0.050,  51.536),
    "Green Street West":                (0.044,  51.534),
    "Stratford":                        (0.003,  51.542),
    "Plashet":                          (0.046,  51.539),
}


# ── Data ───────────────────────────────────────────────────────────────────────
@st.cache_data
def load_risk_data() -> pd.DataFrame:
    return pd.read_csv("data/newham_ward_risk_table_CDEM.csv")


@st.cache_data
def build_polygon_layer_data(df: pd.DataFrame) -> list[dict]:
    """
    Voronoi-tessellate ward centroids into vector polygons, clip to
    Newham's convex hull, and attach risk-score colours.
    Returns a list of feature dicts ready for pydeck PolygonLayer.
    """
    risk = {row["ward"]: (float(row["R_final_CDEM"]), int(row["rank_CDEM"]))
            for _, row in df.iterrows()}

    ward_names = list(WARD_COORDS.keys())
    pts = np.array(list(WARD_COORDS.values()))          # shape (24, 2)

    # Clipping boundary: convex hull + generous buffer (~1.5 km)
    clip = MultiPoint([Point(p) for p in pts]).convex_hull.buffer(0.014)

    # Mirror points in four directions to close all Voronoi regions
    far = 0.30
    mirrors = np.concatenate(
        [pts + [far, 0], pts - [far, 0], pts + [0, far], pts - [0, far]]
    )
    vor = Voronoi(np.vstack([pts, mirrors]))

    scores = [risk[w][0] for w in ward_names if w in risk]
    min_s, max_s = min(scores), max(scores)

    def score_color(score: float) -> list[int]:
        """Teal (low risk) → amber → crimson (high risk)."""
        t = max(0.0, min(1.0, (score - min_s) / (max_s - min_s)))
        if t < 0.5:
            u = t * 2
            r = int(20  + u * (245 - 20))
            g = int(184 + u * (158 - 184))
            b = int(166 - u * 166)
            a = int(80  + u * 70)
        else:
            u = (t - 0.5) * 2
            r = int(245 + u * (185 - 245))
            g = int(158 - u * 158)
            b = 0
            a = int(150 + u * 30)
        return [r, g, b, a]

    features = []
    for i, name in enumerate(ward_names):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        if not region or -1 in region:
            continue

        poly = Polygon([vor.vertices[j] for j in region]).intersection(clip)
        if poly.is_empty:
            continue
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda p: p.area)

        coords = [[x, y] for x, y in poly.exterior.coords]
        centroid = [poly.centroid.x, poly.centroid.y]

        score, rank = risk.get(name, (0.0, 0))
        features.append(
            {
                "polygon":    coords,
                "centroid":   centroid,
                "ward":       name,
                "score":      round(score, 2),
                "rank":       rank,
                "fill_color": score_color(score),
                "line_color": [60, 70, 90, 200],
            }
        )

    return features


# ── Load & derive ──────────────────────────────────────────────────────────────
df = load_risk_data()
polygon_data = build_polygon_layer_data(df)

top3    = df.nlargest(3, "R_final_CDEM")[["ward", "R_final_CDEM", "rank_CDEM"]]
top1    = top3.iloc[0]
avg_s   = df["R_final_CDEM"].mean()
n_eq    = int(df["equity_flag"].sum())
n_hdep  = int(df["high_deprivation"].sum())

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages: list[dict] = [
        {
            "role": "assistant",
            "content": (
                "Hi! I'm your Newham Risk Analyst. Ask me about any ward, "
                "the highest-risk areas, deprivation levels, or air quality."
            ),
        }
    ]


def analyst_reply(prompt: str) -> str:
    p = prompt.lower()
    # Ward lookup
    for ward in df["ward"].tolist():
        if ward.lower() in p:
            r = df[df["ward"] == ward].iloc[0]
            return (
                f"**{ward}** — CDEM score **{r['R_final_CDEM']:.2f}** "
                f"(rank #{int(r['rank_CDEM'])}/24).  \n"
                f"IMD {r['imd_score']:,.0f} · Air quality {r['air_quality_combined']:.2f} · "
                f"Equity flagged: {'Yes' if r['equity_flag'] else 'No'} · "
                f"High deprivation: {'Yes' if r['high_deprivation'] else 'No'}."
            )
    if any(k in p for k in ["highest", "worst", "top", "most at risk"]):
        t = df.nlargest(1, "R_final_CDEM").iloc[0]
        return (
            f"The highest-risk ward is **{t['ward']}** with a CDEM score of "
            f"**{t['R_final_CDEM']:.2f}** (rank #1/24)."
        )
    if any(k in p for k in ["lowest", "safest", "least"]):
        t = df.nsmallest(1, "R_final_CDEM").iloc[0]
        return (
            f"The lowest-risk ward is **{t['ward']}** with a CDEM score of "
            f"**{t['R_final_CDEM']:.2f}** (rank #{int(t['rank_CDEM'])}/24)."
        )
    if any(k in p for k in ["average", "mean", "borough"]):
        return f"The borough-wide average CDEM risk score is **{avg_s:.2f}**."
    if any(k in p for k in ["deprivation", "imd", "poverty"]):
        t = df.nlargest(1, "imd_score").iloc[0]
        return (
            f"Most deprived ward by IMD: **{t['ward']}** (IMD {t['imd_score']:,.0f}). "
            f"{n_hdep}/24 wards are flagged as high deprivation."
        )
    if any(k in p for k in ["air", "pollution", "quality"]):
        t = df.nlargest(1, "air_quality_combined").iloc[0]
        return (
            f"Worst air quality: **{t['ward']}** "
            f"(score {t['air_quality_combined']:.2f})."
        )
    if any(k in p for k in ["equity", "flag"]):
        flagged = df[df["equity_flag"]]["ward"].tolist()
        return f"{n_eq} equity-flagged wards: {', '.join(flagged)}."
    return (
        "I can answer questions about **specific wards**, the **highest/lowest risk** "
        "areas, **deprivation** levels, **air quality**, or the **borough average**. "
        "Try: *'Tell me about Beckton'* or *'Which ward has the worst air quality?'*"
    )


# ── Layout ─────────────────────────────────────────────────────────────────────
map_col, panel_col = st.columns([3, 1])

# ━━ MAP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with map_col:
    poly_layer = pdk.Layer(
        "PolygonLayer",
        data=polygon_data,
        get_polygon="polygon",
        get_fill_color="fill_color",
        get_line_color="line_color",
        line_width_min_pixels=1,
        line_width_max_pixels=2,
        stroked=True,
        filled=True,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 60],
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=polygon_data,
        get_position="centroid",
        get_text="ward",
        get_size=11,
        get_color=[40, 50, 70, 210],
        get_alignment_baseline="'center'",
        get_anchor="'middle'",
        pickable=False,
    )

    tooltip = {
        "html": (
            "<div style='font-family:system-ui;font-size:13px;"
            "background:#fff;color:#1e293b;"
            "border:1px solid #e2e8f0;border-radius:10px;"
            "padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.1);'>"
            "<b style='font-size:14px'>{ward}</b><br/>"
            "<span style='color:#64748b;font-size:11px'>CDEM Rank #{rank}</span><br/>"
            "Risk score: <b style='color:#dc2626'>{score}</b>"
            "</div>"
        ),
        "style": {"backgroundColor": "transparent"},
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[poly_layer, text_layer],
            initial_view_state=pdk.ViewState(
                longitude=0.033,
                latitude=51.527,
                zoom=12.2,
                pitch=0,
                bearing=0,
            ),
            tooltip=tooltip,
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        ),
        use_container_width=True,
        height=1080,
    )

# ━━ PANEL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with panel_col:

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(
        """
<div style="display:flex;justify-content:space-between;align-items:flex-start;
            margin-bottom:2px;">
  <div>
    <p style="font-size:0.65rem;color:#94a3b8;text-transform:uppercase;
              letter-spacing:1px;margin:0;font-weight:600;">
      London Borough of Newham
    </p>
    <p style="font-size:1.05rem;font-weight:700;color:#0f172a;
              margin:3px 0 0;line-height:1.25;">
      Climate Risk Dashboard
    </p>
  </div>
  <button title="Menu"
    style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:9px;
           padding:7px 11px;cursor:pointer;font-size:1rem;
           color:#475569;line-height:1;flex-shrink:0;">
    ☰
  </button>
</div>
<p style="font-size:0.72rem;color:#94a3b8;margin:6px 0 0;">
  CDEM · Deprivation · Environment · Mental Health
</p>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Top risk ward highlight ─────────────────────────────────────────────────
    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,#fef2f2,#fff7ed);
            border:1px solid #fecaca;border-radius:12px;
            padding:12px 16px;margin-bottom:12px;">
  <p style="font-size:0.65rem;color:#ef4444;text-transform:uppercase;
            letter-spacing:0.8px;font-weight:700;margin:0;">
    ⚠ Highest Risk Ward
  </p>
  <p style="font-size:1.1rem;font-weight:800;color:#7f1d1d;margin:4px 0 2px;">
    {top1['ward']}
  </p>
  <p style="font-size:0.78rem;color:#b91c1c;margin:0;">
    CDEM score {top1['R_final_CDEM']:.2f} &nbsp;·&nbsp; Rank #1 of 24
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Key metrics grid ────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Avg CDEM Score", f"{avg_s:.2f}")
    with c2:
        st.metric("Equity Flagged", f"{n_eq} / {len(df)}")

    c3, c4 = st.columns(2)
    with c3:
        st.metric("High Deprivation", f"{n_hdep} / {len(df)}")
    with c4:
        st.metric("Total Wards", str(len(df)))

    st.divider()

    # ── Risk legend ─────────────────────────────────────────────────────────────
    st.markdown(
        "<p style='font-size:0.72rem;font-weight:700;color:#475569;"
        "text-transform:uppercase;letter-spacing:0.6px;margin-bottom:8px;'>"
        "Risk Score Legend</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div style="display:flex;flex-direction:column;gap:5px;font-size:0.77rem;">
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:28px;height:10px;border-radius:3px;
                background:linear-gradient(90deg,#b91c1c,#dc2626);flex-shrink:0;"></div>
    <span style="color:#475569;">High risk &nbsp;(score ≥ 2.0)</span>
  </div>
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:28px;height:10px;border-radius:3px;
                background:linear-gradient(90deg,#d97706,#f59e0b);flex-shrink:0;"></div>
    <span style="color:#475569;">Elevated &nbsp;(0 – 2.0)</span>
  </div>
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:28px;height:10px;border-radius:3px;
                background:linear-gradient(90deg,#0d9488,#14b8a6);flex-shrink:0;"></div>
    <span style="color:#475569;">Lower risk &nbsp;(score &lt; 0)</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Chat ────────────────────────────────────────────────────────────────────
    st.markdown(
        "<p style='font-size:0.72rem;font-weight:700;color:#475569;"
        "text-transform:uppercase;letter-spacing:0.6px;margin-bottom:8px;'>"
        "💬 AI Risk Analyst</p>",
        unsafe_allow_html=True,
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    with st.form("chat_form", clear_on_submit=True, border=False):
        user_input = st.text_input(
            "chat",
            placeholder="Ask about a ward or risk factor…",
            label_visibility="collapsed",
        )
        sent = st.form_submit_button("Send →", use_container_width=True)

    if sent and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        reply = analyst_reply(user_input.strip())
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
