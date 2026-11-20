#!/usr/bin/env python3
"""Add the "Women's Empowerment" portfolio category (rerunnable).

* menu item under Our Portfolio, after Livelihood Enhancement, on every page
* womens-empowerment/index.html built from the Livelihood Enhancement page
* projects listed in MOVES are moved to their new category page: their listing box is taken off
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

CAT_LABEL = {"healthcare": "HealthCare", "education-training": "Education &amp; Training",
             "livelihood-enhancement": "Livelihood Enhancement", "nurturing-excellence": "Nurturing Excellence",
             "philanthropy-partners": "Philanthropy Partners", SLUG: TITLE}

# project slug -> category page it should be listed on (Categories + Area of Work updated too)
MOVES = {
    "aaa": SLUG,
    "stree-mukti-sanghatana": SLUG,
    "society-for-nutrition-education-and-health-action": SLUG,
    "chetana-vikas": SLUG,
    "haqdarshak": "livelihood-enhancement",
    "prakriti": "livelihood-enhancement",
    "gram-sewa-mandal": "livelihood-enhancement",
    "farmers-for-forests": "livelihood-enhancement",
    "movement-for-scavenger-community": "livelihood-enhancement",
    "vasa": "livelihood-enhancement",
    "bridges-of-sports": "nurturing-excellence",
    "ashoka-university": "nurturing-excellence",
    "search-nirman": "nurturing-excellence",
}

# one programme of a two-programme partner shown as a separate, self-contained project in another
# category: a new project page = the partner's intro + only that programme (the other one is cut),
# plus its own listing box. The original page is left as it is.
SPLIT = [
    dict(slug="makerghat", new="makerghat-ignite", post="23903", cat="nurturing-excellence",
         title="MakerGhat &#8211; IGNITE Maharashtra", keep="IGNITE Maharashtra:", drop="Maker Maharashtra:",
         intro=("MFE supports two linked programmes", "MFE supports IGNITE Maharashtra over four years.")),
    dict(slug="stem-shiksha-foundation", new="maker-bhavan-inventx", post="23904", cat="nurturing-excellence",
         title="Maker Bhavan &#8211; InventX", keep="Scaling InventX:", drop="Nationwide expansion",
         intro=("MFE supports two programmes", "MFE supports InventX over three years (October 2026 to September 2029).")),
]


def make_split(sp):
    html = (ROOT / "project" / sp["slug"] / "index.html").read_text()
    old = re.search(r'<h1 class="entry-title">([^<]*)</h1>', html).group(1)
    html = re.sub(rf'<p>{re.escape(sp["intro"][0])}[^<]*</p>', f'<p>{sp["intro"][1]}</p>', html)
    html = re.sub(rf'<p><strong><em>{re.escape(sp["drop"])}.*?(?=<p><strong><em>{re.escape(sp["keep"])})', "", html, flags=re.S)
    for a, b in ((f"<title>{old} &#8211;", f"<title>{sp['title']} &#8211;"),
                 (f'<h1 class="entry-title">{old}</h1>', f'<h1 class="entry-title">{sp["title"]}</h1>'),
                 (f'alt="{old}"', f'alt="{sp["title"]}"'), (f'title="{old}"', f'title="{sp["title"]}"'),
                 (f"{BASE}/project/{sp['slug']}/", f"{BASE}/project/{sp['new']}/"),
                 (f"%2Fproject%2F{sp['slug']}%2F", f"%2Fproject%2F{sp['new']}%2F")):
        html = html.replace(a, b)
    html = re.sub(r'post-\d+', f'post-{sp["post"]}', html)
    out = ROOT / "project" / sp["new"] / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)


def split_box(box, sp):
    old = re.search(r'alt="([^"]*)"', box).group(1)
    box = box.replace(f'title="{old}"', f'title="{sp["title"]}"').replace(f'alt="{old}"', f'alt="{sp["title"]}"')
    box = box.replace(f">{old}<", f">{sp['title']}<").replace(f"{BASE}/project/{sp['slug']}/", f"{BASE}/project/{sp['new']}/")
    return re.sub(r'post-\d+', f'post-{sp["post"]}', box)


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


HOME_IMG = (f'<img loading="lazy" decoding="async" width="1024" height="600" '
            f'src="{BASE}/wp-content/uploads/2026/11/womens-empowerment-1024x600.jpg" class="attachment-large size-large" alt="" />')


def update_home():
    """Homepage Portfolio section: add Women's Empowerment as no. 4 (mobile list + desktop rows)."""
    f = ROOT / "index.html"
    html = f.read_text()
    if f'elementor-size-default"><a href="{BASE}/{SLUG}/"' in html:
        return

    def cut(start_id, end_id):
        a = html.index(f'\t\t<div class="elementor-element elementor-element-{start_id} ')
        b = html.index(f'\t\t<div class="elementor-element elementor-element-{end_id} ')
        return a, b

    def swap(block, frm, to, label=None):
        """Put category `to` (slug, heading text, img tag) into a block built for `frm`."""
        block = re.sub(rf'<a href="{BASE}/{frm[0]}/">[^<]*</a>', f'<a href="{BASE}/{to[0]}/">{label or to[1]}</a>', block)
        return re.sub(r'<img [^>]*>', lambda m: to[2], block, count=1)

    def img(block):
        return re.search(r'<img [^>]*>', block).group(0)

    # desktop rows (photo side alternates): rows N and P, then the "Partner with us" row
    n0, n1 = cut("605d91d", "511878e")
    p0, p1 = cut("511878e", "abfbd32")
    rowN, rowP = html[n0:n1], html[p0:p1]
    N = ("nurturing-excellence", "Nurturing Excellence", img(rowN))
    P = ("philanthropy-partners", "Philanthropy Partners", img(rowP))
    W = (SLUG, TITLE, HOME_IMG)
    desktop = swap(rowN, N, W) + swap(rowP, P, N) + swap(rowN, N, P)

    # mobile list: heading "n) Name" + photo
    m0, m1 = cut("1ebe1b1", "d4bd0d7")
    q0, q1 = cut("d4bd0d7", "ac4be8b")
    mobN, mobP = html[m0:m1], html[q0:q1]
    mobile = (swap(mobN, N, W, f"4) {TITLE}") + mobN.replace("4) Nurturing", "5) Nurturing")
              + mobP.replace("5) Philanthropy", "6) Philanthropy"))

    assert m1 == q0 and q1 < n0 and n1 == p0
    html = html[:m0] + mobile + html[q1:n0] + desktop + html[p1:]
    f.write_text(html)


def main():
    # gather every listing box from every category page, then redistribute by MOVES
    boxes = {cat: [] for cat in CATS + [SLUG]}
    incoming = {cat: [] for cat in boxes}
    for cat in boxes:
        f = ROOT / cat / "index.html"
        g = GRID_RE.search(f.read_text()) if f.exists() else None
        for a in ART_RE.findall(g.group(2)) if g else []:
            dest = MOVES.get(project_slug(a), cat)
            if dest != cat:
                a = re.sub(r'data-category="[^"]*"', f'data-category="{dest}"',
                           re.sub(r'pj-categs-[\w-]+', f'pj-categs-{dest}', a))
            (boxes[dest] if dest == cat else incoming[dest]).append(a)
    for sp in SPLIT:
        make_split(sp)
        if not any(project_slug(a) == sp["new"] for a in boxes[sp["cat"]]):
            orig = next(a for lst in boxes.values() for a in lst if project_slug(a) == sp["slug"])
            incoming[sp["cat"]].append(split_box(orig, sp))
    for cat in boxes:  # boxes already on a page keep their order; newly moved ones go last
        boxes[cat] += incoming[cat]
    found = {project_slug(a) for lst in boxes.values() for a in lst}
    missing = [s for s in MOVES if s not in found]
    if missing:
        raise SystemExit(f"not found on any category page: {missing}")

    def fill(html, cat):
        g = GRID_RE.search(html)
        return html[:g.start(2)] + "".join(boxes[cat]) + html[g.end(2):]

    for cat in CATS:
        f = ROOT / cat / "index.html"
        if GRID_RE.search(f.read_text()):
            f.write_text(fill(f.read_text(), cat))

    # build the new category page from the template
    html = (ROOT / TEMPLATE / "index.html").read_text()
    html = html.replace("Livelihood Enhancement &#8211;", f"{TITLE} &#8211;")
    html = html.replace('<h1 class="entry-title">Livelihood Enhancement</h1>', f'<h1 class="entry-title">{TITLE}</h1>')
    html = html.replace("%2Flivelihood-enhancement%2F", f"%2F{SLUG}%2F")
    html = html.replace(f'rel="canonical" href="{BASE}/livelihood-enhancement/"', f'rel="canonical" href="{BASE}/{SLUG}/"')
    html = html.replace("\t\t'livelihood-enhancement', ", f"\t\t'{SLUG}', ")
    html = html.replace("background-image:url(/motivationforexcellence/wp-content/uploads/2024/01/b79d6c_77c46a0159224022bfb6572e44dbd35amv2-1.webp",
                        "background-image:url(/motivationforexcellence/wp-content/uploads/2026/11/womens-empowerment-1024x600.jpg")
    html = html.replace(" current-menu-item page_item page-item-12515 current_page_item", "")
    out = ROOT / SLUG / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(add_menu(fill(html, SLUG), current=True))

    # menu on every page; Categories + Area of Work on moved project pages
    pages = [p for p in ROOT.rglob("index.html") if not p.relative_to(ROOT).parts[0].startswith("wp-")]
    for p in pages:
        if p == out:
            continue
        html = add_menu(p.read_text())
        rel = p.relative_to(ROOT).parts
        split_dest = {sp["new"]: sp["cat"] for sp in SPLIT}
        if len(rel) == 3 and rel[0] == "project" and (rel[1] in MOVES or rel[1] in split_dest):
            dest = MOVES.get(rel[1]) or split_dest[rel[1]]
            label = CAT_LABEL[dest]
            html = re.sub(r'(<span class="cmsmasters_project_category"><a href=")[^"]*(" class="cmsmasters_cat_color[^"]*" rel="category tag">)[^<]*(</a>)',
                          rf'\g<1>{BASE}/{dest}/\g<2>{label}\g<3>', html)
            html = re.sub(r'pj-categs-[\w-]+', f'pj-categs-{dest}', html)
            html = re.sub(r'(<div class="project_features_item_title">Area of Work</div><div class="project_features_item_desc">)[^<]*(</div>)',
                          rf'\g<1>{label}\g<2>', html)
        p.write_text(html)
    update_home()
    print(f"menu on {len(pages)} pages; moves: {MOVES}")


if __name__ == "__main__":
    main()
