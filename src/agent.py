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
from dotenv import load_dotenv
from anthropic import Anthropic
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


def ask_claude(user_question):
    system_prompt = """
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


if __name__ == "__main__":

    dataset_path = input("Enter path to .h5ad dataset or press Enter for demo PBMC dataset: ")

    try:
        if dataset_path.strip() == "":
            adata = load_dataset()
        else:
            adata = load_dataset(dataset_path)

    except FileNotFoundError:
        print("\nError: Dataset file not found.")
        exit()

    except OSError:
        print("\nError: File is not a valid .h5ad dataset.")
        exit()

    print("\nAvailable metadata columns:")
    print(list(adata.obs.columns))

    cluster_col = input("\nEnter cluster/cell type column to use or press Enter for 'louvain': ")

    if cluster_col.strip() == "":
        cluster_col = "louvain"

    if cluster_col not in adata.obs.columns:
        print(f"\nError: '{cluster_col}' not found in dataset metadata.")
        print("\nAvailable metadata columns:")
        print(list(adata.obs.columns))
        exit() 

    question = input("\nAsk a single-cell analysis question: ")
    command = ask_claude(question)

    print("\nClaude command:")
    print(command)

    try:
        if command.startswith("CALL_MARKERS:"):
            cluster = command.replace("CALL_MARKERS:", "").strip()
            markers = find_markers(adata, cluster, cluster_col=cluster_col)

            print(f"\nTop marker genes for {cluster}:")
            print(markers)

            markers.to_csv(f"outputs/markers_{cluster.replace(' ', '_')}.csv", index=False)
            print(f"\nSaved results to outputs/markers_{cluster.replace(' ', '_')}.csv")

        elif command.startswith("CALL_ALL_MARKERS"):
            markers = find_all_markers(adata, cluster_col=cluster_col)

            print("\nTop marker genes for all clusters:")
            print(markers)

            filename = "outputs/all_cluster_markers.csv"
            markers.to_csv(filename, index=False)

            print(f"\nSaved results to {filename}")    

        elif command.startswith("CALL_GENE:"):
            gene = command.replace("CALL_GENE:", "").strip()
            expression = query_gene_expression(adata, gene, cluster_col=cluster_col)

            print(f"\nAverage expression of {gene}:")
            print(expression)

            expression.to_csv(f"outputs/expression_{gene}.csv")
            print(f"\nSaved results to outputs/expression_{gene}.csv")

        elif command.startswith("CALL_DATASET_INFO"):
            info = get_dataset_info(adata)

            print("\nDataset information:")
            print(f"Cells: {info['cells']}")
            print(f"Genes: {info['genes']}")

            print("\nMetadata columns:")
            for col in info["metadata_columns"]:
                print(f"- {col}")    

        elif command.startswith("CALL_SUMMARY"):
            summary = get_cluster_summary(adata, cluster_col=cluster_col)

            print("\nCluster summary:")
            print(summary)

        elif command.startswith("CALL_UMAP"):
            result = plot_umap(adata, color_by=cluster_col)

            print("\nUMAP generation:")
            print(result)

        elif command.startswith("CALL_ANNOTATE"):
            import pandas as pd

            annotations = []

            clusters = adata.obs[cluster_col].unique()

            for cluster in clusters:
                print(f"\nAnnotating cluster: {cluster}")

                markers = find_markers(adata, cluster, cluster_col=cluster_col)
                top_genes = get_top_marker_genes(markers, n=10)

                predicted_cell_type = annotate_cluster_with_claude(top_genes)

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

        else:
            print("\nSorry, I could not identify which tool to use.")

    except KeyError as e:
        print(f"\nError: {e}")
        print("Please check the gene name, cluster name, or metadata column.")