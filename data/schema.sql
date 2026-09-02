CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    age_at_diagnosis_days INTEGER,
    sex TEXT,
    race TEXT,
    ethnicity TEXT,
    vital_status TEXT,
    days_to_death INTEGER,
    days_to_last_follow_up INTEGER
);

CREATE TABLE IF NOT EXISTS diagnoses (
    diagnosis_id TEXT PRIMARY KEY,
    patient_id TEXT,
    primary_diagnosis TEXT,
    tumor_stage TEXT,
    tumor_grade TEXT,
    days_to_diagnosis INTEGER,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS exposures (
    exposure_id TEXT PRIMARY KEY,
    patient_id TEXT,
    smoking_status TEXT,
    years_smoked INTEGER,
    cigarettes_per_day REAL,
    pack_years_smoked REAL,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id TEXT PRIMARY KEY,
    patient_id TEXT,
    sample_type TEXT,
    tissue_type TEXT,
    dataset_path TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);