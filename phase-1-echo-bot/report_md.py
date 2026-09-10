#!/usr/bin/env python3
"""Parse and check `submission/phase1_report.md` (provided).

The report template puts every student answer between a pair of HTML-comment markers::

    <!--answer:vpc_name-->
    echo-net
    <!--/answer-->

Markers are invisible in rendered Markdown, so the report still reads normally, but they give
the grader a stable anchor that survives students rewording the prose around them.

Two kinds of check are possible here, and they are very different in strength:

* **Structural** — every slot exists, is filled, and meets a minimum length. Cheap, and it
  only proves effort.
* **Cross-checked against `phase1_report.json`** — the latency figures a student writes into
  the prose must match what `measure.py` actually recorded. This is the valuable one: it is
  the only check that catches numbers copied from a classmate or invented.

Use as a library (see ``check``), or run it directly to see how a report scores::

    python phase-1-echo-bot/report_md.py submission/phase1_report.md submission/phase1_report.json
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MARKER = re.compile(r"<!--answer:([A-Za-z0-9_]+)-->(.*?)<!--/answer-->", re.DOTALL)
PLACEHOLDER = {"", "todo"}


@dataclass(frozen=True)
class Slot:
    """One expected answer: how to validate it, and where its truth lives."""
    name: str
    kind: str                      # "number" | "text" | "prose" | "verbatim"
    min_words: int = 0
    json_path: tuple = ()          # e.g. ("platforms", "vm", "cold_ms") — cross-check source
    must_have_tokens: tuple = ()   # whitespace-delimited tokens that must appear verbatim.
                                   # Tokens, not substrings: "echo" must not be satisfied
                                   # by the "echo" inside "echo-bot".


SLOTS: tuple[Slot, ...] = (
    Slot("image_size_mb", "number"),
    Slot("vpc_name", "text"),
    Slot("subnet_name", "text"),
    Slot("vm_cold_ms", "number", json_path=("platforms", "vm", "cold_ms")),
    Slot("vm_warm_median_ms", "number", json_path=("platforms", "vm", "stats", "median")),
    Slot("cloudrun_cold_ms", "number", json_path=("platforms", "cloudrun", "cold_ms")),
    Slot("cloudrun_warm_median_ms", "number", json_path=("platforms", "cloudrun", "stats", "median")),
    Slot("function_cold_ms", "number", json_path=("platforms", "function", "cold_ms")),
    Slot("function_warm_median_ms", "number", json_path=("platforms", "function", "stats", "median")),
    Slot("latency_plot", "verbatim"),
    Slot("scaling_behaviour", "prose", min_words=55),
    Slot("deployment_effort", "prose", min_words=70),
    Slot("run_services_list", "verbatim", must_have_tokens=("echo-bot", "echo")),
    Slot("convergence_explanation", "prose", min_words=90),
)


@dataclass
class Finding:
    slot: str
    ok: bool
    message: str


def parse(markdown: str) -> dict[str, str]:
    """Return {slot_name: answer_text} for every marker pair found."""
    return {m.group(1): m.group(2).strip() for m in MARKER.finditer(markdown)}


def _dig(data: dict, path: tuple):
    for key in path:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def _as_number(text: str) -> float | None:
    """First number in the text, so '812.4 ms' and '~812' both work."""
    m = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return float(m.group()) if m else None


def check(markdown: str, json_report: dict | None = None) -> list[Finding]:
    """Validate a filled report. Cross-checks numbers when json_report is given."""
    answers = parse(markdown)
    findings: list[Finding] = []

    for slot in SLOTS:
        raw = answers.get(slot.name)
        if raw is None:
            findings.append(Finding(slot.name, False, "answer marker is missing from the report"))
            continue
        if raw.strip().lower() in PLACEHOLDER:
            findings.append(Finding(slot.name, False, "still the TODO placeholder — not filled in"))
            continue

        if slot.kind == "number":
            value = _as_number(raw)
            if value is None:
                findings.append(Finding(slot.name, False, f"expected a number, got {raw[:40]!r}"))
                continue
            if slot.json_path and json_report is not None:
                truth = _dig(json_report, slot.json_path)
                if truth is None:
                    findings.append(Finding(slot.name, False,
                                            f"{'.'.join(slot.json_path)} missing from phase1_report.json"))
                    continue
                tolerance = max(1.0, abs(float(truth)) * 0.01)
                if abs(value - float(truth)) > tolerance:
                    findings.append(Finding(slot.name, False,
                                            f"reported {value} but phase1_report.json says {truth}"))
                    continue
            findings.append(Finding(slot.name, True, f"{value}"))
            continue

        words = len(raw.split())
        if slot.min_words and words < slot.min_words:
            findings.append(Finding(slot.name, False,
                                    f"too short: {words} words, expected at least {slot.min_words}"))
            continue
        tokens = set(re.split(r"[\s,;|]+", raw.strip()))
        missing = [tok for tok in slot.must_have_tokens if tok not in tokens]
        if missing:
            findings.append(Finding(slot.name, False,
                                    f"pasted output has no {', '.join(missing)} service"))
            continue
        findings.append(Finding(slot.name, True, f"{words} words"))

    return findings


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__.splitlines()[0])
        print("usage: report_md.py <report.md> [report.json]", file=sys.stderr)
        return 2
    md = Path(argv[0]).read_text(encoding="utf-8")
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8")) if len(argv) > 1 else None

    findings = check(md, data)
    passed = sum(f.ok for f in findings)
    for f in findings:
        print(f"  [{'PASS' if f.ok else 'FAIL'}] {f.slot:<26} {f.message}")
    print(f"\n{passed}/{len(findings)} answer slots OK")
    return 0 if passed == len(findings) else 1


if __name__ == "__main__":
    raise SystemExit(main())
