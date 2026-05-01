#!/usr/bin/env python3
"""PaperSOTA CLI: dataset-centric paper and SOTA table scaffolding.

This CLI intentionally avoids API keys. It performs public scholarly API search,
lightweight page/PDF text retrieval, heuristic dataset verification, and Markdown
report scaffolding. It is designed to support ChatGPT/manual review, not replace it.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

USER_AGENT = "PaperSOTA/0.2 (research survey tool; no API key)"
TIMEOUT = 25
METRIC_RE = re.compile(r"\b([A-Z][A-Z0-9_\-]{1,12}|mAP|IoU|F1|AUC|ACC|RMSE|MAE|BLEU|ROUGE|KLD|SIM|NSS)\s*(?:[↑↓])?\s*[:=]?\s*(-?\d+(?:\.\d+)?)")
URL_RE = re.compile(r"https?://\S+", re.I)

FIELD_HINTS = [
    "segmentation", "detection", "classification", "retrieval", "tracking", "grounding", "saliency",
    "medical", "remote sensing", "nlp", "vision", "recommendation", "weakly supervised", "affordance",
    "显著", "检测", "分割", "分类", "定位", "医学", "遥感", "弱监督", "可供性",
]
DATASET_HINTS = ["dataset", "benchmark", "challenge", "数据集", "基准"]
PAPER_HINTS = ["arxiv.org", "doi.org", "openreview.net", "aclanthology.org", "paper", "论文"]


class TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self.in_script = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.in_script = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.in_script = False

    def handle_data(self, data: str) -> None:
        if not self.in_script and data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def http_text(url: str, binary: bool = False) -> Optional[Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
            if binary:
                return data
            return data.decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"warning: failed request: {url} ({exc})", file=sys.stderr)
        return None


def http_json(url: str) -> Optional[Dict[str, Any]]:
    text = http_text(url)
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception as exc:
        print(f"warning: json parse failed for {url}: {exc}", file=sys.stderr)
        return None


def normalize_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title or "").strip().lower()
    return re.sub(r"[^a-z0-9 ]+", "", title)


def slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    return s[:80] or "papersota"


def detect_language(text: str) -> str:
    zh_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin_words = len(re.findall(r"\b[a-zA-Z]{3,}\b", text))
    return "zh" if zh_chars > latin_words else "en"


def classify_input(text: str, explicit: str = "auto") -> Dict[str, str]:
    if explicit != "auto":
        action = {"field": "discover_datasets", "paper": "extract_datasets_from_paper", "dataset": "verify_dataset"}.get(explicit, "verify_dataset")
        return {"input": text, "input_type": explicit, "language": detect_language(text), "reason": "explicit --input-type", "next_action": action}
    t = text.strip()
    lower = t.lower()
    if URL_RE.search(t) or any(h in lower for h in PAPER_HINTS):
        return {"input": text, "input_type": "paper", "language": detect_language(text), "reason": "paper URL/title hint detected", "next_action": "extract_datasets_from_paper"}
    if any(h in lower for h in FIELD_HINTS) and len(t.split()) >= 2:
        return {"input": text, "input_type": "field", "language": detect_language(text), "reason": "field/task phrase detected", "next_action": "discover_datasets"}
    return {"input": text, "input_type": "dataset", "language": detect_language(text), "reason": "short specific term treated as dataset", "next_action": "verify_dataset"}


def search_openalex(query: str, per_page: int = 25) -> List[Dict[str, Any]]:
    params = urllib.parse.urlencode({"search": query, "per-page": min(per_page, 50)})
    data = http_json(f"https://api.openalex.org/works?{params}")
    out: List[Dict[str, Any]] = []
    if not data:
        return out
    for item in data.get("results", []):
        authors = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])]
        venue = ((item.get("primary_location") or {}).get("source") or {}).get("display_name")
        abstract = inverted_abstract(item.get("abstract_inverted_index") or {})
        doi = item.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        out.append({
            "source": "openalex", "title": item.get("title") or "", "authors": [a for a in authors if a],
            "venue": venue, "year": item.get("publication_year"), "url": item.get("id"), "doi": doi,
            "abstract": abstract, "ids": {"openalex_id": item.get("id")},
        })
    return out


def inverted_abstract(index: Dict[str, List[int]]) -> str:
    pairs: List[Tuple[int, str]] = []
    for word, positions in index.items():
        for pos in positions:
            pairs.append((pos, word))
    return " ".join(w for _, w in sorted(pairs))


def search_semantic_scholar(query: str, limit: int = 25) -> List[Dict[str, Any]]:
    fields = "title,year,authors,venue,url,abstract,externalIds"
    params = urllib.parse.urlencode({"query": query, "limit": min(limit, 100), "fields": fields})
    data = http_json(f"https://api.semanticscholar.org/graph/v1/paper/search?{params}")
    out: List[Dict[str, Any]] = []
    if not data:
        return out
    for item in data.get("data", []):
        ext = item.get("externalIds") or {}
        out.append({
            "source": "semantic_scholar", "title": item.get("title") or "",
            "authors": [a.get("name", "") for a in item.get("authors", []) if a.get("name")],
            "venue": item.get("venue"), "year": item.get("year"), "url": item.get("url"),
            "doi": ext.get("DOI"), "abstract": item.get("abstract") or "",
            "ids": {"semantic_scholar_id": item.get("paperId"), "arxiv_id": ext.get("ArXiv")},
        })
    return out


def search_arxiv(query: str, max_results: int = 25) -> List[Dict[str, Any]]:
    params = urllib.parse.urlencode({"search_query": f'all:"{query}"', "start": 0, "max_results": min(max_results, 50), "sortBy": "relevance"})
    text = http_text(f"https://export.arxiv.org/api/query?{params}")
    out: List[Dict[str, Any]] = []
    if not text:
        return out
    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(text)
    except Exception:
        return out
    for entry in root.findall("a:entry", ns):
        title = re.sub(r"\s+", " ", entry.findtext("a:title", default="", namespaces=ns)).strip()
        abstract = re.sub(r"\s+", " ", entry.findtext("a:summary", default="", namespaces=ns)).strip()
        url = entry.findtext("a:id", default=None, namespaces=ns)
        year = None
        published = entry.findtext("a:published", default="", namespaces=ns)
        if published[:4].isdigit():
            year = int(published[:4])
        authors = [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)]
        out.append({"source": "arxiv", "title": title, "authors": authors, "venue": "arXiv", "year": year, "url": url, "doi": None, "abstract": abstract, "ids": {"arxiv_id": url.rsplit('/', 1)[-1] if url else None}})
    return out


def dedupe(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for rec in records:
        key = rec.get("doi") or rec.get("ids", {}).get("arxiv_id") or normalize_title(rec.get("title", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(rec)
    return out


def discover_datasets(field: str, max_datasets: int) -> List[Dict[str, Any]]:
    queries = [f"{field} dataset benchmark", f"{field} survey datasets", f"{field} challenge benchmark"]
    candidates: Dict[str, Dict[str, Any]] = {}
    for q in queries:
        for rec in search_openalex(q, 20) + search_semantic_scholar(q, 20):
            text = f"{rec.get('title','')} {rec.get('abstract','')}"
            for name in extract_dataset_names(text):
                if name.lower() not in candidates:
                    candidates[name.lower()] = {"dataset_name": name, "aliases": [name], "domain": field, "tasks": [], "official_url": None, "benchmark_url": None, "introducing_paper": rec.get("title"), "verification_status": "likely", "verification_notes": f"discovered from {rec.get('source')} query: {q}"}
        time.sleep(0.2)
    return list(candidates.values())[:max_datasets]


def extract_dataset_names(text: str) -> List[str]:
    names: List[str] = []
    patterns = [
        r"\b([A-Z][A-Za-z0-9\-]{2,20}(?:-[A-Z0-9]{2,10})?)\s+(?:dataset|benchmark|challenge)\b",
        r"\b([A-Z]{2,}[0-9]{0,4}[A-Z]?)\b",
        r"([\u4e00-\u9fffA-Za-z0-9\-]{2,30})数据集",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            name = m.group(1).strip()
            if 2 <= len(name) <= 40 and name.lower() not in {"the", "and", "with", "this", "from"}:
                names.append(name)
    out = []
    for n in names:
        if n not in out:
            out.append(n)
    return out[:10]


def verify_dataset(name: str) -> Dict[str, Any]:
    query = f"{name} dataset benchmark"
    papers = dedupe(search_openalex(query, 10) + search_semantic_scholar(query, 10) + search_arxiv(query, 10))
    aliases = [name]
    intro = papers[0].get("title") if papers else None
    status = "verified" if papers else "not_found"
    notes = "verified by scholarly search candidates" if papers else "no public scholarly candidates found; manual verification needed"
    return {"dataset_name": name, "aliases": aliases, "domain": None, "tasks": [], "official_url": None, "benchmark_url": None, "introducing_paper": intro, "verification_status": status, "verification_notes": notes}


def extract_title_from_url_or_text(text: str) -> Tuple[str, str]:
    url_match = URL_RE.search(text)
    if not url_match:
        return text.strip(), text.strip()
    url = url_match.group(0).rstrip(").,]")
    page = http_text(url)
    if not page:
        return url, ""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else url
    parser = TextHTMLParser()
    try:
        parser.feed(page)
        body = parser.text()
    except Exception:
        body = page[:5000]
    return title, body[:20000]


def datasets_from_paper(text: str) -> List[Dict[str, Any]]:
    title, body = extract_title_from_url_or_text(text)
    found = extract_dataset_names(f"{title} {body}")
    out = []
    for name in found[:8]:
        ds = verify_dataset(name)
        ds["verification_notes"] += f"; extracted from paper/page title: {title}"
        out.append(ds)
    if not out:
        # Fallback: search the paper title and infer dataset names from abstracts.
        for rec in search_openalex(title, 5) + search_semantic_scholar(title, 5):
            for name in extract_dataset_names(f"{rec.get('title','')} {rec.get('abstract','')}"):
                out.append(verify_dataset(name))
    return out[:5]


def collect_papers_for_dataset(dataset: Dict[str, Any], candidate_count: int) -> List[Dict[str, Any]]:
    name = dataset["dataset_name"]
    aliases = dataset.get("aliases") or [name]
    queries = []
    for a in aliases:
        queries += [a, f"{a} benchmark", f"{a} state of the art", f"{a} sota", f"{a} baseline"]
    records: List[Dict[str, Any]] = []
    per_query = max(8, min(30, candidate_count // max(1, len(queries)) + 5))
    for q in queries:
        records += search_openalex(q, per_query)
        records += search_semantic_scholar(q, per_query)
        records += search_arxiv(q, per_query)
        records = dedupe(records)[:candidate_count]
        if len(records) >= candidate_count:
            break
        time.sleep(0.2)
    usage_pat = re.compile("|".join(re.escape(a) for a in aliases), re.I)
    filtered = []
    for i, rec in enumerate(dedupe(records), 1):
        text = f"{rec.get('title','')} {rec.get('abstract','')}"
        usage = "uses_dataset" if usage_pat.search(text) else "unclear"
        rec.update({"paper_id": i, "short_title": short_title(rec.get("title", "")), "dataset_usage": usage, "usage_evidence": text[:400], "include_in_table": usage != "mentions_only", "notes": ""})
        filtered.append(rec)
    return filtered[:candidate_count]


def short_title(title: str) -> str:
    title = re.sub(r"[:：].*$", "", title).strip()
    words = title.split()
    if len(words) <= 5:
        return title[:60]
    # If title has an acronym-like method, use it.
    for w in words:
        if re.fullmatch(r"[A-Z][A-Za-z0-9\-]{2,15}", w):
            return w
    return " ".join(words[:5])


def fetch_accessible_text(rec: Dict[str, Any], cache_dir: Path, fulltext: bool) -> str:
    text = f"{rec.get('title','')}\n{rec.get('abstract','')}"
    if not fulltext:
        return text
    url = rec.get("url")
    if not url:
        return text
    page = http_text(url)
    if page:
        parser = TextHTMLParser()
        try:
            parser.feed(page)
            body = parser.text()
            text += "\n" + body[:50000]
        except Exception:
            text += "\n" + page[:20000]
    # arXiv PDF fallback.
    arxiv_id = rec.get("ids", {}).get("arxiv_id")
    if arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        pdf_data = http_text(pdf_url, binary=True)
        if pdf_data:
            pdf_path = cache_dir / f"{slug(arxiv_id)}.pdf"
            pdf_path.write_bytes(pdf_data)
            text += f"\n[PDF downloaded to {pdf_path}; install pdftotext/pdfplumber to extract tables if needed]"
    return text


def extract_metrics_for_papers(dataset_name: str, papers: List[Dict[str, Any]], cache_dir: Path, fulltext: bool) -> List[Dict[str, Any]]:
    metrics: List[Dict[str, Any]] = []
    for rec in papers:
        source_text = fetch_accessible_text(rec, cache_dir, fulltext)
        found = list(METRIC_RE.finditer(source_text))[:20]
        if not found:
            metrics.append({"paper_id": rec["paper_id"], "paper_label": paper_label(rec), "dataset_name": dataset_name, "protocol": "default", "split": None, "metric": "metric", "metric_name": "metric", "direction": "unknown", "value": None, "display_value": "—", "evidence": "", "source_url": rec.get("url"), "confidence": "low", "notes": "metric not found in accessible text"})
            continue
        seen = set()
        for m in found:
            metric = m.group(1)
            value = float(m.group(2))
            if metric in seen:
                continue
            seen.add(metric)
            direction = infer_metric_direction(metric)
            label = metric + ("↓" if direction == "lower" else "↑" if direction == "higher" else "")
            metrics.append({"paper_id": rec["paper_id"], "paper_label": paper_label(rec), "dataset_name": dataset_name, "protocol": "default", "split": None, "metric": label, "metric_name": metric, "direction": direction, "value": value, "display_value": str(value), "evidence": source_text[max(0, m.start()-120):m.end()+120], "source_url": rec.get("url"), "confidence": "medium", "notes": "heuristically extracted; verify against source table"})
    return metrics


def infer_metric_direction(metric: str) -> str:
    m = metric.lower()
    if m in {"kld", "kl", "mae", "rmse", "mse", "loss", "error", "wer", "perplexity"}:
        return "lower"
    if m in {"sim", "nss", "map", "iou", "f1", "auc", "acc", "accuracy", "bleu", "rouge"}:
        return "higher"
    return "unknown"


def paper_label(rec: Dict[str, Any]) -> str:
    venue = rec.get("venue") or ""
    year = rec.get("year") or ""
    suffix = f", {venue}{year}" if venue or year else ""
    return f"{rec.get('short_title') or short_title(rec.get('title',''))}{suffix} [{rec.get('paper_id')}]"


def build_markdown_report(dataset: Dict[str, Any], papers: List[Dict[str, Any]], metrics: List[Dict[str, Any]], lang: str) -> str:
    name = dataset["dataset_name"]
    if lang == "en":
        title = f"# {name} PaperSOTA Report"
        metric_title = "## 2. Metrics"
        table_title = "## 3. Benchmark / Algorithm Comparison"
        ref_title = "## 4. References"
        notes_title = "## 5. Notes"
    else:
        title = f"# {name} PaperSOTA 报告"
        metric_title = "## 2. Metrics 指标说明"
        table_title = "## 3. Benchmark / Algorithm Comparison 算法指标对比"
        ref_title = "## 4. References 参考文献"
        notes_title = "## 5. Notes 说明"
    metric_names = sorted({m["metric"] for m in metrics if m.get("metric") != "metric"})[:12]
    if not metric_names:
        metric_names = ["Metric"]
    best: Dict[str, Optional[float]] = {}
    directions: Dict[str, str] = {}
    for metric in metric_names:
        vals = [m for m in metrics if m.get("metric") == metric and isinstance(m.get("value"), (int, float))]
        directions[metric] = vals[0].get("direction", "unknown") if vals else "unknown"
        if not vals:
            best[metric] = None
        elif directions[metric] == "lower":
            best[metric] = min(v["value"] for v in vals)
        else:
            best[metric] = max(v["value"] for v in vals)
    metric_map: Dict[int, Dict[str, Dict[str, Any]]] = {}
    for m in metrics:
        metric_map.setdefault(m["paper_id"], {})[m.get("metric", "Metric")] = m
    lines = [title, "", "## 1. Dataset", "", f"- Dataset name: {name}", f"- Aliases: {', '.join(dataset.get('aliases') or [name])}", f"- Domain / task: {dataset.get('domain') or '—'}", f"- Official homepage: {dataset.get('official_url') or '—'}", f"- Introducing paper: {dataset.get('introducing_paper') or '—'}", f"- Verification notes: {dataset.get('verification_notes') or '—'}", "", metric_title, ""]
    for metric in metric_names:
        d = directions.get(metric, "unknown")
        if d == "lower":
            explain = "lower is better / 越低越好"
        elif d == "higher":
            explain = "higher is better / 越高越好"
        else:
            explain = "direction unknown / 方向待核实"
        lines.append(f"- {metric}: {explain}.")
    lines += ["", table_title, "", "> Bold values indicate the best result in each comparable metric column. `—` means metric not found in accessible text.", ""]
    headers = ["Paper"] + metric_names + ["Notes"]
    aligns = ["---"] + ["---:" for _ in metric_names] + ["---"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(aligns) + " |")
    for rec in papers:
        row = [paper_label(rec)]
        notes: List[str] = []
        for metric in metric_names:
            m = metric_map.get(rec["paper_id"], {}).get(metric)
            if not m or m.get("value") is None:
                row.append("—")
                notes.append("metric not found in accessible text")
            else:
                val = m.get("display_value", str(m.get("value")))
                if best.get(metric) is not None and float(m["value"]) == float(best[metric]):
                    val = f"**{val}**"
                row.append(val)
                if m.get("notes"):
                    notes.append(m["notes"])
        row.append("; ".join(sorted(set(notes)))[:160] or rec.get("notes") or "")
        lines.append("| " + " | ".join(str(x).replace("|", "/") for x in row) + " |")
    lines += ["", ref_title, ""]
    for rec in papers:
        authors = ", ".join(rec.get("authors")[:3]) if rec.get("authors") else "Unknown authors"
        if rec.get("authors") and len(rec.get("authors")) > 3:
            authors += " et al."
        title_text = rec.get("title") or "Untitled"
        venue = rec.get("venue") or ""
        year = rec.get("year") or ""
        url = rec.get("url") or ""
        lines.append(f"[{rec.get('paper_id')}] {authors}. **{title_text}**. {venue}, {year}. {url}")
    missing = sum(1 for m in metrics if m.get("value") is None)
    lines += ["", notes_title, "", f"- Generated: {dt.datetime.utcnow().isoformat(timespec='seconds')}Z", f"- Missing metric records: {missing}", "- Automatically extracted metric values should be manually verified against original tables before publication."]
    return "\n".join(lines) + "\n"


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="PaperSOTA: build dataset-centric paper and SOTA metric report scaffolds.")
    parser.add_argument("input", help="field/direction, paper title/link, or dataset name")
    parser.add_argument("--input-type", choices=["auto", "field", "paper", "dataset"], default="auto")
    parser.add_argument("--max-datasets", type=int, default=5)
    parser.add_argument("--candidate-paper", type=int, default=50, help="candidate papers per dataset")
    parser.add_argument("--fulltext", action="store_true", help="try to fetch HTML/PDF text for metric extraction")
    parser.add_argument("--language", choices=["auto", "zh", "en"], default="auto")
    parser.add_argument("--out-dir", default="papersota-output")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "cache"
    cache_dir.mkdir(exist_ok=True)

    classification = classify_input(args.input, args.input_type)
    if args.language != "auto":
        classification["language"] = args.language
    write_json(out_dir / "input_classification.json", classification)

    if classification["input_type"] == "field":
        datasets = discover_datasets(args.input, args.max_datasets)
    elif classification["input_type"] == "paper":
        datasets = datasets_from_paper(args.input)
    else:
        datasets = [verify_dataset(args.input)]
    write_json(out_dir / "datasets.json", datasets)

    all_papers: Dict[str, List[Dict[str, Any]]] = {}
    all_metrics: Dict[str, List[Dict[str, Any]]] = {}
    reports: List[str] = []
    for ds in datasets:
        ds_name = ds["dataset_name"]
        papers = collect_papers_for_dataset(ds, args.candidate_paper)
        metrics = extract_metrics_for_papers(ds_name, papers, cache_dir, args.fulltext)
        all_papers[ds_name] = papers
        all_metrics[ds_name] = metrics
        report = build_markdown_report(ds, papers, metrics, classification["language"])
        report_path = out_dir / f"papersota-report-{slug(ds_name)}.md"
        report_path.write_text(report, encoding="utf-8")
        reports.append(str(report_path))

    write_json(out_dir / "papers.json", all_papers)
    write_json(out_dir / "metrics.json", all_metrics)
    notes = ["# PaperSOTA notes", "", "- Metric extraction is heuristic and requires manual review.", "- Use examples/agd20k-report.md as a formatting reference for publication-quality tables.", "- Split reports by protocol when metrics are not directly comparable."]
    (out_dir / "notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "reports": reports, "datasets": [d["dataset_name"] for d in datasets]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
