import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(
    page_title="Newham Climate & Health Risk Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Reset Streamlit chrome ── */
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    display: none !important;
}

/* ── Full-viewport canvas ── */
html, body {
    height: 100vh;
    overflow: hidden;
    background: #080c12;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"] {
    height: 100vh !important;
    max-width: 100% !important;
    padding: 0 !important;
    overflow: hidden !important;
    background: transparent !important;
}

/* ── Column row fills viewport ── */
[data-testid="stHorizontalBlock"] {
    height: 100vh !important;
    align-items: stretch !important;
    gap: 0 !important;
}

/* ── Map column: no padding, dark bg ── */
[data-testid="column"]:first-child {
    padding: 0 !important;
    flex: 1 1 0% !important;
    background: #080c12 !important;
    overflow: hidden !important;
}

/* pydeck iframe fills its parent */
[data-testid="column"]:first-child iframe,
[data-testid="column"]:first-child .stDeckGlJsonChart {
    height: 100vh !important;
    width: 100% !important;
    border: none !important;
}

/* ── Floating panel column ── */
[data-testid="column"]:last-child {
    flex: 0 0 380px !important;
    max-width: 380px !important;
    min-width: 380px !important;
    height: 100vh !important;
    overflow-y: auto !important;
    padding: 28px 22px 100px 22px !important;
    background: rgba(10, 14, 22, 0.84) !important;
    backdrop-filter: blur(22px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(22px) saturate(160%) !important;
    border-left: 1px solid rgba(255, 255, 255, 0.07) !important;
    box-shadow: -8px 0 40px rgba(0, 0, 0, 0.55) !important;
}

/* scrollbar for panel */
[data-testid="column"]:last-child::-webkit-scrollbar { width: 4px; }
[data-testid="column"]:last-child::-webkit-scrollbar-track { background: transparent; }
[data-testid="column"]:last-child::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.12);
    border-radius: 4px;
}

/* ── Panel typography ── */
[data-testid="column"]:last-child * { color: #e8eaf0 !important; }

[data-testid="column"]:last-child h1,
[data-testid="column"]:last-child h2,
[data-testid="column"]:last-child h3 {
    color: #ffffff !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px !important;
}

/* ── Metric cards ── */
[data-testid="column"]:last-child [data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    margin-bottom: 8px !important;
}

[data-testid="column"]:last-child [data-testid="stMetricValue"] {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #f0f2f8 !important;
}

[data-testid="column"]:last-child [data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    color: #8892a4 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
}

/* ── Chat messages ── */
[data-testid="column"]:last-child [data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
}

/* ── Chat input ── */
[data-testid="column"]:last-child [data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
}

/* ── Divider ── */
[data-testid="column"]:last-child hr {
    border-color: rgba(255, 255, 255, 0.08) !important;
    margin: 16px 0 !important;
}

/* Caption text */
[data-testid="column"]:last-child .stCaption p {
    color: #6b7585 !important;
    font-size: 0.72rem !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Data ───────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv("data/newham_ward_risk_table_CDEM.csv")


df = load_data()

# Approximate ward centroids (lon, lat) for pydeck
WARD_COORDS: dict[str, tuple[float, float]] = {
    "Canning Town North":              (0.009,  51.514),
    "Custom House":                    (0.030,  51.511),
    "East Ham South":                  (0.053,  51.525),
    "Plaistow South":                  (0.020,  51.527),
    "Wall End":                        (0.056,  51.537),
    "Beckton":                         (0.068,  51.510),
    "Forest Gate South":               (0.038,  51.543),
    "Canning Town South":              (0.012,  51.507),
    "West Ham":                        (0.009,  51.536),
    "Plaistow West & Canning Town East":(0.010, 51.522),
    "Royal Albert":                    (0.043,  51.503),
    "Plaistow North":                  (0.020,  51.534),
    "Stratford Olympic Park":          (0.014,  51.545),
    "Boleyn":                          (0.040,  51.536),
    "Maryland":                        (0.018,  51.548),
    "Manor Park":                      (0.060,  51.543),
    "East Ham":                        (0.048,  51.537),
    "Royal Victoria":                  (0.022,  51.503),
    "Little Ilford":                   (0.058,  51.549),
    "Forest Gate North":               (0.038,  51.549),
    "Green Street East":               (0.050,  51.536),
    "Green Street West":               (0.044,  51.534),
    "Stratford":                       (0.003,  51.542),
    "Plashet":                         (0.046,  51.539),
}


def risk_color(score: float, min_s: float, max_s: float) -> list[int]:
    """Map a risk score to an RGBA colour: low → blue, high → red."""
    t = max(0.0, min(1.0, (score - min_s) / (max_s - min_s)))
    # Palette: deep-blue → amber → vivid-red
    if t < 0.5:
        r = int(20  + t * 2 * (235 - 20))
        g = int(120 + t * 2 * (160 - 120))
        b = int(200 - t * 2 * (200 - 40))
    else:
        u = (t - 0.5) * 2
        r = int(235 + u * (255 - 235))
        g = int(160 - u * 160)
        b = int(40  - u * 40)
    return [r, g, b, 210]


min_score = df["R_final_CDEM"].min()
max_score = df["R_final_CDEM"].max()

map_data = []
for _, row in df.iterrows():
    coords = WARD_COORDS.get(row["ward"])
    if coords:
        score = row["R_final_CDEM"]
        map_data.append(
            {
                "lon": coords[0],
                "lat": coords[1],
                "ward": row["ward"],
                "score": round(score, 2),
                "rank": int(row["rank_CDEM"]),
                "color": risk_color(score, min_score, max_score),
                "radius": int(200 + abs(score) * 60),
            }
        )

# ── Sidebar metrics (derived) ──────────────────────────────────────────────────
top3 = df.nlargest(3, "R_final_CDEM")[["ward", "R_final_CDEM", "rank_CDEM"]]
avg_score = df["R_final_CDEM"].mean()
n_high_dep = int(df["high_deprivation"].sum())
n_equity = int(df["equity_flag"].sum())

# Session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm your Newham Risk Analyst. Ask me about ward risk scores, "
                "deprivation patterns, or air quality across the borough."
            ),
        }
    ]

# ── Layout ─────────────────────────────────────────────────────────────────────
map_col, panel_col = st.columns([3, 1])   # CSS overrides the visual widths

# ── MAP ────────────────────────────────────────────────────────────────────────
with map_col:
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="radius",
        radius_scale=4,
        radius_min_pixels=8,
        radius_max_pixels=60,
        pickable=True,
        opacity=0.88,
        stroked=True,
        get_line_color=[255, 255, 255, 60],
        line_width_min_pixels=1,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=map_data,
        get_position=["lon", "lat"],
        get_text="ward",
        get_size=11,
        get_color=[220, 225, 240, 200],
        get_angle=0,
        get_alignment_baseline="'top'",
        get_pixel_offset=[0, 14],
    )

    view = pdk.ViewState(
        longitude=0.033,
        latitude=51.527,
        zoom=12.2,
        pitch=35,
        bearing=0,
    )

    tooltip = {
        "html": (
            "<div style='font-family:system-ui;font-size:13px;"
            "background:rgba(10,14,22,0.9);color:#e8eaf0;"
            "border:1px solid rgba(255,255,255,0.12);"
            "border-radius:8px;padding:10px 14px;'>"
            "<b style='color:#fff'>{ward}</b><br/>"
            "Risk Score: <b style='color:#f97316'>{score}</b><br/>"
            "CDEM Rank: <b>#{rank}</b>"
            "</div>"
        ),
        "style": {"backgroundColor": "transparent", "color": "white"},
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[scatter_layer, text_layer],
            initial_view_state=view,
            tooltip=tooltip,
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        ),
        use_container_width=True,
        height=900,
    )

# ── FLOATING PANEL ─────────────────────────────────────────────────────────────
with panel_col:
    # Header
    st.markdown("### 🌍 Newham Risk Dashboard")
    st.caption("Climate · Deprivation · Environment · Mental Health")
    st.divider()

    # ── Top risk wards ─────────────────────────────────────────────────────────
    st.markdown("**⚠️ Highest Risk Wards**")
    rank_colors = ["#ef4444", "#f97316", "#eab308"]
    for i, (_, row) in enumerate(top3.iterrows()):
        medal = ["🥇", "🥈", "🥉"][i]
        st.metric(
            label=f"{medal}  Rank #{int(row['rank_CDEM'])} — {row['ward']}",
            value=f"{row['R_final_CDEM']:.2f}",
        )

    st.divider()

    # ── Summary stats ──────────────────────────────────────────────────────────
    st.markdown("**📊 Borough Overview**")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Avg CDEM Score", f"{avg_score:.2f}")
    with c2:
        st.metric("Equity-Flagged", f"{n_equity} / {len(df)}")

    st.divider()

    # ── Legend ─────────────────────────────────────────────────────────────────
    st.markdown("**🎨 Risk Score Legend**")
    st.markdown(
        """
<div style="display:flex;flex-direction:column;gap:6px;font-size:0.78rem;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:14px;height:14px;border-radius:50%;background:#ef4444;flex-shrink:0"></div>
    <span style="color:#aab0bc">High risk &nbsp;(score &gt; 2.0)</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:14px;height:14px;border-radius:50%;background:#f97316;flex-shrink:0"></div>
    <span style="color:#aab0bc">Elevated risk &nbsp;(1.0 – 2.0)</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:14px;height:14px;border-radius:50%;background:#3b82f6;flex-shrink:0"></div>
    <span style="color:#aab0bc">Lower risk &nbsp;(score &lt; 0)</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:12px;height:12px;border-radius:50%;background:#3b82f6;flex-shrink:0"></div>
    <span style="color:#aab0bc;font-size:0.72rem">Larger circle = higher absolute score</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Chat ───────────────────────────────────────────────────────────────────
    st.markdown("**💬 Risk Analyst**")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask about a ward or risk factor…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Simple keyword response — replace with LLM call as desired
        p = prompt.lower()
        if any(w.lower() in p for w in df["ward"].tolist()):
            matched = next(w for w in df["ward"] if w.lower() in p)
            row = df[df["ward"] == matched].iloc[0]
            reply = (
                f"**{matched}** has a CDEM Risk Score of **{row['R_final_CDEM']:.2f}** "
                f"(Rank #{int(row['rank_CDEM'])} of 24). "
                f"IMD: {row['imd_score']:,.0f} · Air Quality: {row['air_quality_combined']:.2f} · "
                f"Equity flagged: {'Yes' if row['equity_flag'] else 'No'}."
            )
        elif "highest" in p or "worst" in p or "top" in p:
            t = df.nlargest(1, "R_final_CDEM").iloc[0]
            reply = (
                f"The highest-risk ward is **{t['ward']}** with a CDEM score of "
                f"**{t['R_final_CDEM']:.2f}**."
            )
        elif "average" in p or "mean" in p:
            reply = f"The borough average CDEM risk score is **{avg_score:.2f}**."
        elif "deprivation" in p or "imd" in p:
            top_dep = df.nlargest(1, "imd_score").iloc[0]
            reply = (
                f"The most deprived ward by IMD score is **{top_dep['ward']}** "
                f"(IMD: {top_dep['imd_score']:,.0f}). "
                f"{n_high_dep} of 24 wards are flagged as high deprivation."
            )
        elif "air" in p:
            top_aq = df.nlargest(1, "air_quality_combined").iloc[0]
            reply = (
                f"Worst air quality: **{top_aq['ward']}** "
                f"(score {top_aq['air_quality_combined']:.2f})."
            )
        else:
            reply = (
                "I can answer questions about specific wards, the highest risk areas, "
                "deprivation levels, air quality, or average scores. Try asking: "
                "*'Which ward has the highest risk?'* or *'Tell me about Beckton.'*"
            )

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
