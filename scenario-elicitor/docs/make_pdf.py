#!/usr/bin/env python3
"""Render a markdown doc in this folder to a PDF, via headless Chrome.

    python3 make_pdf.py provenance.md

Exists so the PDF can be regenerated whenever the markdown changes, rather than
becoming a stale copy of a doc that has moved on. Handles only the constructs
these documents actually use: headings, paragraphs, blockquotes, bullet lists,
tables, and inline bold/italic/code/links.
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: letter landscape; margin: 0.5in 0.55in 0.6in; }
* { box-sizing: border-box; }
body {
  font: 10pt/1.5 -apple-system, "Helvetica Neue", Arial, sans-serif;
  color: #2A2118; margin: 0; -webkit-print-color-adjust: exact;
}
h1 {
  font-size: 21pt; line-height: 1.15; margin: 0 0 2pt; letter-spacing: -0.01em;
}
.sub { color: #7A6A55; font-size: 10pt; margin: 0 0 14pt; }
h2 {
  font-size: 13pt; margin: 20pt 0 7pt; padding-bottom: 4pt;
  border-bottom: 1.5px solid #C9B896; break-after: avoid;
}
h2:first-of-type { margin-top: 6pt; }
p { margin: 0 0 7pt; max-width: 62em; }
ul { margin: 0 0 8pt; padding-left: 16pt; max-width: 62em; }
li { margin-bottom: 4pt; }
code {
  font: 8.6pt/1.4 "SF Mono", Menlo, Consolas, monospace;
  background: #F2EADC; padding: 0.5pt 3pt; border-radius: 3px;
}
table { width: 100%; border-collapse: collapse; margin: 0 0 10pt; }
thead { display: table-header-group; }
th {
  text-align: left; font-size: 7.8pt; text-transform: uppercase;
  letter-spacing: 0.07em; color: #6B5B45; font-weight: 700;
  padding: 5pt 7pt; background: #F2EADC; border-bottom: 1.5px solid #C9B896;
}
td {
  padding: 6pt 7pt; vertical-align: top; font-size: 9.2pt; line-height: 1.45;
  border-bottom: 0.75px solid #E4DAC6;
}
tr { break-inside: avoid; }
tr.band th {
  background: #EDE2CE; color: #4A3D2C; font-size: 8.6pt; letter-spacing: 0.04em;
  text-transform: none; border-bottom: 0; padding-bottom: 2pt;
}
tbody tr:nth-child(even) td { background: #FBF7EF; }
/* Widths come from a colgroup, not nth-child: the ledger gets a row-number
   column prepended, which shifts every positional selector by one and lands the
   source styling on the why text. Columns are fixed so a long Why does not
   starve the others. */
table { table-layout: fixed; }
table.f4 td:nth-of-type(2) { font-weight: 600; }
table.f4 td:last-child {
  font-size: 8.6pt; color: #6B5B45; font-style: italic;
}
table.src td:first-child { font-weight: 600; }
.n { color: #A89578; font-variant-numeric: tabular-nums; padding-right: 4pt; }
blockquote {
  margin: 0 0 8pt; padding: 6pt 10pt; background: #FBF7EF;
  border-left: 2.5px solid #C9B896; max-width: 62em;
}
blockquote p:last-child { margin-bottom: 0; }
hr { border: 0; border-top: 1px solid #E4DAC6; margin: 14pt 0; }
"""


def inline(t: str) -> str:
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", t)   # links are noise in print
    return t


def cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def render(md: str) -> str:
    out, lines, i = [], md.splitlines(), 0
    section = ""
    title = sub = ""
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|") and i + 1 < len(lines) and set(
                lines[i + 1].replace("|", "").replace(" ", "")) <= {"-", ":"}:
            head = cells(ln)
            i += 2
            body = []
            while i < len(lines) and lines[i].startswith("|"):
                body.append(cells(lines[i])); i += 1
            klass = "f4" if len(head) == 4 else "src"
            numbered = klass == "f4"
            th = "".join(f"<th>{inline(h)}</th>" for h in head)
            if numbered:
                th = "<th></th>" + th
                cols = ("3%", "19%", "19%", "42%", "17%")
            else:
                cols = ("13%", "87%")
            cg = "".join(f'<col style="width:{w}">' for w in cols)
            # thead repeats on every page, so the section name rides along in
            # it: without it, a reader on page 4 has no idea which part of the
            # document the rows in front of them belong to. Only on the ledger
            # tables, which run over pages. On a short table it sits directly
            # under the heading it repeats, which is just noise.
            band = (f'<tr class="band"><th colspan="{len(cols)}">{section}</th></tr>'
                    if section and numbered else "")
            rows = []
            for n, r in enumerate(body, 1):
                tds = "".join(f"<td>{inline(c)}</td>" for c in r)
                if numbered:
                    tds = f'<td class="n">{n}</td>' + tds
                rows.append(f"<tr>{tds}</tr>")
            out.append(f'<table class="{klass}"><colgroup>{cg}</colgroup>'
                       f'<thead>{band}<tr>{th}</tr></thead>'
                       f'<tbody>{"".join(rows)}</tbody></table>')
            continue
        if ln.startswith("# "):
            title = inline(ln[2:].strip()); i += 1; continue
        if ln.startswith("## "):
            section = inline(ln[3:].strip())
            out.append(f"<h2>{section}</h2>"); i += 1; continue
        if ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:]); i += 1
            out.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
            continue
        if ln.startswith("- "):
            buf = []
            while i < len(lines) and (lines[i].startswith("- ")
                                      or lines[i].startswith("  ")):
                if lines[i].startswith("- "):
                    buf.append(lines[i][2:].strip())
                elif buf:
                    buf[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in buf)
                       + "</ul>")
            continue
        if ln.strip() == "---":
            out.append("<hr>"); i += 1; continue
        if ln.strip():
            buf = []
            while i < len(lines) and lines[i].strip() and not lines[i][:1] in "#|->":
                buf.append(lines[i].strip()); i += 1
            para = inline(" ".join(buf))
            if not sub and not out:
                sub = para
            else:
                out.append(f"<p>{para}</p>")
            continue
        i += 1
    head = (f"<h1>{title}</h1>" if title else "") + \
           (f'<p class="sub">{sub}</p>' if sub else "")
    return (f"<!doctype html><meta charset='utf-8'><title>{title}</title>"
            f"<style>{CSS}</style>{head}{''.join(out)}")


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "provenance.md")
    if not src.exists():
        print(f"no such file: {src}"); return 1
    tmp = src.with_suffix(".html")
    tmp.write_text(render(src.read_text()))
    pdf = src.with_suffix(".pdf")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf.resolve()}", tmp.resolve().as_uri()],
                   check=True, capture_output=True)
    tmp.unlink()
    print(f"{pdf}  ({pdf.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
