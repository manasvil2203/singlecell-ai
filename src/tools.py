import scanpy as sc


def load_dataset(filepath=None):
    """
    Load a single-cell dataset.

    If no filepath is provided, load the processed PBMC3K demo dataset.
    If a filepath is provided, load the user's .h5ad file.
    """
    if filepath is None:
        print("Loading demo PBMC dataset")
        adata = sc.datasets.pbmc3k_processed()
    else:
        print(f"Loading user dataset from: {filepath}")
        adata = sc.read_h5ad(filepath)

    return adata

def get_cluster_summary(adata, cluster_col="louvain"):
    """
    Return the number of cells in each cluster.
    """
    cluster_counts = adata.obs[cluster_col].value_counts().sort_index()
    return cluster_counts

def query_gene_expression(adata, gene, cluster_col="louvain"):
    """
    Return the average expression of a gene across clusters.
    """
    if gene not in adata.var_names:
        return f"Gene '{gene}' not found in dataset."

    gene_expression = adata[:, gene].to_df()
    gene_expression[cluster_col] = adata.obs[cluster_col].values

    avg_expression = gene_expression.groupby(cluster_col, observed=True)[gene].mean()
    avg_expression = avg_expression.sort_values(ascending=False)

    return avg_expression

def plot_umap(adata, color_by="louvain", output_file="outputs/umap.png"):
    """
    Generate and save a UMAP plot colored by a selected metadata column or gene.
    """
    sc.pl.umap(
        adata,
        color=color_by,
        save=False,
        show=False
    )

    import matplotlib.pyplot as plt
    plt.savefig(output_file, bbox_inches="tight", dpi=300)
    plt.close()

    return f"UMAP saved to {output_file}"

def find_markers(adata, group, cluster_col="louvain", n_genes=10):
    """
    Return top marker genes for a selected cluster.
    """
    sc.tl.rank_genes_groups(
        adata,
        groupby=cluster_col,
        groups=[group],
        reference="rest",
        method="wilcoxon"
    )

    markers = sc.get.rank_genes_groups_df(adata, group=group)
    markers = markers.head(n_genes)

    return markers[["names", "scores", "logfoldchanges", "pvals_adj"]]

def find_all_markers(adata, cluster_col="louvain", n_genes=10):
    """
    Return top marker genes for all clusters.
    """
    sc.tl.rank_genes_groups(
        adata,
        groupby=cluster_col,
        reference="rest",
        method="wilcoxon"
    )

    all_markers = sc.get.rank_genes_groups_df(adata, group=None)

    top_markers = (
        all_markers
        .groupby("group")
        .head(n_genes)
        .reset_index(drop=True)
    )

    return top_markers[["group", "names", "scores", "logfoldchanges", "pvals_adj"]]

def get_dataset_info(adata):
    """
    Return basic dataset information.
    """
    info = {
        "cells": adata.n_obs,
        "genes": adata.n_vars,
        "metadata_columns": list(adata.obs.columns)
    }

    return info

def get_top_marker_genes(markers_df, n=10):
    """
    Extract the top marker gene names from a marker gene dataframe.
    """
    return markers_df["names"].head(n).tolist()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Single-cell RNA-seq analysis tools"
    )

    parser.add_argument("--summary", action="store_true", help="Show cluster summary")
    parser.add_argument("--gene", type=str, help="Query average expression of a gene")
    parser.add_argument("--markers", type=str, help="Find marker genes for a cluster")
    parser.add_argument("--umap", type=str, help="Generate UMAP colored by metadata column or gene")

    args = parser.parse_args()

    adata = load_dataset()

    if args.summary:
        print("\nCluster summary:")
        print(get_cluster_summary(adata))

    if args.gene:
        print(f"\nAverage {args.gene} expression by cluster:")
        print(query_gene_expression(adata, args.gene))

    if args.markers:
        print(f"\nTop marker genes for {args.markers}:")
        print(find_markers(adata, args.markers))

    if args.umap:
        print("\nGenerating UMAP plot:")
        print(plot_umap(adata, color_by=args.umap))

    if not any([args.summary, args.gene, args.markers, args.umap]):
        print("No analysis selected. Try one of these:")
        print("python src/tools.py --summary")
        print("python src/tools.py --gene MS4A1")
        print('python src/tools.py --markers "B cells"')
        print("python src/tools.py --umap louvain")