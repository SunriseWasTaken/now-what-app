"""Newham clinical burden (C): OpenPrescribing filtered to genuine Newham GP practices."""

import pandas as pd

EPRACCUR_COLS = [
    "code", "name", "national_grouping", "health_geog", "addr1", "addr2", "addr3",
    "addr4", "addr5", "postcode", "open_date", "close_date", "status", "subtype",
    "commissioner", "join_date", "left_date", "phone", "f19", "f20", "f21",
    "amended", "f23", "provider_purchaser", "f25", "prescribing_setting", "f27",
]

NEWHAM_POSTCODE_DISTRICTS = r"^(E6|E7|E12|E13|E15|E16|E20)\s"


def load_newham_clinical_practice_level(epraccur_path, prescribing_path):
    epraccur = pd.read_csv(epraccur_path, header=None, names=EPRACCUR_COLS)
    nel = pd.read_csv(prescribing_path)

    merged = nel.merge(
        epraccur[["code", "postcode", "status", "prescribing_setting"]],
        left_on="id", right_on="code", how="left",
    )

    newham_mask = merged["postcode"].str.strip().str.match(NEWHAM_POSTCODE_DISTRICTS, na=False)
    gp_practice_mask = merged["prescribing_setting"] == "RO76"
    active_mask = merged["status"] == "ACTIVE"

    nh = merged[newham_mask & gp_practice_mask & active_mask].copy()

    nh["date"] = pd.to_datetime(nh["date"])
    latest_12mo = nh[nh["date"] >= nh["date"].max() - pd.DateOffset(months=11)]

    practice_burden = (
        latest_12mo.groupby(["id", "name", "postcode"])["y_items"]
        .sum()
        .reset_index()
        .rename(columns={"y_items": "psychotropic_items_12mo"})
        .sort_values("psychotropic_items_12mo", ascending=False)
    )

    return practice_burden


if __name__ == "__main__":
    df = load_newham_clinical_practice_level("epraccur.csv", "nel_prescribing.csv")
    print(f"Genuine Newham GP practices: {len(df)}")
    df.to_csv("newham_clinical_practice_level_real.csv", index=False)
