#!/usr/bin/env python3
"""Offline, evidence-traceable PS5 diagnostic prototype."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

VERSION = "0.1.0"
DEFAULT_RULES = Path(__file__).parent / "data" / "errors.json"


def load_rules(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read rule database {path}: {exc}") from exc


def walk_json(value: Any, pointer: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from walk_json(child, f"{pointer}/{escaped}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_json(child, f"{pointer}/{index}")
    elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
        yield pointer or "/", str(value)


def extract_evidence(source: Path) -> tuple[str, list[dict[str, Any]]]:
    raw = source.read_text(encoding="utf-8-sig", errors="replace")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        evidence = []
        for number, line in enumerate(raw.splitlines(), start=1):
            if line.strip():
                evidence.append({
                    "location": {"line": number},
                    "original_message": line,
                })
        return "text", evidence
    evidence = [
        {"location": {"json_pointer": pointer}, "original_message": value}
        for pointer, value in walk_json(parsed)
    ]
    return "json", evidence


def analyze(code: str | None, source: Path | None, rules: dict[str, Any]):
    source_info: dict[str, Any]
    evidence: list[dict[str, Any]]
    if source:
        source_format, evidence = extract_evidence(source)
        source_info = {"filename": source.name, "format": source_format, "provenance": "user_import"}
    else:
        evidence = [{"location": {"input": "command_line"}, "original_message": code or ""}]
        source_info = {"filename": None, "format": "manual_code", "provenance": "user_input"}

    findings = []
    for rule in rules.get("rules", []):
        matched: list[dict[str, Any]] = []
        if code and code.upper() in {item.upper() for item in rule.get("codes", [])}:
            matched.append(evidence[0])
        for item in evidence:
            message = item["original_message"]
            pattern = rule.get("pattern")
            if pattern and re.search(pattern, message, flags=re.IGNORECASE):
                matched.append(item)
        # A source line may satisfy both code and text matching; show it once.
        unique = {(json.dumps(item["location"], sort_keys=True), item["original_message"]): item for item in matched}
        if not unique:
            continue
        findings.append({
            "finding_id": rule["finding_id"],
            "title": rule["title"],
            "summary": rule["summary"],
            "confidence": rule["confidence"],
            "source": source_info,
            "evidence": list(unique.values()),
            "matched_rule": {
                "id": rule["id"],
                "rule_set_version": rules["version"],
                "reason": rule["reason"],
            },
            "possible_causes": rule.get("possible_causes", []),
            "recommended_checks": rule.get("recommended_checks", []),
            "missing_information": rule.get("missing_information", []),
        })
    return {
        "analyzer_version": VERSION,
        "rule_set_version": rules["version"],
        "input": source_info,
        "findings": findings,
        "status": "needs_investigation" if findings else "no_match",
        "note": "A rule match is a lead for investigation, not proof of root cause." if findings else "No bundled rule matched. This does not mean the input is error-free.",
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [f"PS5 Error Analyzer {report['analyzer_version']}", f"Status: {report['status']}", report["note"]]
    for finding in report["findings"]:
        lines.extend(["", f"{finding['title']} ({finding['confidence']} confidence)", finding["summary"]])
        for item in finding["evidence"]:
            location = item["location"]
            if "line" in location:
                where = f"line {location['line']}"
            elif "json_pointer" in location:
                where = f"JSON field {location['json_pointer']}"
            else:
                where = "manual input"
            lines.append(f"  Evidence: {finding['source']['filename'] or 'command line'}:{where}")
            lines.append(f"  Original: {item['original_message']}")
        rule = finding["matched_rule"]
        lines.append(f"  Rule: {rule['id']} (rules {rule['rule_set_version']}) — {rule['reason']}")
        lines.append("  Possible causes: " + ("; ".join(finding["possible_causes"]) or "None listed"))
        lines.append("  Recommended checks: " + ("; ".join(finding["recommended_checks"]) or "None listed"))
        lines.append("  Missing information: " + ("; ".join(finding["missing_information"]) or "None identified by this rule"))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze PS5 log text, JSON reports, or an error code.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Text log or JSON crash report to analyze")
    group.add_argument("--code", help="Error code to look up (no network access)")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Report format")
    parser.add_argument("--output", type=Path, help="Write report to a file instead of stdout")
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES, help="Diagnostic rule database JSON")
    args = parser.parse_args()
    try:
        rules = load_rules(args.rules)
        if args.file and not args.file.is_file():
            raise ValueError(f"Input file does not exist: {args.file}")
        report = analyze(args.code, args.file, rules)
        rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else render_text(report)
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

