#!/usr/bin/env python3
"""Add the "Women's Empowerment" portfolio category (rerunnable).

* menu item under Our Portfolio, after Livelihood Enhancement, on every page
* womens-empowerment/index.html built from the Livelihood Enhancement page
* projects listed in MOVE are moved onto it: their listing box is taken off
  their old category page, and the project page's "Categories:" link and
  pj-categs class are switched to the new category.

Run from the repo root:  python3 tools/add_category.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "/motivationforexcellence"
SLUG = "womens-empowerment"
TITLE = "Women&#8217;s Empowerment"
MENU_ID = "90001"
TEMPLATE = "livelihood-enhancement"
CATS = ["healthcare", "education-training", "livelihood-enhancement",
        "nurturing-excellence", "philanthropy-partners"]

# project slugs to move onto the Women's Empowerment page
MOVE = []

ART_RE = re.compile(r'<!-- Start Standard Project -->\s*<article id="post-\d+".*?</article>\s*<!-- Finish Standard Project -->\s*', re.S)
GRID_RE = re.compile(r'(<div class="portfolio grid [^"]*">\n)(.*?)(</div><div class="cmsmasters_wrap_more_projects)', re.S)


def menu_li(current=False):
    cur = " current-menu-item current_page_item" if current else ""
    return (f'\t<li id="menu-item-{MENU_ID}" class="menu-item menu-item-type-post_type menu-item-object-page{cur} '
            f'menu-item-{MENU_ID} menu-item-depth-1"><a href="{BASE}/{SLUG}/"><span class="nav_item_wrap">'
            f'<span class="nav_title">{TITLE}</span></span></a>\t</li>\n')


def add_menu(html, current=False):
    html = re.sub(rf'\t<li id="menu-item-{MENU_ID}".*?</li>\n', "", html, flags=re.S)
    m = re.search(r'<li id="menu-item-12522".*?</li>\n', html, re.S)
    if not m:
        return html
    return html[:m.end()] + menu_li(current) + html[m.end():]


def project_slug(article):
    m = re.search(rf'href="{BASE}/project/([^/"]+)/"', article)
    return m.group(1) if m else None


def main():
    # collect listing boxes: from category pages (moving those in MOVE) and the existing new page
    moved = {}
    for cat in CATS + [SLUG]:
        f = ROOT / cat / "index.html"
        if not f.exists():
            continue
        html = f.read_text()
        g = GRID_RE.search(html)
        if not g:
            continue
        keep = []
        for a in ART_RE.findall(g.group(2)):
            s = project_slug(a)
            if s in MOVE and s not in moved:
                moved[s] = a
            elif cat != SLUG:
                keep.append(a)
        if cat != SLUG:
            html = html[:g.start(2)] + "".join(keep) + html[g.end(2):]
            f.write_text(html)
    missing = [s for s in MOVE if s not in moved]
    if missing:
        raise SystemExit(f"not found on any category page: {missing}")

    # build the new category page from the template
    html = (ROOT / TEMPLATE / "index.html").read_text()
    html = html.replace("Livelihood Enhancement &#8211;", f"{TITLE} &#8211;")
    html = html.replace('<h1 class="entry-title">Livelihood Enhancement</h1>', f'<h1 class="entry-title">{TITLE}</h1>')
    html = html.replace("%2Flivelihood-enhancement%2F", f"%2F{SLUG}%2F")
    html = html.replace(f'rel="canonical" href="{BASE}/livelihood-enhancement/"', f'rel="canonical" href="{BASE}/{SLUG}/"')
    html = html.replace("\t\t'livelihood-enhancement', ", f"\t\t'{SLUG}', ")
    html = html.replace(" current-menu-item page_item page-item-12515 current_page_item", "")
    g = GRID_RE.search(html)
    boxes = [re.sub(r'data-category="[^"]*"', f'data-category="{SLUG}"',
                    re.sub(r'pj-categs-[\w-]+', f'pj-categs-{SLUG}', moved[s])) for s in MOVE]
    html = html[:g.start(2)] + "".join(boxes) + html[g.end(2):]
    out = ROOT / SLUG / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(add_menu(html, current=True))

    # menu on every page; category link on moved project pages
    pages = [p for p in ROOT.rglob("index.html") if not p.relative_to(ROOT).parts[0].startswith("wp-")]
    for p in pages:
        if p == out:
            continue
        html = add_menu(p.read_text())
        rel = p.relative_to(ROOT).parts
        if len(rel) == 3 and rel[0] == "project" and rel[1] in MOVE:
            html = re.sub(r'(<span class="cmsmasters_project_category"><a href=")[^"]*(" class="cmsmasters_cat_color[^"]*" rel="category tag">)[^<]*(</a>)',
                          rf'\g<1>{BASE}/{SLUG}/\g<2>{TITLE}\g<3>', html)
            html = re.sub(r'pj-categs-[\w-]+', f'pj-categs-{SLUG}', html)
        p.write_text(html)
    print(f"menu on {len(pages)} pages; moved: {MOVE or 'none yet'}")


if __name__ == "__main__":
    main()
