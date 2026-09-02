from tools import (
    load_dataset,
    find_markers,
    find_all_markers,
    query_gene_expression,
    get_cluster_summary,
    plot_umap,
    get_dataset_info,
    get_top_marker_genes
)
import os
import sqlite3
from query_clinical_db import run_query, get_database_schema
from dotenv import load_dotenv
from anthropic import Anthropic
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


def ask_claude(user_question, clinical_schema=None):
    if clinical_schema is None:
        clinical_schema = """
patients(patient_id, age_at_diagnosis_days, sex, race, ethnicity, vital_status, days_to_death, days_to_last_follow_up)

diagnoses(diagnosis_id, patient_id, primary_diagnosis, tumor_stage, tumor_grade, days_to_diagnosis)

exposures(exposure_id, patient_id, smoking_status, years_smoked, cigarettes_per_day, pack_years_smoked)

samples(sample_id, patient_id, sample_type, tissue_type, dataset_path)
""".strip()
        
    system_prompt = f"""
You are a routing agent.

Available commands:

1. Marker genes

Return:

CALL_MARKERS:<cluster_name>

Examples:

User: Show me marker genes for B cells
Assistant: CALL_MARKERS:B cells

User: Find markers for CD4 T cells
Assistant: CALL_MARKERS:CD4 T cells

2. Marker genes for all clusters

Return:

CALL_ALL_MARKERS

Examples:

User: Give me marker genes for this dataset
Assistant: CALL_ALL_MARKERS

User: Find markers for all clusters
Assistant: CALL_ALL_MARKERS

User: What are the markers in this dataset?
Assistant: CALL_ALL_MARKERS

3. Gene expression

Return:

CALL_GENE:<gene_name>

Examples:

User: Which clusters express MS4A1?
Assistant: CALL_GENE:MS4A1

User: Show expression of CD79A
Assistant: CALL_GENE:CD79A

4. Cluster summary

Return:

CALL_SUMMARY

Examples:

User: How many clusters are in this dataset?
Assistant: CALL_SUMMARY

User: Give me a summary of the cell populations
Assistant: CALL_SUMMARY

5. UMAP visualization

Return:

CALL_UMAP

Examples:

User: Show me a UMAP
Assistant: CALL_UMAP

User: Generate a UMAP plot
Assistant: CALL_UMAP

User: Visualize the clusters
Assistant: CALL_UMAP

6. Unclear request

If the user request is vague, unclear, or does not match any available tool, return:

CALL_UNKNOWN

Examples:

User: what is going on
Assistant: CALL_UNKNOWN

User: help
Assistant: CALL_UNKNOWN

User: do something
Assistant: CALL_UNKNOWN

7. Dataset information

Return:

CALL_DATASET_INFO

Examples:

User: Tell me about this dataset
Assistant: CALL_DATASET_INFO

User: How many cells and genes are there?
Assistant: CALL_DATASET_INFO

User: What metadata columns are available?
Assistant: CALL_DATASET_INFO

8. Automatic cluster annotation

Return:

CALL_ANNOTATE

Examples:

User: Annotate my clusters
Assistant: CALL_ANNOTATE

User: Predict cell types for this dataset
Assistant: CALL_ANNOTATE

9. CALL_SQL:<sql_query>

Use CALL_SQL when the user asks about clinical metadata, patients, diagnosis, smoking status, vital status, race, ethnicity, age, samples, or follow-up.

Clinical database schema:

{clinical_schema}

Return only:
CALL_SQL:<sql_query>

Return ONLY the command.
Do not explain anything.
If the request is unclear, return CALL_UNKNOWN.
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": user_question
            }
        ]
    )

    return response.content[0].text.strip()

def annotate_cluster_with_claude(marker_genes):
    """
    Use Claude to suggest a likely broad cell type from marker genes.
    """

    marker_text = ", ".join(marker_genes)

    prompt = f"""
You are helping annotate single-cell RNA-seq clusters.

Given these marker genes:

{marker_text}

Suggest the most likely cell type based only on these marker genes.
Be as specific as the marker evidence allows.
If the markers are ambiguous, return a broad cell type.
If the markers are not enough, return "Unknown".
Return only the cell type name.
Do not explain.

"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text.strip()


def run_single_cell_session():
    """
    Load a single-cell dataset once and allow the user to ask
    multiple analysis questions during the same session.
    """

    dataset_path = input(
        "\nEnter path to .h5ad dataset or press Enter for demo PBMC dataset: "
    )

    try:
        if dataset_path.strip() == "":
            adata = load_dataset()
        else:
            adata = load_dataset(dataset_path)

    except FileNotFoundError:
        print("\nError: Dataset file not found.")
        return

    except OSError:
        print("\nError: File is not a valid .h5ad dataset.")
        return

    print("\nDataset loaded successfully.")

    info = get_dataset_info(adata)
    print(f"Cells: {info['cells']}")
    print(f"Genes: {info['genes']}")

    print("\nAvailable metadata columns:")
    print(list(adata.obs.columns))

    cluster_col = input(
        "\nEnter cluster/cell type column to use or press Enter for 'louvain': "
    )

    if cluster_col.strip() == "":
        cluster_col = "louvain"

    if cluster_col not in adata.obs.columns:
        print(f"\nError: '{cluster_col}' not found in dataset metadata.")
        print("\nAvailable metadata columns:")
        print(list(adata.obs.columns))
        return

    print("\nSingle-cell analysis session started.")
    print("Ask questions about the loaded dataset.")
    print("Type 'exit' when you are finished.")

    while True:

        question = input("\nAsk a single-cell question: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("\nLeaving single-cell analysis session.")
            break

        if not question:
            continue

        command = ask_claude(question)

        print("\nClaude command:")
        print(command)

        try:
            if command.startswith("CALL_MARKERS:"):
                cluster = command.replace("CALL_MARKERS:", "").strip()
                markers = find_markers(
                    adata,
                    cluster,
                    cluster_col=cluster_col
                )

                print(f"\nTop marker genes for {cluster}:")
                print(markers)

                filename = f"outputs/markers_{cluster.replace(' ', '_')}.csv"
                markers.to_csv(filename, index=False)
                print(f"\nSaved results to {filename}")

            elif command.startswith("CALL_ALL_MARKERS"):
                markers = find_all_markers(
                    adata,
                    cluster_col=cluster_col
                )

                print("\nTop marker genes for all clusters:")
                print(markers)

                filename = "outputs/all_cluster_markers.csv"
                markers.to_csv(filename, index=False)
                print(f"\nSaved results to {filename}")

            elif command.startswith("CALL_GENE:"):
                gene = command.replace("CALL_GENE:", "").strip()

                expression = query_gene_expression(
                    adata,
                    gene,
                    cluster_col=cluster_col
                )

                print(f"\nAverage expression of {gene}:")
                print(expression)

                filename = f"outputs/expression_{gene}.csv"
                expression.to_csv(filename)
                print(f"\nSaved results to {filename}")

            elif command.startswith("CALL_DATASET_INFO"):
                info = get_dataset_info(adata)

                print("\nDataset information:")
                print(f"Cells: {info['cells']}")
                print(f"Genes: {info['genes']}")

                print("\nMetadata columns:")
                for col in info["metadata_columns"]:
                    print(f"- {col}")

            elif command.startswith("CALL_SUMMARY"):
                summary = get_cluster_summary(
                    adata,
                    cluster_col=cluster_col
                )

                print("\nCluster summary:")
                print(summary)

            elif command.startswith("CALL_UMAP"):
                result = plot_umap(
                    adata,
                    color_by=cluster_col
                )

                print("\nUMAP generation:")
                print(result)

            elif command.startswith("CALL_ANNOTATE"):
                import pandas as pd

                annotations = []

                clusters = adata.obs[cluster_col].unique()

                for cluster in clusters:
                    print(f"\nAnnotating cluster: {cluster}")

                    markers = find_markers(
                        adata,
                        cluster,
                        cluster_col=cluster_col
                    )

                    top_genes = get_top_marker_genes(markers, n=10)

                    predicted_cell_type = annotate_cluster_with_claude(
                        top_genes
                    )

                    annotations.append({
                        "cluster": cluster,
                        "top_marker_genes": ", ".join(top_genes),
                        "predicted_cell_type": predicted_cell_type
                    })

                    print(f"Top genes: {top_genes}")
                    print(f"Predicted cell type: {predicted_cell_type}")

                annotations_df = pd.DataFrame(annotations)

                print("\nCluster annotations:")
                print(annotations_df)

                filename = "outputs/cluster_annotations.csv"
                annotations_df.to_csv(filename, index=False)

                print(f"\nSaved results to {filename}")

            elif command.startswith("CALL_UNKNOWN"):
                print("\nI could not tell which analysis you wanted.")
                print("Try asking something like:")
                print("- Give me a cluster summary")
                print("- Show marker genes for B cells")
                print("- Which clusters express MS4A1?")
                print("- Show me a UMAP")

            elif command.startswith("CALL_SQL:"):
                print(
                    "\nThis is a clinical-data question. "
                    "Please use the clinical analysis mode."
                )

            else:
                print("\nSorry, I could not identify which tool to use.")

        except KeyError as e:
            print(f"\nError: {e}")
            print(
                "Please check the gene name, cluster name, "
                "or metadata column."
            )

def run_clinical_session():
    """
    Allow the user to ask multiple clinical questions
    during the same session.
    """

    print("\nClinical analysis session started.")

    db_input = input(
        "\nEnter path to SQLite clinical database "
        "or press Enter for demo TCGA-LUAD database: "
    ).strip()

    if db_input == "":
        db_path = Path("data/clinical_luad.db")
        print("\nUsing demo TCGA-LUAD clinical database.")
    else:
        db_path = Path(db_input)
        print(f"\nUsing clinical database: {db_path}")

    if not db_path.exists():
        print(f"\nDatabase file not found: {db_path}")
        return   

    clinical_schema = get_database_schema(db_path)

    print("\nDetected database schema:")
    print(clinical_schema)   

    print("Type 'exit' when you are finished.")
    
    while True:

        question = input("\nAsk a clinical data question: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("\nLeaving clinical analysis session.")
            break

        if not question:
            continue

        command = ask_claude(
            question,
            clinical_schema=clinical_schema
        )

        print("\nClaude command:")
        print(command)

        if command.startswith("CALL_SQL:"):
            try:
                sql_query = command.replace("CALL_SQL:", "").strip()
                results = run_query(sql_query, db_path=db_path)

                print("\nClinical database results:")
                print(results)

                output_path = "outputs/clinical_query_results.csv"
                results.to_csv(output_path, index=False)

                print(f"\nResults saved to: {output_path}")

            except (ValueError, sqlite3.Error) as e:
                print(f"\nClinical query error: {e}")

        elif command.startswith("CALL_UNKNOWN"):
            print("\nI could not tell which clinical analysis you wanted.")
            print("Try asking something like:")
            print("- Show me all alive patients")
            print("- How many patients are in the database?")
            print("- Show patients with stage II disease")

        else:
            print(
                "\nThat question does not appear to be a clinical-data request."
            )

if __name__ == "__main__":

    Path("outputs").mkdir(parents=True, exist_ok=True)

    print("\nWelcome to SingleCell-AI")
    print("\nWhat would you like to analyze?")
    print("1. Single-cell RNA-seq data")
    print("2. Clinical data")
    print("3. Exit")

    choice = input("\nSelect an option: ").strip()

    if choice == "1":
        run_single_cell_session()

    elif choice == "2":
        run_clinical_session()

    elif choice == "3":
        print("\nGoodbye.")

    else:
        print("\nInvalid option. Please run the program again.")