# SingleCell-AI

An AI-powered copilot for single-cell RNA-seq analysis built with Python, Scanpy, and Anthropic's Claude API.

Instead of generating biological answers directly, the agent acts as a routing layer between natural language queries and analysis tools. All analyses are performed on the loaded dataset using Scanpy, ensuring that results are data-driven rather than based on the LLM's internal knowledge.

---

## Features

* Load user-provided `.h5ad` datasets or use a demo PBMC dataset
* Configurable cluster/cell-type metadata columns
* Dataset information and metadata inspection
* Cluster summaries
* Marker gene analysis for individual clusters
* Dataset-wide marker gene analysis
* Gene expression queries across clusters
* UMAP visualization
* Automatic cluster annotation
* Automatic saving of results and figures
* Basic error handling for invalid files, metadata columns, genes, and clusters

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

---

## Project Structure

```text
singlecell-ai/
├── src/
│   ├── agent.py
│   └── tools.py
├── outputs/
├── .env
├── .gitignore
├── environment.yml
└── README.md
```

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
```

---

## How It Works

```text
User Question
        ↓
Claude Router
        ↓
Command
        ↓
Python Tool
        ↓
Scanpy Analysis
        ↓
Dataset-Derived Result
```

The LLM determines which analysis tool to use, while all computations are performed using Scanpy on the loaded dataset.

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

---

## Future Directions

* Differential expression analysis
* Reference-based cluster annotation
* Heatmap generation
* Multi-question conversational sessions
* Additional visualization tools
* Support for tissue-specific reference datasets
* Integration with external annotation frameworks such as CellTypist and celldex
