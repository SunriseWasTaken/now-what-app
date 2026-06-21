# Now What? — London Climate & Health Risk Dashboard

Interactive Streamlit dashboard mapping climate and health risk across London wards in **Newham** and **Kensington & Chelsea**.

Built for the Health in Climate AI Hackathon (London 2026).

## Features

- **Full-screen ward map** — Pydeck polygon choropleth on a light basemap
- **Layer modes** — Risk (teal), Equity severity (amber→red), or bivariate Both blend
- **Borough selector** — switch between Newham and Kensington & Chelsea
- **Split view** — side-by-side Newham vs K&C comparison
- **Ranking leaderboard** — scrollable ward rankings in the right panel
- **Floating overlays** — legend (left) and stats panel (right), collapsible

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

## Project structure

```
app.py                          # Streamlit app (map, UI, data logic)
requirements.txt                # Python dependencies
packages.txt                    # System libs for GeoPandas (Streamlit Cloud)
runtime.txt                     # Python version (3.12)
data/
  newham_ward_risk_table_CDEM.csv
  kc_ward_risk_table_FINAL.csv
  wards_newham_kc.geojson       # Trimmed ward boundaries (42 wards)
.streamlit/
  config.toml                   # Streamlit server settings
  secrets.toml.example          # Mapbox token template
```

## Mapbox token

Pydeck uses Mapbox for the `light` basemap. Locally it often works without a key; hosted deploys usually need one.

1. Create a free token at https://account.mapbox.com/access-tokens/
2. Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`
3. Paste your token, or set `MAPBOX_API_KEY` in the environment

## Deploy

### Streamlit Community Cloud (recommended)

1. Push this repo to GitHub
2. Go to https://share.streamlit.io → **New app** → connect the repo
3. **Main file path:** `app.py`
4. **Secrets** (Settings → Secrets):

   ```toml
   MAPBOX_API_KEY = "pk.your_token_here"
   ```

5. Deploy

Streamlit Cloud uses `requirements.txt`, `packages.txt`, and `runtime.txt` automatically.

### Render / Railway / Fly.io

**Start command:**

```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

Set `MAPBOX_API_KEY` as an environment variable.

> **Note:** Netlify static hosting is not a fit for this app — it needs a long-running Python/Streamlit server.

## Data

| File | Wards | Description |
|------|-------|-------------|
| `data/newham_ward_risk_table_CDEM.csv` | 24 | Newham risk scores (CDEM model) |
| `data/kc_ward_risk_table_FINAL.csv` | 18 | Kensington & Chelsea risk scores |
| `data/wards_newham_kc.geojson` | 42 | Ward boundaries (EPSG:4326, ~61 KB) |

Equity severity is computed in-app as the collision of high deprivation (D) and low service capacity (M).

Large local-only datasets (full UK GeoJSON, postcode lookup, legacy shapefiles) are gitignored.

## Branches

| Branch | Description |
|--------|-------------|
| `main` | Bivariate blend overlay (default) |
| `view/equity-pins` | Teal risk map + equity pin drops |
| `view/3d-cityscape` | 3D extrusion by equity severity |

## License

Hackathon project — check with the team before reuse.
