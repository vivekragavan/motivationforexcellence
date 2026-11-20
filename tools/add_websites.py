#!/usr/bin/env python3
"""Add a "Website" line to the Project details box on each partner page.

Usage: python3 tools/add_websites.py

Safe to re-run: an existing Website line is replaced. Pages not listed in
SITES (no official site found, or the only candidate was dead or a different
organisation) get no line.
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

SITES = {
    "321-education-foundation": "https://321-foundation.org/",
    "aaa": "https://arogyasathi.org/",
    "akanksha": "https://www.akanksha.org/",
    "akshar": "https://www.aksharfoundation.org/",
    "anand-niketan": "https://anandniketansevagram.wordpress.com/",
    "arch-dharampur": "https://www.archgujarat.org/",
    "ashoka-university": "https://www.ashoka.edu.in/",
    "baif": "https://baif.org.in/",
    "bridges-of-sports": "https://www.bridgesofsports.org/",
    "central-square-foundation": "https://www.centralsquarefoundation.org/",
    "chetana-vikas": "https://chetanavikas.org/",
    "dr-apj-kalam-library-mgims": "https://www.mgims.ac.in/",
    "educate-girls": "https://www.educategirls.ngo/",
    "farmers-for-forests": "https://www.farmersforforests.org/",
    "ffe": "https://www.ffe.org/",
    "gravis": "https://www.gravis.org.in/",
    "haqdarshak": "https://www.haqdarshak.com/",
    "harper-collins": "https://harpercollins.co.in/",
    "healing-fields-foundation": "https://healingfields.org/",
    "institute-for-psychological-health": "https://www.healthymind.org/",
    "karuna-trust": "https://www.karunatrust.org/",
    "lfe": "https://www.leadershipforequity.org/",
    "madhi-foundation": "https://www.madhifoundation.org/",
    "magic-bus": "https://www.magicbus.org/",
    "makerghat": "https://makerghat.org/",
    "mantra4change": "https://www.mantra4change.org/",
    "mswc": "https://mswcindia.org/",
    "oasis": "https://oasismovement.in/",
    "pradan": "https://www.pradan.net/",
    "pratham": "https://www.pratham.org/",
    "prayas": "https://www.tiss.edu/view/11/projects/prayas/",
    "quest": "https://quest.org.in/",
    "ramakrishna-mission": "https://belurmath.org/",
    "rocket-learning": "https://rocketlearning.org/",
    "room-to-read": "https://www.roomtoread.org/",
    "sankara-nethralaya": "https://www.sankaranethralaya.org/",
    "search-nirman": "https://searchforhealth.ngo/",
    "society-for-education-action-and-research-in-community-health": "https://searchforhealth.ngo/",
    "society-for-nutrition-education-and-health-action": "https://www.snehamumbai.org/",
    "stree-mukti-sanghatana": "https://streemuktisanghatana.org/",
    "tata-memorial-centre": "https://tmc.gov.in/",
    "tata-trusts-dmhp-rmhp": "https://www.tatatrusts.org/",
    "test-project": "https://www.swasthyaswaraj.org/",  # Swasthya Swaraj Society
    "vayam": "https://vayamindia.wordpress.com/",
    "vidhya-vidhai-foundation": "https://vidhyavidhai.org/",
    "wotr": "https://wotr.org/",
}

OLD = re.compile(r'<div class="project_features_item project_website">.*?</div></div>', re.S)


def label(url):
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    return host


def item(url):
    u = html.escape(url)
    return ('<div class="project_features_item project_website"><div class="project_features_item_title">Website</div>'
            f'<div class="project_features_item_desc"><a href="{u}" target="_blank" rel="noopener">{html.escape(label(url))}</a></div></div>')


def main():
    pages = sorted(p.name for p in (ROOT / "project").iterdir() if (p / "index.html").exists())
    unknown = set(SITES) - set(pages)
    assert not unknown, unknown
    for slug in pages:
        path = ROOT / "project" / slug / "index.html"
        s = OLD.sub("", path.read_text())
        if slug in SITES:
            b = s.index('<div class="project_sidebar">')
            f = s.find('<div class="project_features entry-meta">', b)
            if f != -1:
                end = s.index("</div></div></article>", f)  # close of project_features, then project_sidebar
                s = s[:end] + item(SITES[slug]) + s[end:]
            else:  # a few pages have only the Categories box: add a features box for the website
                end = s.index("</div></article>", b)  # close of project_sidebar
                s = s[:end] + '<div class="project_features entry-meta">' + item(SITES[slug]) + "</div>" + s[end:]
            print(f"{slug:65} {SITES[slug]}")
        else:
            print(f"{slug:65} (no website)")
        path.write_text(s)


if __name__ == "__main__":
    sys.exit(main())
