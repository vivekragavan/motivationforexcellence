#!/usr/bin/env python3
"""Swap the grey placeholder photos of the new project pages for real ones.

Usage: python3 tools/set_photos.py

For each slug in PHOTOS, wp-content/uploads/2026/11/<slug>-1024x589.jpg becomes the
header photo on project/<slug>/ and <slug>-580x490.jpg the photo on its box in the
section listing, so the box and the page show the same picture.
Safe to re-run. Photos are temporary, taken from the partners' own websites.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
B = "/motivationforexcellence/"
PH = B + "wp-content/uploads/placeholders/"
UP = B + "wp-content/uploads/2026/11/"

PHOTOS = {  # slug: where the photo came from (for the record)
    "ashoka-university": "x.ashoka.edu.in/about-us/ (AshokaX Overview page header), chosen by the owner",
    "madhi-foundation": "madhifoundation.org home page",
    "makerghat": "makerghat.org home page (cropped below the speech bubbles)",
    "stem-shiksha-foundation": "makerbhavanfoundation.org (Indian partner of Maker Bhavan Foundation)",
    "vidhya-vidhai-foundation": "owner's own photo IMG_2650.jpeg (Desktop)",
}


def main():
    for slug in PHOTOS:
        assert (ROOT / f"wp-content/uploads/2026/11/{slug}-1024x589.jpg").exists(), slug
        assert (ROOT / f"wp-content/uploads/2026/11/{slug}-580x490.jpg").exists(), slug

        p = ROOT / "project" / slug / "index.html"
        s = p.read_text()
        s, n = re.subn(r'src="' + re.escape(PH) + r'banner-1024x589\.svg" (class=" wp-post-image" alt="[^"]*?) \(photo to come\)"',
                       f'src="{UP}{slug}-1024x589.jpg" \\1"', s)
        if n:
            p.write_text(s)
        print(f"page    {slug}: {'set' if n else 'already set'}")

    for listing in ("education-training", "healthcare", "livelihood-enhancement", "nurturing-excellence"):
        p = ROOT / listing / "index.html"
        s = p.read_text()
        for slug in PHOTOS:
            pat = (r'(<figure class="cmsmasters_img_rollover_wrap preloader"><img [^>]*?)src="' + re.escape(PH) +
                   r'card-580x490\.svg"([^>]*?alt="[^"]*?) \(photo to come\)"([^>]*><div class="cmsmasters_img_rollover"><a href="'
                   + re.escape(B + f"project/{slug}/") + ")")
            s, n = re.subn(pat, f'\\1src="{UP}{slug}-580x490.jpg"\\2"\\3', s)
            if n:
                print(f"listing {listing}: {slug}")
        p.write_text(s)


if __name__ == "__main__":
    main()
