"""Marker-slot Markdown reports: parse and check (shared by every phase with a writeup).

A report template puts every student answer between a pair of HTML-comment markers::

    <!--answer:vpc_name-->
    echo-net
    <!--/answer-->

Markers are invisible in rendered Markdown, so the report still reads normally, but they give
the grader a stable anchor that survives students rewording the prose around them.

Each phase declares its expected answers as a tuple of :class:`Slot` and calls :func:`check`.
Three kinds of check exist, of very different strength:

* **Structural** — every slot exists, is filled, meets a minimum length, mentions required
  words. Cheap; it only proves effort.
* **Cross-checked against the phase's JSON report** — numbers a student writes into the prose
  must match what the tooling actually recorded. This is the valuable one: it is the only
  check that catches numbers copied from a classmate or invented.
* **Range** — a number must fall in a plausible interval when no ground truth exists.

Per-phase wrappers (``phase-N-*/report_md.py``) hold the slots and give a CLI::

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
# A "token" for must_have checks: identifier-ish runs, so `collect()`, "echo-bot", and
# `roles/run.invoker` each yield sensible pieces; surrounding punctuation is not part of it.
TOKEN = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-/]*")
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass(frozen=True)
class Slot:
    """One expected answer: how to validate it, and where its truth lives."""
    name: str
    kind: str                       # "number" | "text" | "prose" | "verbatim"
    min_words: int = 0
    json_path: tuple = ()           # e.g. ("platforms", "vm", "cold_ms") — cross-check source
    tol_abs: float = 1.0            # cross-check tolerance: max(tol_abs, tol_rel * |truth|)
    tol_rel: float = 0.01
    min_value: float | None = None  # range check when there is no ground truth
    max_value: float | None = None
    must_have_tokens: tuple = ()    # ALL of these must appear as tokens (case-insensitive)
    any_of_tokens: tuple = ()       # at least ONE of these must appear as a token
    must_have_number: bool = False  # prose must contain at least one number


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
    m = NUMBER.search(text.replace(",", ""))
    return float(m.group()) if m else None


def _tokens(text: str) -> set[str]:
    return {t.rstrip(".").lower() for t in TOKEN.findall(text)}


def check(markdown: str, slots: tuple[Slot, ...], json_report: dict | None = None) -> list[Finding]:
    """Validate a filled report against ``slots``. Cross-checks numbers when json_report is given."""
    answers = parse(markdown)
    findings: list[Finding] = []

    for slot in slots:
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
                                            f"{'.'.join(slot.json_path)} missing from the JSON report"))
                    continue
                tolerance = max(slot.tol_abs, abs(float(truth)) * slot.tol_rel)
                if abs(value - float(truth)) > tolerance:
                    findings.append(Finding(slot.name, False,
                                            f"reported {value} but the JSON report says {truth}"))
                    continue
            if slot.min_value is not None and value < slot.min_value:
                findings.append(Finding(slot.name, False, f"{value} is below the plausible minimum {slot.min_value}"))
                continue
            if slot.max_value is not None and value > slot.max_value:
                findings.append(Finding(slot.name, False, f"{value} is above the plausible maximum {slot.max_value}"))
                continue
            findings.append(Finding(slot.name, True, f"{value}"))
            continue

        words = len(raw.split())
        if slot.min_words and words < slot.min_words:
            findings.append(Finding(slot.name, False,
                                    f"too short: {words} words, expected at least {slot.min_words}"))
            continue
        tokens = _tokens(raw)
        missing = [tok for tok in slot.must_have_tokens if tok.lower() not in tokens]
        if missing:
            findings.append(Finding(slot.name, False, f"does not mention {', '.join(missing)}"))
            continue
        if slot.any_of_tokens and not any(tok.lower() in tokens for tok in slot.any_of_tokens):
            findings.append(Finding(slot.name, False,
                                    f"mentions none of {', '.join(slot.any_of_tokens)}"))
            continue
        if slot.must_have_number and _as_number(raw) is None:
            findings.append(Finding(slot.name, False, "should contain a number (an estimate, a count, a time)"))
            continue
        findings.append(Finding(slot.name, True, f"{words} words"))

    return findings


def main(slots: tuple[Slot, ...], argv=None, usage: str = "report_md.py <report.md> [report.json]") -> int:
    """CLI shared by the per-phase wrappers: print PASS/FAIL per slot, exit 0 iff all pass."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(f"usage: {usage}", file=sys.stderr)
        return 2
    md = Path(argv[0]).read_text(encoding="utf-8")
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8")) if len(argv) > 1 else None

    findings = check(md, slots, data)
    passed = sum(f.ok for f in findings)
    for f in findings:
        print(f"  [{'PASS' if f.ok else 'FAIL'}] {f.slot:<28} {f.message}")
    print(f"\n{passed}/{len(findings)} answer slots OK")
    return 0 if passed == len(findings) else 1
