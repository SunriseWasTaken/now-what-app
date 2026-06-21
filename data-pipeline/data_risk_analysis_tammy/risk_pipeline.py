"""
Now What? - Newham Climate Mental Health Risk Pipeline
=========================================================
Team: After The Fire Has Gone | Health in Climate AI Hackathon, London 2026
Owner: Tammy (Data/ML)

WHAT THIS SCRIPT DOES
----------------------
Produces TWO outputs, both real data, validated:

1. WARD-LEVEL risk table: R = D + E + M. 24 real Newham wards, ranked.
   D = deprivation, E = climate exposure, M = capacity (PROXY - see below).

2. PRACTICE-LEVEL clinical burden: C, kept SEPARATE from the ward table.
   See clinical_processing.py -> newham_clinical_practice_level_real.csv
   (46-47 genuine Newham GP practices, real 12-month psychotropic
   prescribing volumes).

M IS A PROXY, NOT THE PRD's SPECIFIED METRIC: the PRD asked for
OpenStreetMap mental-health-service counts (CMHTs, crisis teams). That
wasn't sourced in time. Instead, M uses GP practice DENSITY per ward (same
46 Newham practices used for C), joined to ward via postcodes.io's exact
postcode->ward API (precise, not nearest-neighbor). FLAG THIS IN THE PITCH
AND POLICY BRIEF: GP practice count measures general primary-care access,
not specialist mental health crisis capacity. Real data, defensible as
"best available given time", but not equivalent to what the PRD described.

WHY C ISN'T MERGED INTO THE WARD TABLE: the PRD's own Data Architecture
table specifies the clinical layer's output as "Mental health burden +
gaps by practice" - practice level is PRD-compliant on its own. Merging C
to ward would need the same postcodes.io-style join used for M; not done
yet, but is now straightforward to add if time allows - the lookup
mechanism already exists (see get_practice_wards_LOCAL.py).

DATA PROVENANCE
----------------
D: gov.uk IMD25 (File 1, LSOA rank+decile) -> ONS LSOA-to-ward lookup ->
   ward-level mean rank, inverted so higher = more deprived.
   See imd_ward_aggregation.py.
E: DEFRA LAQM background pollution grids (PM2.5 + NO2, 2021) -> nearest-
   grid-cell matched to LSOA population-weighted centroids (ONS) -> same
   LSOA-to-ward lookup -> ward-level mean.
   See airquality_processing.py.
C: OpenPrescribing (NHS North East London, BNF 4.1/4.2/4.3) -> filtered to
   genuine Newham GP practices via epraccur.csv (NHS ODS reference data,
   Open Government Licence - postcode + prescribing_setting='RO76' to
   exclude PCN hubs/specialist clinics/urgent care).
   See clinical_processing.py.

WARD NAMES: Newham's real 24 wards, confirmed via ONS LSOA(2021) to
Electoral Ward(2024) to LAD(2024) Best Fit Lookup. (An earlier draft of
this script used guessed ward names that don't exist - corrected.)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# CONFIG - Sandya / team: tune these without touching the rest
# ============================================================
DEPRIVATION_HIGH_QUANTILE = 0.80   # top 20% most deprived -> equity flag
CAPACITY_LOW_QUANTILE = 0.20       # bottom 20% GP-practice-density -> equity flag
EQUITY_MULTIPLIER = 1.3            # applied to flagged wards' R score

NEWHAM_WARDS = [
    "Beckton", "Boleyn", "Canning Town North", "Canning Town South",
    "Custom House", "East Ham", "East Ham South", "Forest Gate North",
    "Forest Gate South", "Green Street East", "Green Street West",
    "Little Ilford", "Manor Park", "Maryland", "Plaistow North",
    "Plaistow South", "Plaistow West & Canning Town East", "Plashet",
    "Royal Albert", "Royal Victoria", "Stratford", "Stratford Olympic Park",
    "Wall End", "West Ham",
]


def zscore(series):
    return (series - series.mean()) / series.std(ddof=0)


# ============================================================
# 1. Ward-level data loaders (D + E, both real)
# ============================================================

def load_deprivation_data():
    """D: deprivation, by ward. See imd_ward_aggregation.py for the join."""
    real = pd.read_csv("/home/claude/now_what/newham_ward_imd_real.csv")
    df = real[["ward_name", "imd_score_proxy"]].rename(
        columns={"ward_name": "ward", "imd_score_proxy": "imd_score"}
    )
    missing = set(NEWHAM_WARDS) - set(df["ward"])
    if missing:
        print(f"WARNING: no real IMD data for: {missing}")
    return df


def load_climate_data():
    """E: PM2.5 + NO2 average, by ward. See airquality_processing.py."""
    real = pd.read_csv("/home/claude/now_what/newham_ward_airquality_real.csv")
    real["air_quality_combined"] = (real["pm25_ugm3"] + real["no2_ugm3"]) / 2
    df = real[["ward_name", "air_quality_combined"]].rename(columns={"ward_name": "ward"})
    missing = set(NEWHAM_WARDS) - set(df["ward"])
    if missing:
        print(f"WARNING: no real air quality data for: {missing}")
    return df, "air_quality_combined"


# ============================================================
# 2. Capacity proxy (M) - REAL but a PROXY, not the PRD's spec
# ============================================================

def load_capacity_data():
    """M (capacity): GP practice count per ward. REAL DATA, but a PROXY -
    not the PRD's specified metric. PRD asked for OpenStreetMap mental-
    health-service counts (CMHTs, crisis teams, etc.) - not sourced in
    time. INSTEAD: GP practice density per ward, from the same 46 real
    Newham practices used for C, joined to ward via postcodes.io's exact
    postcode->ward lookup (precise, not nearest-neighbor approximation).
    CAVEAT - FLAG THIS IN THE PITCH/POLICY BRIEF: GP practice count
    measures general primary-care access, not specialist mental health
    crisis capacity. Real data, defensible as "best available given time",
    but not equivalent to what the PRD described.
    Only 21 of 24 Newham wards have >=1 matched practice in this dataset;
    the other 3 are filled with 0 (treated as a real low-capacity signal,
    not missing data - but not manually verified, flag before presenting
    as a definitive finding)."""
    real = pd.read_csv("/home/claude/now_what/newham_ward_capacity_proxy.csv")
    df = real.rename(columns={"gp_practice_count": "capacity_proxy"})
    full = pd.DataFrame({"ward": NEWHAM_WARDS}).merge(df, on="ward", how="left")
    zero_wards = full[full["capacity_proxy"].isna()]["ward"].tolist()
    full["capacity_proxy"] = full["capacity_proxy"].fillna(0)
    if zero_wards:
        print(f"NOTE: 0 matched GP practices for: {zero_wards} "
              f"(treated as 0 - verify before presenting as a finding)")
    return full


# ============================================================
# 3. Ward-level risk model: R = D + E + M
# ============================================================

def build_ward_risk_table():
    deprivation = load_deprivation_data()
    climate, climate_col = load_climate_data()
    capacity = load_capacity_data()
    df = deprivation.merge(climate, on="ward").merge(capacity, on="ward")

    df["D"] = zscore(df["imd_score"])
    df["E"] = zscore(df[climate_col])
    # M is inverse capacity: FEWER practices -> HIGHER risk contribution
    df["M"] = -zscore(df["capacity_proxy"])
    df["R_raw"] = df["D"] + df["E"] + df["M"]

    # Equity flag: NOW uses the real thing - high deprivation AND low
    # capacity (capacity = GP practice proxy, see load_capacity_data caveat)
    dep_cutoff = df["imd_score"].quantile(DEPRIVATION_HIGH_QUANTILE)
    cap_cutoff = df["capacity_proxy"].quantile(CAPACITY_LOW_QUANTILE)
    df["high_deprivation"] = df["imd_score"] >= dep_cutoff
    df["low_capacity"] = df["capacity_proxy"] <= cap_cutoff
    df["equity_flag"] = df["high_deprivation"] & df["low_capacity"]
    df["R_final"] = np.where(df["equity_flag"], df["R_raw"] * EQUITY_MULTIPLIER, df["R_raw"])

    df = df.sort_values("R_final", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    cols = ["rank", "ward", "imd_score", climate_col, "capacity_proxy",
            "D", "E", "M", "R_raw", "equity_flag", "R_final"]
    return df[cols].round(3)


def equity_audit(df):
    flagged = df[df["equity_flag"]].copy()
    return {
        "n_equity_flagged_wards": int(flagged.shape[0]),
        "pct_of_top10_flagged": round(100 * df.head(10)["equity_flag"].sum() / 10, 1),
        "flagged_wards": flagged["ward"].tolist(),
    }, flagged


# ============================================================
# 4. Practice-level clinical burden (C) - separate, see clinical_processing.py
# ============================================================

def load_clinical_practice_table():
    return pd.read_csv("/home/claude/now_what/newham_clinical_practice_level_real.csv")


if __name__ == "__main__":
    # --- Ward-level R = D + E + M ---
    ward_risk = build_ward_risk_table()
    ward_risk.to_csv("/home/claude/now_what/newham_ward_risk_table.csv", index=False)

    summary, flagged = equity_audit(ward_risk)
    print("=== Ward-level risk table (R = D + E + M), top 10 ===")
    print(ward_risk.head(10).to_string(index=False))
    print("\n=== Equity audit summary (high-deprivation + low-capacity-proxy) ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    top10 = ward_risk.head(10)
    colors = ["#c0392b" if f else "#2c7fb8" for f in top10["equity_flag"]]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top10["ward"][::-1], top10["R_final"][::-1], color=colors[::-1])
    ax.set_xlabel("Composite Risk Score (R_final = D + E + M, equity-weighted)")
    ax.set_title("Newham: Top 10 Wards by Post-Disaster Mental Health Risk\n"
                  "(red = high-deprivation + low GP-practice-density ward)")
    plt.tight_layout()
    plt.savefig("/home/claude/now_what/newham_ward_risk_chart.png", dpi=150)

    # --- Practice-level C, reported separately ---
    clinical = load_clinical_practice_table()
    print(f"\n=== Practice-level clinical burden (C), top 10 of {len(clinical)} Newham GP practices ===")
    print(clinical.head(10).to_string(index=False))

    print("\nSaved: newham_ward_risk_table.csv, newham_ward_risk_chart.png")
    print("(Practice-level C already saved separately: newham_clinical_practice_level_real.csv)")
