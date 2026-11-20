#!/usr/bin/env python3
"""Add the November 2026 MoU write-ups to the static site.

Usage: python3 tools/add_writeups.py <MFE_New_Writeups folder>

- new_pages/*.md     -> new project pages under project/<slug>/, cloned from an
                        existing project page, plus a card on the section listing
- page_updates/*.md  -> replaces "The project supported by MFE" on the existing
                        page and updates the Project details box

The write-ups themselves are not kept in this repo (they hold agreement file
names and review notes that must not be published). Run once on a fresh tree;
re-running on already-updated pages is refused.
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
B = "/motivationforexcellence/"
PH = B + "wp-content/uploads/placeholders/"
TEMPLATE = ROOT / "project/central-square-foundation/index.html"  # postid 12231

SECTION = {"Education & Training": "education-training",
           "Livelihood Enhancement": "livelihood-enhancement",
           "Healthcare": "healthcare"}

# Choices made where the write-ups leave it open (see the summary to the owner)
SLUG = {"ashoka-university-olympiadx": "ashoka-university"}  # keep the placeholder name out of the URL
NEW_IDS = iter(range(13901, 13999))


# ---------------------------------------------------------------- markdown
def parse(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        if re.match(r"^\w+:", line):
            k, v = line.split(":", 1)
            meta[k] = re.sub(r"\s+#.*$", "", v).strip()
    body = re.sub(r"<!--.*?-->", "", m.group(2), flags=re.S)  # review notes
    sections, cur = {}, None
    for line in body.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    return meta, sections


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = s.replace("'", "’")
    return s


def to_html(lines, skip_heading=None):
    """Write-up section -> the paragraph markup used on the existing pages."""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
        if items:
            out.append("<ul>\n" + "\n".join("<li>" + inline(i) + "</li>" for i in items) + "\n</ul>")
            items.clear()

    for line in lines:
        line = line.rstrip()
        if not line:
            flush()
        elif re.match(r"^\(Keep the existing .*\)$", line):  # instruction, not content
            flush()
        elif line.startswith("### "):
            flush()
            if line[4:].strip() != skip_heading:
                out.append("<p><strong><em>" + inline(line[4:].strip()) + "</em></strong></p>")
        elif line.startswith("- "):
            para and flush()
            items.append(line[2:])
        else:
            para.append(line)
    flush()
    return "\n\n".join(out)


def split_subs(lines):
    """Section lines -> (lines before the first ###, [(### heading, lines), ...])."""
    pre, subs = [], []
    for line in lines:
        if line.startswith("### "):
            subs.append((line[4:].strip(), []))
        else:
            (subs[-1][1] if subs else pre).append(line)
    return pre, subs


def after_first_para(lines):
    """Drop the first paragraph of a sub-section, keep the rest."""
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and lines[i].strip():
        i += 1
    return lines[i:]


def project_heading(sections):
    name = next(k for k in sections if k.lower().startswith("the project"))
    return name, "<p><strong>" + inline(name) + ":</strong></p>"


# ---------------------------------------------------------------- sidebar
def set_detail(page, title, value):
    pat = (r'(<div class="project_features_item_title">' + re.escape(title) +
           r'</div><div class="project_features_item_desc">)[^<]*(</div>)')
    new, n = re.subn(pat, lambda m: m.group(1) + html.escape(value, quote=False) + m.group(2), page)
    assert n == 1, title
    return new


def sidebar(meta):
    sec = SECTION[meta["category"]]
    cat = html.escape(meta["category"])
    return ('<div class="project_sidebar"><div class="project_details entry-meta"><h4 class="project_details_title">Project details</h4>'
            '<div class="project_details_item"><div class="project_details_item_title">Categories:</div><div class="project_details_item_desc">'
            f'<span class="cmsmasters_project_category"><a href="{B}{sec}/" class="cmsmasters_cat_color" rel="category tag">{cat}</a></span></div></div></div>'
            '<div class="project_features entry-meta">'
            + "".join(f'<div class="project_features_item"><div class="project_features_item_title">{t}</div>'
                      f'<div class="project_features_item_desc">{html.escape(meta[k], quote=False)}</div></div>'
                      for t, k in (("Area of Work", "area_of_work"), ("Location", "location"),
                                   ("Supported by MFE since", "supported_by_mfe_since")))
            + "</div></div>")


# ---------------------------------------------------------------- new pages
def new_page(tpl, meta, sections, slug, pid, title, nav):
    esc = html.escape(title)
    name, head = project_heading(sections)
    site = meta.get("website", "")
    logo = (f'<img loading="lazy" decoding="async" class="alignnone size-thumbnail" src="{PH}logo-150x150.svg" '
            f'alt="{esc} logo (placeholder)" width="150" height="150" />')
    if site.startswith("http"):
        logo = f'<a href="{html.escape(site)}" target="_blank" rel="noopener">{logo}</a>'
    content = "\n\n".join(["<p>" + logo + "</p>", to_html(sections["About"]), head, to_html(sections[name])])

    s = tpl
    s = s.replace("<title>Central Square Foundation &#8211;", f"<title>{esc} &#8211;")
    s = s.replace("project%2Fcentral-square-foundation%2F", f"project%2F{slug}%2F")
    s = s.replace("project/central-square-foundation/", f"project/{slug}/")
    s = s.replace("wp/v2/project/12231", f"wp/v2/project/{pid}").replace("?p=12231", f"?p={pid}")
    s = s.replace("postid-12231", f"postid-{pid}")
    s = s.replace('<h1 class="entry-title">Central Square Foundation</h1>', f'<h1 class="entry-title">{esc}</h1>')
    s = re.sub(r'<article id="post-12231" class="([^"]*?)post-12231 ([^"]*?)pj-categs-[\w-]+"',
               lambda m: f'<article id="post-{pid}" class="{m.group(1)}post-{pid} {m.group(2)}pj-categs-{SECTION[meta["category"]]}"', s)
    a = s.index('<figure class="cmsmasters_img_wrap">')
    b = s.index('<div class="project_sidebar">')
    c = s.index("</article>", b)
    figure = (f'<figure class="cmsmasters_img_wrap"><img fetchpriority="high" width="1024" height="589" '
              f'src="{PH}banner-1024x589.svg" class=" wp-post-image" alt="{esc} (photo to come)" title="{esc}" decoding="async" /></figure>')
    s = (s[:a] + figure + '<div class="cmsmasters_project_content entry-content">\n' + content + "\n</div></div>"
         + sidebar(meta) + s[c:])
    s = re.sub(r'<aside class="post_nav">.*?</aside>', nav, s, flags=re.S)
    assert "Central Square" not in s and "12231" not in s, slug
    return s


def card(pid, slug, title, sec):
    esc = html.escape(title)
    return f'''
<!-- Start Standard Project -->

<article id="post-{pid}" class="cmsmasters_project_grid post-{pid} project type-project status-publish format-standard has-post-thumbnail hentry pj-categs-{sec}" data-category="{sec}">
	<div class="project_outer">
	<figure class="cmsmasters_img_rollover_wrap preloader"><img loading="lazy" decoding="async" width="580" height="490" src="{PH}card-580x490.svg" class="full-width wp-post-image" alt="{esc} (photo to come)" title="{esc}" /><div class="cmsmasters_img_rollover"><a href="{B}project/{slug}/" title="{esc}" class="cmsmasters_open_post_link cmsmasters-icon-export-3"></a></div></figure><div class="project_inner"><header class="cmsmasters_project_header entry-header"><h3 class="cmsmasters_project_title entry-title"><a href="{B}project/{slug}/">{esc}</a></h3></header></div><span class="dn meta-date">20261119120000</span>	</div>
</article>
<!-- Finish Standard Project -->
'''


# ---------------------------------------------------------------- updates
HEAD_RE = re.compile(r"<p(?: class=\"wp-block-paragraph\")?><(strong|b)>The project supported by MFE:\s*</\1></p>")


def update_page(slug, meta, sections):
    path = ROOT / "project" / slug / "index.html"
    s = path.read_text()
    a = s.index('<div class="cmsmasters_project_content entry-content">')
    b = s.index('<div class="project_sidebar">', a)
    name, head = project_heading(sections)

    pre, subs = split_subs(sections[name])
    if slug == "ramakrishna-mission":  # the existing project + the renewal = two projects
        head = head.replace("The project ", "The projects ")
    H = lambda t: "<p><strong><em>" + inline(t) + "</em></strong></p>"
    sub = lambda i, skip=0: to_html(subs[i][1][skip:])  # body of sub-section i
    full = lambda i: H(subs[i][0]) + "\n\n" + sub(i)

    if slug == "rocket-learning":  # no project section yet; it goes above "Reports and Media Features"
        # "Earlier support" is left out: the page's About already says it
        i = s.index("<p><strong><u>Reports and Media Features", a, b)
        s = s[:i] + head + "\n\n" + full(0) + "\n\n" + s[i:]
    else:
        # The existing project write-up stays word for word; the new projects are added around it.
        m = HEAD_RE.search(s, a, b)
        assert m, f"{slug}: project heading not found (already updated?)"
        ends = [s.find(t, m.end(), b) for t in ("<p>&nbsp;</p>", "<p></p>", '<form id="gal_front_form', "</div>")]
        end = min(e for e in ends if e != -1)
        old = s[m.end():end].strip()
        parts = {
            # intro, existing Tribal Utthan, then only the new phase + the three new projects
            "baif": lambda: [to_html(pre), old, H("Tribal Utthan: the next phase, 54 new villages in Dhanora block"),
                     to_html(after_first_para(subs[0][1])), full(1), full(2), full(3)],
            # existing project first, then the new one (same order on every page)
            "central-square-foundation": lambda: [old, full(0)],          # existing grant, then new 2025 partnership
            "mantra4change": lambda: [old, "<p>The EduMentum programme has been extended to March 2027.</p>", full(0)],
            "ramakrishna-mission": lambda: [old, H("The Awakened Citizen Programme, 2025–2028: making value education self-sustaining"),
                                    to_html(after_first_para(subs[0][1]))],
            "quest": lambda: [old, sub(0), full(1)],                        # Palavee + extension sentence, then campus
        }[slug]()
        s = s[:m.start()] + head + "\n\n" + "\n\n".join(p for p in parts if p) + "\n\n" + s[end:]

    s = set_detail(s, "Area of Work", meta["area_of_work"])
    s = set_detail(s, "Location", meta["location"])
    s = set_detail(s, "Supported by MFE since", meta["supported_by_mfe_since"])
    path.write_text(s)


# ---------------------------------------------------------------- main
def main():
    src = pathlib.Path(sys.argv[1])
    tpl = TEMPLATE.read_text()

    news = []
    for f in sorted((src / "new_pages").glob("*.md")):
        meta, sections = parse(f)
        slug = SLUG.get(meta["suggested_slug"], meta["suggested_slug"]).strip("/").split("/")[-1]
        title = next(l[2:].strip() for l in f.read_text().splitlines() if l.startswith("# "))
        news.append((slug, next(NEW_IDS), title, meta, sections))

    for i, (slug, pid, title, meta, sections) in enumerate(news):
        assert not (ROOT / "project" / slug).exists(), f"{slug} already exists"
        links = []
        if i > 0:
            links.append(f'<span class="cmsmasters_prev_post post_nav_prev_arrow"><a href="{B}project/{news[i-1][0]}/" rel="prev">{html.escape(news[i-1][2])}</a></span>')
        if i < len(news) - 1:
            links.append(f'<span class="cmsmasters_next_post post_nav_next_arrow"><a href="{B}project/{news[i+1][0]}/" rel="next">{html.escape(news[i+1][2])}</a></span>')
        nav = '<aside class="post_nav">' + "".join(links) + "</aside>"
        out = ROOT / "project" / slug / "index.html"
        out.parent.mkdir()
        out.write_text(new_page(tpl, meta, sections, slug, pid, title, nav))
        print("new     project/" + slug)

    by_sec = {}
    for slug, pid, title, meta, _ in news:
        by_sec.setdefault(SECTION[meta["category"]], []).append(card(pid, slug, title, SECTION[meta["category"]]))
    for sec, cards in by_sec.items():
        p = ROOT / sec / "index.html"
        s = p.read_text()
        marker = '</div><div class="cmsmasters_wrap_more_projects'
        assert s.count(marker) == 1
        s = s.replace(marker, "".join(cards) + "\n" + marker)
        p.write_text(s)
        print(f"listing {sec}: +{len(cards)}")

    for f in sorted((src / "page_updates").glob("*.md")):
        meta, sections = parse(f)
        slug = meta["existing_page"].rstrip("/").split("/")[-1]
        update_page(slug, meta, sections)
        print("updated project/" + slug)


if __name__ == "__main__":
    main()
