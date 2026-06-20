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

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

html, body { height: 100vh; overflow: hidden; margin: 0; background: #eef1f4; }

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
    position: relative !important;
}

/* ── Map column (middle) — full-screen background ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 1 !important;
    padding: 0 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) iframe,
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) .stDeckGlJsonChart {
    height: 100vh !important;
    width: 100vw !important;
    border: none !important;
    display: block !important;
}

/* ── Legend panel (left) ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
    position: fixed !important;
    top: 20px !important;
    left: 20px !important;
    width: 280px !important;
    min-width: 280px !important;
    max-width: 280px !important;
    z-index: 999 !important;
    padding: 0 !important;
    background: rgba(255, 255, 255, 0.92) !important;
    backdrop-filter: blur(12px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(12px) saturate(140%) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.7) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 8px 32px rgba(0,0,0,0.10) !important;
    overflow: hidden !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child > div {
    padding: 18px 16px !important;
}

/* ── Chat panel (right) ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    bottom: 20px !important;
    width: 380px !important;
    min-width: 380px !important;
    max-width: 380px !important;
    z-index: 999 !important;
    padding: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    background: rgba(255, 255, 255, 0.92) !important;
    backdrop-filter: blur(12px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(12px) saturate(140%) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.7) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 8px 32px rgba(0,0,0,0.10) !important;
    overflow: hidden !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child > div {
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    padding: 0 !important;
    overflow: hidden !important;
}

/* Chat scroll area */
.chat-scroll {
    flex: 1 !important;
    overflow-y: auto !important;
    padding: 0 18px 8px 18px !important;
}
.chat-scroll::-webkit-scrollbar { width: 3px; }
.chat-scroll::-webkit-scrollbar-thumb { background: #dde3ea; border-radius: 3px; }

/* Chat messages */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 4px 0 !important;
    margin-bottom: 2px !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stChatMessage"] p,
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stChatMessage"] li {
    font-size: 0.84rem !important;
    line-height: 1.55 !important;
    color: #334155 !important;
}

/* Chat input pinned inside panel */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stChatInput"] {
    position: relative !important;
    bottom: auto !important;
    padding: 10px 14px 14px 14px !important;
    border-top: 1px solid #eef2f6 !important;
    background: rgba(255,255,255,0.95) !important;
    margin: 0 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stChatInput"] textarea {
    border-radius: 24px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: #f8fafc !important;
    font-size: 0.84rem !important;
    color: #1e293b !important;
    padding: 10px 16px !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stChatInput"] textarea:focus {
    border-color: #94a3b8 !important;
    box-shadow: none !important;
}

/* Hide global chat input dock if Streamlit renders one */
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
        t = max(0.0, min(1.0, (score - min_s) / (max_s - min_s)))
        # Purple (low) → teal (high) — matches target legend aesthetic
        r = int(94  + t * (45  - 94))
        g = int(39  + t * (212 - 39))
        b = int(130 + t * (191 - 130))
        a = int(160 + t * 40)
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

        score, rank = risk.get(name, (0.0, 0))
        features.append(
            {
                "polygon":    [[x, y] for x, y in poly.exterior.coords],
                "ward":       name,
                "score":      round(score, 2),
                "rank":       rank,
                "fill_color": score_color(score),
                "line_color": [255, 255, 255, 180],
            }
        )
    return features


df = load_risk_data()
polygon_data = build_polygon_layer_data(df)

top1 = df.nlargest(1, "R_final_CDEM").iloc[0]
min_score = df["R_final_CDEM"].min()
max_score = df["R_final_CDEM"].max()
avg_s = df["R_final_CDEM"].mean()
n_eq = int(df["equity_flag"].sum())
n_hdep = int(df["high_deprivation"].sum())
now_str = datetime.now().strftime("%b %d, %Y at %-I:%M %p")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                f"The **Final Risk Score (CDEM)** layer shows ward-level climate and health "
                f"risk across Newham. The highest-risk ward is **{top1['ward']}** "
                f"(score **{top1['R_final_CDEM']:.2f}**, rank #1 of 24).\n\n"
                f"Ask me about any ward, deprivation patterns, air quality, or equity flags."
            ),
        }
    ]


def analyst_reply(prompt: str) -> str:
    p = prompt.lower()
    for ward in df["ward"].tolist():
        if ward.lower() in p:
            r = df[df["ward"] == ward].iloc[0]
            return (
                f"**{ward}** — CDEM score **{r['R_final_CDEM']:.2f}** "
                f"(rank #{int(r['rank_CDEM'])}/24).\n\n"
                f"IMD {r['imd_score']:,.0f} · Air quality {r['air_quality_combined']:.2f} · "
                f"Equity flagged: {'Yes' if r['equity_flag'] else 'No'}."
            )
    if any(k in p for k in ["highest", "worst", "top", "most at risk"]):
        t = df.nlargest(1, "R_final_CDEM").iloc[0]
        return f"The highest-risk ward is **{t['ward']}** (CDEM **{t['R_final_CDEM']:.2f}**)."
    if any(k in p for k in ["lowest", "safest", "least"]):
        t = df.nsmallest(1, "R_final_CDEM").iloc[0]
        return (
            f"The lowest-risk ward is **{t['ward']}** "
            f"(CDEM **{t['R_final_CDEM']:.2f}**, rank #{int(t['rank_CDEM'])}/24)."
        )
    if any(k in p for k in ["average", "mean", "borough"]):
        return f"Borough average CDEM score: **{avg_s:.2f}**."
    if any(k in p for k in ["deprivation", "imd", "poverty"]):
        t = df.nlargest(1, "imd_score").iloc[0]
        return (
            f"Most deprived: **{t['ward']}** (IMD {t['imd_score']:,.0f}). "
            f"{n_hdep}/24 wards flagged high deprivation."
        )
    if any(k in p for k in ["air", "pollution", "quality"]):
        t = df.nlargest(1, "air_quality_combined").iloc[0]
        return f"Worst air quality: **{t['ward']}** (score {t['air_quality_combined']:.2f})."
    if any(k in p for k in ["equity", "flag"]):
        flagged = df[df["equity_flag"]]["ward"].tolist()
        return f"{n_eq} equity-flagged wards: {', '.join(flagged)}."
    return (
        "Try asking about a specific ward (e.g. *'Tell me about Beckton'*), "
        "the highest-risk area, deprivation, or air quality."
    )


# ── Layout: legend | map | chat ───────────────────────────────────────────────
legend_col, map_col, chat_col = st.columns([1, 6, 1.4])

# ━━ LEGEND (left overlay) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with legend_col:
    st.markdown(
        """
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
  <span style="font-size:0.95rem;font-weight:700;color:#1e293b;">Legend</span>
  <span style="font-size:1rem;color:#64748b;cursor:pointer;line-height:1;">☰</span>
</div>
<p style="font-size:0.72rem;font-weight:600;color:#64748b;margin:0 0 6px;
          text-transform:uppercase;letter-spacing:0.5px;">
  Final Risk Score (CDEM)
</p>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div style="margin-bottom:6px;">
  <div style="height:12px;border-radius:6px;
              background:linear-gradient(90deg,#5e2782,#2dd4bf);
              margin-bottom:6px;"></div>
  <div style="display:flex;justify-content:space-between;
              font-size:0.72rem;color:#64748b;">
    <span>{min_score:.1f}</span>
    <span>{max_score:.1f}</span>
  </div>
</div>
<p style="font-size:0.72rem;color:#94a3b8;margin:10px 0 0;line-height:1.4;">
  Ward polygons coloured by CDEM risk score.<br/>
  Higher score = greater climate &amp; health risk.
</p>
""",
        unsafe_allow_html=True,
    )

# ━━ MAP (full-screen background) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with map_col:
    poly_layer = pdk.Layer(
        "PolygonLayer",
        data=polygon_data,
        get_polygon="polygon",
        get_fill_color="fill_color",
        get_line_color="line_color",
        line_width_min_pixels=1.5,
        line_width_max_pixels=2,
        stroked=True,
        filled=True,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 80],
    )
    tooltip = {
        "html": (
            "<div style='font-family:system-ui;font-size:13px;background:#fff;"
            "color:#1e293b;border:1px solid #e2e8f0;border-radius:10px;"
            "padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.1);'>"
            "<b>{ward}</b><br/>"
            "<span style='color:#64748b;font-size:11px'>Rank #{rank}</span><br/>"
            "Score: <b style='color:#7c3aed'>{score}</b>"
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
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        ),
        use_container_width=True,
        height=1080,
    )

# ━━ CHAT (right overlay) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with chat_col:
    st.markdown(
        f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:16px 18px 10px;border-bottom:1px solid #f1f5f9;">
  <span style="font-size:0.72rem;color:#94a3b8;">{now_str}</span>
  <span style="font-size:1rem;color:#64748b;cursor:pointer;">☰</span>
</div>
<div style="padding:10px 18px 8px;border-bottom:1px solid #f1f5f9;">
  <p style="font-size:0.72rem;color:#64748b;margin:0 0 2px;
            text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">
    Highest Risk Ward
  </p>
  <p style="font-size:0.9rem;font-weight:700;color:#1e293b;margin:0;">
    {top1['ward']}
    <span style="font-weight:500;color:#7c3aed;font-size:0.82rem;">
      &nbsp;·&nbsp;{top1['R_final_CDEM']:.2f}
    </span>
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Ask about this map…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        reply = analyst_reply(prompt)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
