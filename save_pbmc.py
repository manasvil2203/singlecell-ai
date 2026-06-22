import scanpy as sc

adata = sc.datasets.pbmc3k_processed()

adata.write("pbmc_test.h5ad")

print("Saved pbmc_test.h5ad")