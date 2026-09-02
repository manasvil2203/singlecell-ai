import json
from pathlib import Path

import requests
import pandas as pd


GDC_CASES_ENDPOINT = "https://api.gdc.cancer.gov/cases"
OUTPUT_DIR = Path("data/raw_clinical")
OUTPUT_FILE = OUTPUT_DIR / "tcga_luad_cases.tsv"


def download_tcga_luad_cases() -> None:
    """Download TCGA-LUAD clinical metadata from the GDC cases endpoint."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filters = {
        "op": "in",
        "content": {
            "field": "project.project_id",
            "value": ["TCGA-LUAD"]
        }
    }

    fields = [
        "case_id",
        "submitter_id",
        "project.project_id",
        "demographic.gender",
        "demographic.race",
        "demographic.ethnicity",
        "demographic.vital_status",
        "diagnoses.primary_diagnosis",
        "diagnoses.ajcc_pathologic_stage",
        "diagnoses.tumor_grade",
        "diagnoses.age_at_diagnosis",
        "diagnoses.days_to_death",
        "diagnoses.days_to_last_follow_up",
        "exposures.tobacco_smoking_status",
        "exposures.years_smoked",
        "exposures.cigarettes_per_day",
        "exposures.pack_years_smoked"
    ]

    params = {
        "filters": json.dumps(filters),
        "fields": ",".join(fields),
        "format": "TSV",
        "size": "2000"
    }

    response = requests.get(GDC_CASES_ENDPOINT, params=params)
    response.raise_for_status()

    OUTPUT_FILE.write_text(response.text, encoding="utf-8")

    df = pd.read_csv(OUTPUT_FILE, sep="\t")
    print(f"Downloaded {df.shape[0]} rows and {df.shape[1]} columns.")
    print(f"Saved to: {OUTPUT_FILE}")
    print(df.head())


if __name__ == "__main__":
    download_tcga_luad_cases()