# PaperSOTA extraction schema

Use this schema for each dataset, paper, and metric record.

## Input classification

```json
{
  "input": "string",
  "input_type": "field | paper | dataset | ambiguous",
  "language": "zh | en",
  "reason": "string",
  "next_action": "discover_datasets | extract_datasets_from_paper | verify_dataset"
}
```

## Dataset record

```json
{
  "dataset_name": "string",
  "aliases": ["string"],
  "domain": "string or null",
  "tasks": ["string"],
  "official_url": "string or null",
  "benchmark_url": "string or null",
  "introducing_paper": "string or null",
  "verification_status": "verified | likely | ambiguous | not_found",
  "verification_notes": "string"
}
```

## Paper record

```json
{
  "paper_id": 1,
  "short_title": "string",
  "title": "string",
  "authors": ["string"],
  "venue": "string or null",
  "year": "integer or null",
  "url": "string or null",
  "doi": "string or null",
  "arxiv_id": "string or null",
  "dataset_usage": "introduces_dataset | uses_dataset | compares_on_dataset | mentions_only | unclear",
  "usage_evidence": "string",
  "include_in_table": true,
  "notes": "string"
}
```

## Metric record

```json
{
  "paper_id": 1,
  "paper_label": "ShortTitle, VenueYear [1]",
  "dataset_name": "string",
  "protocol": "string",
  "split": "string or null",
  "metric": "KLD↓",
  "metric_name": "KLD",
  "direction": "lower | higher | unknown",
  "value": "number or null",
  "display_value": "string",
  "evidence": "string",
  "source_url": "string or null",
  "confidence": "high | medium | low",
  "notes": "string"
}
```

If the metric value is unavailable, use `null` and render `—` in the Markdown table. Add the note `metric not found in accessible text`.
