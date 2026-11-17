#!/usr/bin/env python3
"""Remove the theme's demo sidebar and demo footer widgets from the copied pages.

- Gallery pages: drop the right sidebar (demo search, categories, news, fake
  Brooklyn contact, Twitter error) and make the content full width.
- Every page with the demo "bottom" widget area (Lorem ipsum, campaigns, tag
  cloud, demo posts) gets the real bottom area from the homepage
  (Mumbai address, info@ email, logo).
- Project-category links point at the matching portfolio page instead of the
  removed category archives.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
B = "/motivationforexcellence/"

def block(s, start, end):
    i = s.find(start); j = s.find(end, i)
    return (i, j + len(end)) if i >= 0 and j >= 0 else None

home = (ROOT / "index.html").read_text(encoding="utf-8")
hb = block(home, "<!--  Start Bottom -->", "<!--  Finish Bottom -->")
real_bottom = home[hb[0]:hb[1]]

CATS = {"healthcare": "healthcare/", "education-training": "education-training/", "education": "education-training/",
        "eurturing-excellence": "nurturing-excellence/", "livelihood-enhancement": "livelihood-enhancement/"}

changed = 0
for p in ROOT.rglob("index.html"):
    rel = p.relative_to(ROOT).as_posix()
    if rel.startswith(("wp-", "tools/", ".git/")):
        continue
    s = p.read_text(encoding="utf-8"); o = s
    sb = block(s, "<!-- Start Sidebar -->", "<!-- Finish Sidebar -->")
    if sb:
        s = s[:sb[0]] + s[sb[1]:]
        s = s.replace('<div class="content_wrap r_sidebar">', '<div class="content_wrap fullwidth">', 1)
        s = s.replace('<div class="content entry">', '<div class="middle_content entry">', 1)
    if "sidebar_layout_14141414" in s:
        bb = block(s, "<!--  Start Bottom -->", "<!--  Finish Bottom -->")
        s = s[:bb[0]] + real_bottom + s[bb[1]:]
    def cat(m):
        t = CATS.get(m.group(2))
        return f'{m.group(1)}"{B}{t}"' if t else m.group(1).replace("href=", "data-href=") + '""'
    s = re.sub(r'(href=)"' + re.escape(B) + r'pj-categs/([^/"]+)/"', cat, s)
    s = re.sub(r'<link rel="alternate" type="text/calendar"[^>]*>\s*', "", s)
    s = re.sub(r'<link rel="alternate" type="application/(rss|atom)\+xml"[^>]*>\s*', "", s)  # WordPress feeds
    # cookie consent banner (site sets no tracking cookies; owner asked to remove it)
    for pat in (r'<script id="cookie-law-info-js-extra">.*?</script>\s*', r'<script id="cookie-law-info-js"[^>]*></script>\s*',
                r'<script id="ckyBannerTemplate" type="text/template">.*?</script>\s*', r'<style id="cky-style-inline">.*?</style>\s*',
                r'<link[^>]*cookie-law-info[^>]*>\s*'):
        s = re.sub(pat, "", s, flags=re.S)
    # "Contact Us" menu item jumped to the footer; owner wants it to open the Contact Us page
    s = s.replace('menu-item-13038 menu-item-depth-0"><a href="#footer">',
                  'menu-item-13038 menu-item-depth-0"><a href="' + B + 'contact-us/">')
    s = s.replace(B + "project/bridges-of-sports-2/",B + "project/bridges-of-sports/")  # duplicate page removed
    if s != o:
        p.write_text(s, encoding="utf-8"); changed += 1
print("pages changed:", changed)
