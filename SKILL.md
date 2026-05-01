---
name: papersota
description: automate dataset-centric paper and sota metric surveys. use when the user asks about a research field, direction, paper, paper link, benchmark, dataset, algorithm comparison, or sota table. classify the input as field or direction, paper or paper link, or explicit dataset name; discover authoritative datasets when needed; verify dataset identity; collect papers that actually use the dataset; extract metrics from abstracts, html, or pdf full text; and generate markdown reports with metric explanations, bold best scores, numbered papers, and references.
---

# PaperSOTA

## Overview

PaperSOTA builds dataset-centric benchmark reports. It first classifies the user's input, then routes to a workflow that discovers datasets, verifies dataset identity, collects papers that actually use each dataset, extracts metric tables from accessible paper pages or PDFs, and produces a Markdown SOTA comparison report.

Default report language is Chinese, while table headers remain English (`Paper`, `KLD↓`, `SIM↑`, `NSS↑`, etc.). If the user asks entirely in English or explicitly requests English, generate the report in English.

## Input classification

Before searching, classify the user input into exactly one of these categories:

1. **Field or research direction**
   - Examples: `弱监督显著目标检测`, `medical image segmentation`, `remote sensing object detection`.
   - Action: discover 3-5 authoritative datasets by default, then run the dataset workflow for each dataset.
   - CLI default: `--max-datasets 5`.
2. **Paper, paper title, or paper link**
   - Examples: arXiv URL, DOI URL, OpenReview URL, ACL Anthology URL, paper title.
   - Action: fetch or infer the paper title and metadata, identify datasets used by the paper, then run the dataset workflow for each discovered dataset.
3. **Explicit dataset name**
   - Examples: `ImageNet`, `AGD20K`, `MIMIC-III`.
   - Action: verify the dataset identity, find papers that use the dataset, extract benchmark metrics, and generate the final report.

Ask a clarification only when classification is genuinely ambiguous or when multiple datasets share the same name/acronym and identity cannot be verified.

## Default dataset workflow

For each dataset:

1. **Verify dataset identity**
   - Find the official dataset name, aliases, homepage, benchmark page, and introducing paper when possible.
   - Flag acronym collisions and possible false positives.
2. **Collect candidate papers**
   - Default candidate count: 50 papers.
   - CLI parameter: `--candidate-paper 50`.
   - Search across scholarly sources such as OpenAlex, Semantic Scholar, Crossref, arXiv, DOI pages, benchmark pages, and paper pages when available.
3. **Confirm actual dataset usage**
   - Keep papers that clearly introduce, use, compare on, or evaluate with the dataset.
   - Drop or flag papers that merely mention the dataset without using it.
4. **Extract metrics**
   - Prefer full text or benchmark tables from HTML/PDF when accessible.
   - Use title/abstract metadata only for discovery, not for final metric claims.
   - If a metric value cannot be found, keep the paper row and write `—`; add a note: `metric not found in accessible text`.
5. **Build SOTA table**
   - Use `Paper` as the first column.
   - Use dataset metrics as remaining columns, preserving arrows such as `KLD↓`, `SIM↑`, `NSS↑`.
   - Bold the best score in each metric column. For `↓`, lower is better; for `↑`, higher is better.
   - Number papers as `[1]`, `[2]`, etc. and use the same numbers in references.
6. **Generate references**
   - Use a reasonable citation format: authors, title, venue, year, link.
   - Make every table citation number correspond exactly to one reference entry.

## CLI quick start

Use the bundled CLI when network access and Python execution are available:

```bash
python scripts/papersota.py "AGD20K" --candidate-paper 50 --out-dir ./papersota-agd20k
```

Field/direction mode:

```bash
python scripts/papersota.py "weakly supervised affordance grounding" \
  --input-type field \
  --max-datasets 5 \
  --candidate-paper 50 \
  --fulltext \
  --out-dir ./papersota-affordance
```

Paper/link mode:

```bash
python scripts/papersota.py "https://arxiv.org/abs/xxxx.xxxxx" \
  --input-type paper \
  --candidate-paper 50 \
  --fulltext \
  --out-dir ./papersota-from-paper
```

Dataset mode:

```bash
python scripts/papersota.py "ImageNet" \
  --input-type dataset \
  --candidate-paper 50 \
  --fulltext \
  --out-dir ./papersota-imagenet
```

## Report format

Follow `references/report-template.md`. At minimum, the report must include:

1. Dataset name.
2. Brief metric explanations.
3. Benchmark/algorithm comparison table with bold best values.
4. References whose numbering matches the paper IDs in the table.

Use `examples/agd20k-report.md` as the primary formatting example. It demonstrates metric explanations, multiple benchmark tables, best-score bolding, notes about comparability, and numbered references.

## Metric extraction rules

Use `references/extraction-schema.md` for structured extraction.

- Preserve metric direction arrows from the source table when possible.
- If the source says lower is better, render the metric as `Metric↓`; if higher is better, render as `Metric↑`.
- Only bold a value if it is the best within the same comparable table/split/protocol.
- Do not compare values across different protocols, splits, annotation regimes, or extra-training settings unless the report explicitly warns that they are not directly comparable.
- If protocols differ materially, split the results into separate tables, as in the AGD20K example.

## Quality checks

Before finalizing:

- Confirm the dataset identity and aliases.
- Deduplicate papers by DOI, arXiv ID, Semantic Scholar ID, normalized title, and URL.
- Separate introducing papers, baseline papers, and later algorithm papers.
- Confirm the paper actually uses the dataset, not just cites or mentions it.
- Verify metric directions before bolding best values.
- Add `—` for missing metrics and note `metric not found in accessible text`.
- Keep references in the same order as first appearance in the tables.

## Output files

The CLI should create:

- `input_classification.json`: detected input type and routing decision.
- `datasets.json`: discovered or verified datasets.
- `papers.json`: candidate and filtered papers.
- `metrics.json`: extracted metric records.
- `papersota-report.md`: final Markdown report.
- `notes.md`: limitations, false positives, missing full text, and extraction warnings.

## Limitations

PaperSOTA helps automate discovery and table construction, but final benchmark claims require manual review. Public APIs may miss papers. PDFs can be inaccessible, scanned, or difficult to parse. Some papers report metrics in figures, supplementary material, or external leaderboards rather than main tables.
