"""Build the submission .docx inside the official Apart template.

Keeps the template's package (styles, fonts, page setup, title block, footnote), fills the title block (title,
authors, abstract) and replaces the guidance text with the paper body, converted by pandoc with the template as
reference doc. Images and hyperlinks of the body are merged into the template package.

  python paper/final/build_template_docx.py --template <template.docx> --md paper/final/paper_final.md \
      --out paper/final/Before_the_Swarm_Tips_final.docx
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

TITLE = "Before the Swarm Tips: Early Warning for Collective Rule-Breaking in LLM Agent Teams"
AUTHORS = [("Mauricio Neubecker", ["Technical University of Munich", "Safe AI Germany (SAGE)"]),
           ("Tim Würfl", ["Technical University of Munich", "Safe AI Germany (SAGE)"]),
           ("Maximilian Eder", ["Technical University of Munich", "Safe AI Germany (SAGE)"])]
ORDER = ["1. Introduction", "2. Related Work", "3. A Simulator for Collective Tipping", "4. What Makes a Team Tip",
         "5. Early Warning: What Works, and Where It Breaks", "6. Discussion and Limitations", "7. Conclusion",
         "Code and Data", "Limitations and Dual-Use / Ethical Considerations", "Author Contributions", "References",
         "Appendix", "LLM Usage Statement"]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def top_elements(body):
    depth, elems, start, cur = 0, [], 0, None
    for m in re.finditer(r'<(/?)(w:p|w:tbl|w:sectPr)\b[^>]*?(/?)>', body):
        tag, close, selfc = m.group(2), m.group(1) == "/", m.group(3) == "/"
        if not close and depth == 0:
            start, cur = m.start(), tag
        if selfc:
            if depth == 0:
                elems.append((cur, body[start:m.end()]))
            continue
        depth += 1 if not close else -1
        if close and depth == 0:
            elems.append((cur, body[start:m.end()]))
    return elems


def body_markdown(md):
    s = md[md.index("# 1. Introduction"):]
    s = re.sub(r"(?m)^\[\^1\]:.*$", "", s)
    s = re.sub(r'<img src="([^"]+)" style="width:([0-9.]+)in;height:[0-9.]+in" />',
               lambda m: f"![]({os.path.abspath(m.group(1))}){{width={m.group(2)}in}}", s)
    parts = re.split(r"(?m)^# (.+)$", s)
    secs = {parts[i].strip(): parts[i + 1] for i in range(1, len(parts), 2)}
    missing = [k for k in secs if k not in ORDER]
    assert not missing, f"unknown sections {missing}"
    out = []
    for k in ORDER:
        if k in secs:
            out.append(f"# {k}\n{secs[k]}")
    s = "\n".join(out)
    s = re.sub(r"(?m)^## ", "### ", s)
    s = re.sub(r"(?m)^# ", "## ", s)
    return s


def abstract_text(md):
    i = md.index("> LLM agent teams")
    return md[i + 2:md.index("\n", i)].strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    md = open(a.md, encoding="utf8").read()
    work = tempfile.mkdtemp()
    tpl, bod = os.path.join(work, "tpl"), os.path.join(work, "body")
    zipfile.ZipFile(a.template).extractall(tpl)

    # 1. body via pandoc with the template as reference doc
    bmd = os.path.join(work, "body.md")
    open(bmd, "w", encoding="utf8").write(body_markdown(md))
    bdocx = os.path.join(work, "body.docx")
    subprocess.run(["pandoc", bmd, "-f", "markdown+pipe_tables", "-o", bdocx, f"--reference-doc={a.template}"], check=True)
    zipfile.ZipFile(bdocx).extractall(bod)
    bx = open(os.path.join(bod, "word", "document.xml"), encoding="utf8").read()
    bbody = bx[bx.index("<w:body>") + 8:bx.rindex("</w:body>")]
    belems = [e for t, e in top_elements(bbody) if t != "w:sectPr"]

    # 2. relationships of the body (images, hyperlinks) -> new ids in the template package
    brels = open(os.path.join(bod, "word", "_rels", "document.xml.rels"), encoding="utf8").read()
    relmap = {m.group(1): m.group(0) for m in re.finditer(r'<Relationship [^>]*Id="([^"]+)"[^>]*/>', brels)}
    body_xml = "".join(belems)
    used = sorted(set(re.findall(r'r:(?:embed|id|link)="([^"]+)"', body_xml)))
    trels_p = os.path.join(tpl, "word", "_rels", "document.xml.rels")
    trels = open(trels_p, encoding="utf8").read()
    new_rels = []
    for rid in used:
        nid = f"rIdBody{rid[3:] if rid.startswith('rId') else rid}"
        body_xml = re.sub(rf'r:(embed|id|link)="{re.escape(rid)}"', rf'r:\1="{nid}"', body_xml)
        rel = relmap[rid].replace(f'Id="{rid}"', f'Id="{nid}"')
        tgt = re.search(r'Target="([^"]+)"', rel).group(1)
        if "TargetMode" not in rel and tgt.startswith("media/"):
            os.makedirs(os.path.join(tpl, "word", "media"), exist_ok=True)
            shutil.copy(os.path.join(bod, "word", tgt), os.path.join(tpl, "word", tgt))
        new_rels.append(rel)
    trels = trels.replace("</Relationships>", "".join(new_rels) + "</Relationships>")
    open(trels_p, "w", encoding="utf8").write(trels)

    # 3. styles and numbering from the pandoc output (template styles + pandoc's own), png content type
    for f in ("styles.xml", "numbering.xml"):
        src = os.path.join(bod, "word", f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(tpl, "word", f))
    ct_p = os.path.join(tpl, "[Content_Types].xml")
    ct = open(ct_p, encoding="utf8").read()
    for ext, typ in (("png", "image/png"), ("jpeg", "image/jpeg"), ("jpg", "image/jpeg")):
        if f'Extension="{ext}"' not in ct:
            ct = ct.replace("<Types ", "<Types ", 1).replace(
                '<Default Extension="xml"', f'<Default Extension="{ext}" ContentType="{typ}"/><Default Extension="xml"', 1)
    if 'PartName="/word/numbering.xml"' not in ct and os.path.exists(os.path.join(tpl, "word", "numbering.xml")):
        ct = ct.replace("</Types>", '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/></Types>')
    open(ct_p, "w", encoding="utf8").write(ct)

    # 4. title block: title, authors (drop the second author row), abstract
    dp = os.path.join(tpl, "word", "document.xml")
    dx = open(dp, encoding="utf8").read()
    head, tbody = dx[:dx.index("<w:body>") + 8], dx[dx.index("<w:body>") + 8:dx.rindex("</w:body>")]
    elems = top_elements(tbody)
    title_tbl = elems[1][1]
    assert "PROJECT TITLE" in title_tbl
    title_tbl = title_tbl.replace(">PROJECT TITLE<", f">{esc(TITLE)}<", 1)
    rows = list(re.finditer(r"<w:tr\b.*?</w:tr>", title_tbl, flags=re.S))
    for r in rows:
        if "Author name 4" in r.group(0) and "Author name 1" not in r.group(0):
            title_tbl = title_tbl.replace(r.group(0), "", 1)
            break
    for k, (name, affs) in enumerate(AUTHORS, start=1):
        title_tbl = title_tbl.replace(f">Author name {k}<", f">{esc(name)}<", 1)
        aff = "</w:t><w:br/><w:t>".join(esc(x) for x in affs)
        title_tbl = title_tbl.replace(">Affiliation<", f">{aff}<", 1)
    assert "Author name" not in title_tbl, "unfilled author slots left"
    # abstract: the paragraph holding the guidance text
    pm = [m for m in re.finditer(r"<w:p\b.*?</w:p>", title_tbl, flags=re.S) if "Summarize your project" in m.group(0)]
    assert len(pm) == 1, "abstract paragraph not found"
    p = pm[0].group(0)
    runs = list(re.finditer(r"<w:r\b.*?</w:r>", p, flags=re.S))
    first = runs[0].group(0)
    rpr = re.search(r"<w:rPr>.*?</w:rPr>", first, flags=re.S)
    rpr = re.sub(r"<w:i/>|<w:iCs/>|<w:i w:val=\"[^\"]*\"/>|<w:iCs w:val=\"[^\"]*\"/>", "", rpr.group(0)) if rpr else ""
    newrun = f'<w:r>{rpr}<w:t xml:space="preserve">{esc(abstract_text(md))}</w:t></w:r>'
    newp = p[:runs[0].start()] + newrun + p[runs[-1].end():]
    title_tbl = title_tbl.replace(p, newp, 1)

    sect = [e for t, e in elems if t == "w:sectPr"]
    new_body = elems[0][1] + title_tbl + elems[2][1] + body_xml + (sect[0] if sect else "")
    dx = head + new_body + dx[dx.rindex("</w:body>"):]
    open(dp, "w", encoding="utf8").write(dx)

    # 5. zip
    if os.path.exists(a.out):
        os.remove(a.out)
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
        ctp = os.path.join(tpl, "[Content_Types].xml")
        z.write(ctp, "[Content_Types].xml")
        for root, _, files in os.walk(tpl):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, tpl)
                if arc != "[Content_Types].xml":
                    z.write(full, arc)
    print("wrote", a.out, "body elements:", len(belems), "relationships merged:", len(new_rels))


if __name__ == "__main__":
    main()
