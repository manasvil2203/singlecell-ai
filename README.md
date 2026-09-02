# SingleCell-AI

An AI-powered copilot for single-cell RNA-seq and clinical data analysis built with Python, Scanpy, SQLite, and Anthropic's Claude API.

Instead of generating biological answers directly, the agent acts as an interpretation and orchestration layer between natural language queries and analysis tools. Single-cell analyses are performed on the loaded dataset using Scanpy, while clinical questions are translated into SQL queries and executed against a structured clinical database. This ensures that results are derived from the underlying data rather than from the LLM's internal knowledge.

---

## Features

* Load user-provided `.h5ad` datasets or use a demo PBMC dataset

* Configurable cluster/cell-type metadata columns

* Persistent multi-question analysis sessions

* Dataset information and metadata inspection

* Cluster summaries

* Marker gene analysis for individual clusters

* Dataset-wide marker gene analysis

* Gene expression queries across clusters

* UMAP visualization

* Preliminary LLM-assisted cluster annotation

* Clinical metadata querying using natural language

* SQLite-based clinical database

* TCGA-LUAD clinical metadata extraction and transformation pipeline

* User-provided SQLite database support

* Automatic SQLite schema inspection

* Dynamic schema-aware SQL generation

* Read-only clinical SQL execution

* Automatic routing between single-cell and clinical analysis tools

* Automatic saving of results and figures

* Basic error handling for invalid files, metadata columns, genes, clusters, database paths, and clinical queries

---

## Automatic Cluster Annotation

The agent can perform preliminary cluster annotation using marker genes.

When the user asks:

```text
Annotate my clusters
```

the workflow is:

```text
Cluster
    ↓
Marker gene identification (Scanpy)
    ↓
Top marker genes
    ↓
Claude interpretation
    ↓
Predicted cell type
```

Predicted annotations are saved to:

```text
outputs/cluster_annotations.csv
```

Cluster annotation is intended as a starting point for interpretation rather than a replacement for expert review or reference-based annotation.

A major future direction is to move toward reference-grounded annotation using established cell-type references and annotation frameworks rather than relying primarily on LLM interpretation of marker genes.

---

## Clinical Data Analysis

The project includes a clinical metadata layer built using public TCGA Lung Adenocarcinoma (TCGA-LUAD) data obtained through the NCI Genomic Data Commons API.

The clinical ETL pipeline downloads and restructures metadata for 585 TCGA-LUAD cases into four SQLite tables:

```text
patients
diagnoses
exposures
samples
```

The database contains patient demographics and outcomes, diagnosis information including AJCC pathologic stage, smoking and exposure metadata, and a sample table designed to support future connections between clinical records and molecular datasets.

Clinical questions can be asked using natural language. For example:

```text
How many patients are alive?
```

The workflow is:

```text
Clinical Question
      ↓
Claude Interpretation
      ↓
SQL Query
      ↓
SQLite Clinical Database
      ↓
Data-Derived Result
```

The generated SQL is executed against the local clinical database and the results are saved to:

```text
outputs/clinical_query_results.csv
```

Clinical analysis is not restricted to the included TCGA-LUAD database. Users can provide another SQLite database when starting a clinical session. SingleCell-AI automatically inspects the database tables and columns and provides the detected schema to Claude for SQL formulation.

For example:

```text
Selected SQLite Database
        ↓
Automatic Schema Inspection
        ↓
Claude SQL Formulation
        ↓
Read-Only SQLite Execution
        ↓
Data-Derived Result
```

This allows the clinical workflow to operate on previously unseen database schemas without hardcoding table or column names.

The clinical and single-cell components currently operate as separate data sources. Patient-level linkage between clinical metadata and molecular datasets is planned as a future extension.

---

## Project Structure

```text
singlecell-ai/
├── src/
│   ├── agent.py
│   ├── tools.py
│   ├── download_tcga_luad.py
│   ├── build_clinical_db.py
│   ├── etl_clinical.py
│   └── query_clinical_db.py
├── data/
│   └── schema.sql
├── outputs/
├── .env
├── .gitignore
├── environment.yml
└── README.md
```

Downloaded clinical data, generated SQLite databases, `.h5ad` datasets, API credentials, and analysis outputs are excluded from version control.

---

## Example Questions

```text
Tell me about this dataset

Give me a cluster summary

Show me marker genes for B cells

Find markers for all clusters

Which clusters express MS4A1?

Show me a UMAP

Annotate my clusters

How many patients are alive?

How many patients are in the clinical database?

What tumor stages are represented?

How many alive patients have a recorded smoking status?
```

---

## How It Works

```text
                         User Question
                              ↓
                         Claude
                         ↙    ↘
                Single-Cell   Clinical
                    Tool        SQL
                     ↓           ↓
                   Scanpy      SQLite
                     ↓           ↓
                 .h5ad Data   Clinical Database
                         ↘     ↙
                       Data-Derived
                          Result
```

The LLM determines which analysis pathway and tool to use. For single-cell analysis, biological computations are performed using Scanpy on the loaded dataset. For clinical analysis, Claude formulates SQL using the detected database schema, while SQLite executes the query against the underlying records.

The LLM therefore acts as an interpretation and orchestration layer rather than as the source of the scientific results.

---

## Clinical Data Pipeline

The TCGA-LUAD clinical database can be recreated from the source data using the included scripts.

Download the clinical metadata:

```bash
python src/download_tcga_luad.py
```

Build the empty SQLite database:

```bash
python src/build_clinical_db.py
```

Transform and load the clinical metadata:

```bash
python src/etl_clinical.py
```

The ETL workflow cleans GDC missing values, restructures nested clinical fields, and loads the transformed records into the relational database defined by `data/schema.sql`.

---

## Installation

Clone the repository:

```bash
git clone <repository_url>
cd singlecell-ai
```

Create the environment:

```bash
conda env create -f environment.yml
conda activate sc_agent
```

Create a `.env` file and add your Anthropic API key:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

Run the agent:

```bash
python src/agent.py
```

The agent will prompt you to choose between single-cell and clinical analysis.

For single-cell analysis, you can provide a `.h5ad` file or use the included demo workflow.

For clinical analysis, you can provide a SQLite database path or use the default TCGA-LUAD database.

---

## Future Directions

* Reference-grounded cluster annotation using established cell-type references rather than relying primarily on LLM interpretation

* Integration with annotation frameworks such as CellTypist and celldex

* Tissue-specific reference datasets for more biologically informed annotation

* Differential expression analysis

* Heatmap generation and additional visualization tools

* Deterministic grounding of natural-language terms to categorical values stored in clinical databases

* Patient-level linkage between clinical metadata and molecular datasets

* Clinical cohort selection followed by downstream single-cell or molecular analysis

* Support for additional TCGA cancer cohorts

* More advanced clinical and molecular query workflows

* Stronger validation and safety controls for LLM-generated SQL