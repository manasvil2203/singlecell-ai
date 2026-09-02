import sqlite3
from pathlib import Path

import pandas as pd


RAW_FILE = Path("data/raw_clinical/tcga_luad_cases.tsv")
DB_PATH = Path("data/clinical_luad.db")


def clean_missing(value):
    """Convert common GDC missing-value strings to None."""
    if pd.isna(value):
        return None

    if isinstance(value, str) and value.lower() in {
        "not reported",
        "not available",
        "unknown",
        "--"
    }:
        return None

    return value


def transform_patients(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw GDC case metadata into the patients table."""
    patients = pd.DataFrame({
        "patient_id": raw_df["submitter_id"],
        "age_at_diagnosis_days": raw_df["diagnoses.0.age_at_diagnosis"],
        "sex": None,
        "race": raw_df["demographic.race"],
        "ethnicity": raw_df["demographic.ethnicity"],
        "vital_status": raw_df["demographic.vital_status"],
        "days_to_death": None,
        "days_to_last_follow_up": raw_df["diagnoses.0.days_to_last_follow_up"],
    })

    patients = patients.map(clean_missing)
    return patients.drop_duplicates(subset=["patient_id"])


def transform_diagnoses(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw GDC diagnosis metadata into the diagnoses table."""
    diagnoses = pd.DataFrame({
        "diagnosis_id": raw_df["case_id"],
        "patient_id": raw_df["submitter_id"],
        "primary_diagnosis": raw_df["diagnoses.0.primary_diagnosis"],
        "tumor_stage": raw_df["diagnoses.0.ajcc_pathologic_stage"],
        "tumor_grade": None,
        "days_to_diagnosis": None,
    })

    diagnoses = diagnoses.map(clean_missing)
    return diagnoses.drop_duplicates(subset=["diagnosis_id"])


def transform_exposures(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw GDC exposure metadata into the exposures table."""
    exposures = pd.DataFrame({
        "exposure_id": raw_df["case_id"],
        "patient_id": raw_df["submitter_id"],
        "smoking_status": raw_df["exposures.0.tobacco_smoking_status"],
        "years_smoked": None,
        "cigarettes_per_day": raw_df["exposures.0.cigarettes_per_day"],
        "pack_years_smoked": raw_df["exposures.0.pack_years_smoked"],
    })

    exposures = exposures.map(clean_missing)
    return exposures.drop_duplicates(subset=["exposure_id"])


def transform_samples(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Create a placeholder samples table linked to future AnnData files."""
    samples = pd.DataFrame({
        "sample_id": raw_df["submitter_id"] + "_SAMPLE",
        "patient_id": raw_df["submitter_id"],
        "sample_type": "Primary Tumor",
        "tissue_type": "Lung",
        "dataset_path": None,
    })

    return samples.drop_duplicates(subset=["sample_id"])


def load_table(df: pd.DataFrame, table_name: str, conn: sqlite3.Connection) -> None:
    """Load a cleaned dataframe into SQLite."""
    df.to_sql(table_name, conn, if_exists="append", index=False)


def run_etl() -> None:
    """Run the full clinical metadata ETL workflow."""
    raw_df = pd.read_csv(RAW_FILE, sep="\t")

    patients = transform_patients(raw_df)
    diagnoses = transform_diagnoses(raw_df)
    exposures = transform_exposures(raw_df)
    samples = transform_samples(raw_df)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("DELETE FROM samples")
        conn.execute("DELETE FROM exposures")
        conn.execute("DELETE FROM diagnoses")
        conn.execute("DELETE FROM patients")

        load_table(patients, "patients", conn)
        load_table(diagnoses, "diagnoses", conn)
        load_table(exposures, "exposures", conn)
        load_table(samples, "samples", conn)
        
    print("ETL complete.")
    print(f"Patients: {patients.shape}")
    print(f"Diagnoses: {diagnoses.shape}")
    print(f"Exposures: {exposures.shape}")
    print(f"Samples: {samples.shape}")


if __name__ == "__main__":
    run_etl()