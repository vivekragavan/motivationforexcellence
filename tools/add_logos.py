#!/usr/bin/env python3
"""Put partner logos back on the 22 older project pages.

The WordPress originals (hot-linked from the dead mfe.crmleadgen.net host) are lost, so the
logos are current official ones collected from each partner's website (Sahil, 2026-11-22).
clean_demo.py removes the dead <img> tags; this script re-inserts a logo at the same spot,
using the pre-removal markup from git commit 663fe31^ to find where the logo (and its link) was.

Usage: python3 tools/add_logos.py <folder with <slug>.png/.jpg/.svg>
Pages with no file in the folder (or listed in HOLD) stay without a logo. Rerunnable.
"""
import re, subprocess, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "wp-content/uploads/partner-logos"
URL = "/motivationforexcellence/wp-content/uploads/partner-logos/"
BEFORE = "663fe31^"  # last commit with the dead logo tags in place
FILE_FOR = {"ffe": "foundation-for-excellence", "lfe": "leadership-for-equity"}
HOLD = {"prayas"}  # logo supplied may be the wrong Prayas (Pune energy group vs TISS) - check first
DEAD = re.compile(r'(?:<a [^>]*>\s*)?<img [^>]*src="https?://mfe\.crmleadgen\.net/[^>]*>(?:\s*</a>)?')
STYLE = "width:auto;height:auto;max-width:300px;max-height:120px"
MARK = "partner-logo"

src_dir = Path(sys.argv[1]).expanduser()
DEST.mkdir(parents=True, exist_ok=True)
pages = subprocess.run(["git", "grep", "-l", "mfe.crmleadgen.net", BEFORE, "--", "project/*/index.html"],
                       cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
added, skipped = [], []
for ref in pages:
    path = ref.split(":", 1)[1]
    slug = path.split("/")[1]
    page = ROOT / path
    s = page.read_text(encoding="utf-8")
    if MARK in s:
        added.append(slug + " (already)"); continue
    name = FILE_FOR.get(slug, slug)
    files = [f for f in src_dir.glob(name + ".*") if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".svg", ".webp")]
    if slug in HOLD or not files:
        skipped.append(slug); continue
    f = files[0]
    out = DEST / (slug + f.suffix.lower())
    if f.suffix.lower() == ".svg":
        shutil.copy(f, out)
    else:  # web size: at most 600px on the long side (2x the display box)
        subprocess.run(["sips", "-Z", "600", str(f), "--out", str(out)], check=True, capture_output=True)
    old = subprocess.run(["git", "show", f"{BEFORE}:{path}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    m = DEAD.search(old)
    tag = m.group(0)
    link = re.match(r'<a [^>]*>', tag)
    style = "height:70px;width:auto" if out.suffix == ".svg" else STYLE  # svg has a tiny 66x33 intrinsic size
    img = f'<img class="{MARK}" decoding="async" src="{URL}{out.name}" alt="" style="{style}" />'
    new = (link.group(0) + img + "</a>") if link else img
    # where the logo was: text just before it in the old page, else the wrapper it sat in
    before = old[:m.start()]
    after = old[m.end():]
    wrap_open = re.search(r'<(p|h1)( [^>]*)?>\s*$', before)
    if wrap_open and re.match(r'\s*</%s>' % wrap_open.group(1), after):
        ctx = before[:wrap_open.start()]
        tail = after[re.match(r'\s*</%s>' % wrap_open.group(1), after).end():]
        new = f'<p>{new}</p>'
    else:
        ctx, tail = before, after
    ctx, tail = ctx[-120:], tail.lstrip()[:120]
    if s.count(ctx) == 1:
        i = s.index(ctx) + len(ctx)
    elif s.count(tail) == 1:
        i = s.index(tail)
    else:
        sys.exit(f"{slug}: insertion point not found uniquely")
    page.write_text(s[:i] + new + s[i:], encoding="utf-8")
    added.append(slug)
print("added:", len(added), added)
print("no logo:", skipped)
