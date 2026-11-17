#!/usr/bin/env python3
"""Build the files for the real website (www.motivationforexcellence.org on GitHub Pages).

The repository itself is the GitHub Pages preview, which lives under
/valenciawineries/ and is hidden from search engines. This script copies it to
an output folder and turns it into the real site:

  * links point at the domain root (/about-us/ instead of /valenciawineries/about-us/)
  * the preview's "noindex,nofollow" tag is removed
  * canonical / social / search-engine addresses become https://valenciawineries.org/...
  * robots.txt, sitemap.xml, 404.html and .htaccess are added
  * images and plugin files no page uses are left out
  * a zip ready to upload is written next to the folder

    python3 tools/build_live.py <output-folder>            (Hostinger: .htaccess + zip)
    python3 tools/build_live.py --github <output-folder>   (GitHub Pages)

Hostinger upload: File Manager > public_html > upload the zip > Extract.
GitHub Pages: the output folder is a clone of vivekragavan/valenciawineries-live;
its .git is kept, so afterwards commit and push there to publish. GitHub Pages
ignores .htaccess, so old addresses get small forwarding pages instead.
"""
import datetime
import pathlib
import re
import shutil
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://www.motivationforexcellence.org"
GITHUB_DOMAIN = "www.motivationforexcellence.org"
BASE = "/motivationforexcellence/"


SKIP_TOP = {".git", "tools", "README.md", "CHANGES.md", ".nojekyll", ".gitignore", ".DS_Store"}

# Old WordPress addresses that people or search engines may still have.
HTACCESS = """# valenciawineries.org - static site (replaced WordPress {date})
Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html

<IfModule mod_alias.c>
Redirect 301 /product/2009-white-wine-soave-750ml/ /product/cabernet-sauvignon-2017/
Redirect 301 /shop-1/ /shop/
Redirect 301 /cart/ /shop/
Redirect 301 /checkout/ /shop/
Redirect 301 /my-account/ /shop/
Redirect 301 /product-category/reserve/ /shop/
Redirect 301 /terms-and-conditions/ /privacy-policy/
Redirect 301 /refund_returns/ /privacy-policy/
RedirectMatch 301 ^/wp-content/uploads/(.*)$ /storage/$1
RedirectMatch 301 ^/(wp-admin|wp-login\\.php|newlogin|login)(/.*)?$ /
</IfModule>

<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType text/html "access plus 10 minutes"
ExpiresByType text/css "access plus 30 days"
ExpiresByType application/javascript "access plus 30 days"
ExpiresByType image/jpeg "access plus 30 days"
ExpiresByType image/png "access plus 30 days"
ExpiresByType image/webp "access plus 30 days"
ExpiresByType image/svg+xml "access plus 30 days"
ExpiresByType font/woff2 "access plus 1 year"
</IfModule>
"""


# Same redirects as .htaccess, as forwarding pages (GitHub Pages has no server redirects).
FORWARDS = {
    **{p: "/" for p in ("shop/", "shop-2/", "home-store/", "cart/", "checkout/", "my-account/", "campaigns/",
                        "donate-confirmation/", "news/", "events/", "projects-3/", "wp-admin/", "wp-login.php/")},
    "project/bridges-of-sports-2/": "/project/bridges-of-sports/",
    "pj-categs/healthcare/": "/healthcare/", "pj-categs/education-training/": "/education-training/",
    "pj-categs/education/": "/education-training/", "pj-categs/eurturing-excellence/": "/nurturing-excellence/",
    "pj-categs/livelihood-enhancement/": "/livelihood-enhancement/",
}


def forward_page(target: str) -> str:
    url = SITE + target
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Motivation for Excellence</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace("{target}" + location.hash);</script>
</head><body><p>This page has moved to <a href="{target}">{url}</a>.</p></body></html>
"""


def rewrite_html(html: str, path: str) -> str:
    html = re.sub(r'<meta name="robots" content="noindex,nofollow">\r?\n?', "", html)
    html = html.replace("&#8211; motivationforexcellence</title>", "&#8211; Motivation for Excellence</title>")
    html = html.replace(BASE, "/").replace("\\/motivationforexcellence\\/", "\\/")
    html = html.replace('"url":"/motivationforexcellence"', '"url":"/"')
    # absolute addresses for search engines and link previews
    html = re.sub(r'(<link rel="canonical" href=")/', r"\1" + SITE + "/", html)
    html = re.sub(r'(<meta property="og:url" content=")/', r"\1" + SITE + "/", html)

    def ld(m: re.Match) -> str:
        body = re.sub(r'("(?:@id|url|item)":")\\/', r"\1https:\\/\\/www.motivationforexcellence.org\\/", m.group(2))
        body = re.sub(r'("(?:@id|url|item)":")/', r"\1" + SITE + "/", body)
        return m.group(1) + body + m.group(3)

    html = re.sub(r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)', ld, html, flags=re.S)
    return html


def make_404(contact_html: str) -> str:
    h = re.sub(r"<title>.*?</title>", "<title>Page not found &#8211; Motivation for Excellence</title>", contact_html, flags=re.S)
    h = h.replace('<h1 class="entry-title">Contact Us</h1>', '<h1 class="entry-title">Page not found</h1>', 1)
    h = re.sub(r'<link rel="canonical"[^>]*>\r?\n?', "", h)
    h = re.sub(r'<meta (name="description"|property="og:[a-z:]+"|name="twitter:[a-z:]+")[^>]*>\r?\n?', "", h)
    h = re.sub(r'<script type="application/ld\+json"[^>]*>.*?</script>\r?\n?', "", h, flags=re.S)
    h = re.sub(r"(<head[^>]*>)", r'\1\n<meta name="robots" content="noindex">', h, count=1)
    # contact block = optional address paragraph + "For more information..." paragraph -> one 404 message
    old = re.search(r'<p style="text-align:center;font-size:20px;margin:30px.*?For more information, contact us at <a [^>]*href="mailto:[^"]+">[^<]+</a></p>', h, flags=re.S)
    h = h[:old.start()] + ('<p style="text-align:center;font-size:20px;margin:30px 0 40px;">'
                           "Sorry, we couldn't find that page. Please use the menu above, or go to our "
                           '<a href="/">home page</a>.</p>') + h[old.end():]
    return h

def referenced_files(out: pathlib.Path) -> set:
    """Every file the pages need: links in the HTML plus url(...) inside CSS, recursively."""
    keep, todo = set(), []

    def add(ref: str, rel_to: pathlib.Path):
        ref = ref.strip().strip("'\"").split("#")[0].split("?")[0]
        if not ref or ref.startswith(("data:", "http:", "https:", "//", "mailto:")):
            return
        p = (out / ref.lstrip("/")) if ref.startswith("/") else (rel_to.parent / ref)
        try:
            p = p.resolve()
            is_file = p.is_file()
        except OSError:  # e.g. a long meta description, not a file name
            return
        if is_file and p not in keep:
            keep.add(p)
            if p.suffix == ".css":
                todo.append(p)

    for page in out.glob("**/*.html"):
        text = page.read_text(encoding="utf-8")
        for r in re.findall(r'(?:src|href|data-src|content)=["\']([^"\']+)["\']', text):
            add(r, page)
        for s in re.findall(r'srcset=["\']([^"\']+)["\']', text):
            for part in s.split(","):
                add(part.strip().split(" ")[0], page)
        for r in re.findall(r"url\(([^)]+)\)", text):
            add(r, page)
        for r in re.findall(r'["\'(](/(?:core|storage|lib|wp-content)/[^"\')\s]+)', text.replace("\\/", "/")):
            add(r, page)
    while todo:
        css = todo.pop()
        text = css.read_text(encoding="utf-8", errors="ignore")
        for r in re.findall(r"url\(([^)]+)\)", text):
            add(r, css)
        for r in re.findall(r'@import\s+["\']([^"\']+)["\']', text):
            add(r, css)
    return keep


def main() -> None:
    global SITE
    args = sys.argv[1:]
    github = "--github" in args
    args = [a for a in args if a != "--github"]
    if len(args) != 1:
        sys.exit(__doc__)
    if github:
        SITE = "https://" + GITHUB_DOMAIN
    out = pathlib.Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for item in out.iterdir():  # empty the folder but keep its git history
        if item.name == ".git":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()

    for item in ROOT.iterdir():
        if item.name in SKIP_TOP:
            continue
        dest = out / item.name
        shutil.copytree(item, dest) if item.is_dir() else shutil.copy2(item, dest)

    for page in out.glob("**/index.html"):
        with open(page, encoding="utf-8", newline="") as fh:
            html = fh.read()
        with open(page, "w", encoding="utf-8", newline="") as fh:
            fh.write(rewrite_html(html, str(page.relative_to(out).parent)))

    (out / "404.html").write_text(make_404((out / "contact-us/index.html").read_text(encoding="utf-8")), encoding="utf-8")

    today = datetime.date.today().isoformat()
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    pages = sorted(p.relative_to(out).parent.as_posix() for p in out.glob("**/index.html")
                   if not p.relative_to(out).parts[0].startswith("wp-") and "moved to" not in p.read_text(encoding="utf-8")[:2000])
    urls = "".join(f"  <url><loc>{SITE}/{'' if p == '.' else p + '/'}</loc><lastmod>{today}</lastmod></url>\n" for p in pages)
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    if github:
        (out / "CNAME").write_text(GITHUB_DOMAIN + "\n")
        (out / ".nojekyll").write_text("")
        for path, target in FORWARDS.items():
            (out / path).mkdir(parents=True, exist_ok=True)
            (out / path / "index.html").write_text(forward_page(target), encoding="utf-8")
    else:
        (out / ".htaccess").write_text(HTACCESS.format(date=today))

    # leave out files that nothing uses
    keep = referenced_files(out)
    keep |= {(out / n).resolve() for n in ("404.html", "robots.txt", "sitemap.xml", ".htaccess", "CNAME", ".nojekyll")}
    keep |= {p.resolve() for p in out.glob("**/index.html")}
    # files that scripts load on the fly (not referenced in HTML/CSS)
    for pattern in ("wp-content/plugins/elementor/assets/js/**/*", "wp-content/plugins/elementor-pro/assets/js/**/*",
                    "wp-content/plugins/LayerSlider/assets/static/layerslider/skins/v5/*",
                    "wp-includes/js/wp-emoji-release.min.js"):
        keep |= {p.resolve() for p in out.glob(pattern) if p.is_file()}
    removed = 0
    for f in sorted(out.rglob("*")):
        if ".git" in f.relative_to(out).parts:
            continue
        if f.is_file() and f.resolve() not in keep:
            f.unlink()
            removed += 1
    for d in sorted((p for p in out.rglob("*") if p.is_dir() and ".git" not in p.relative_to(out).parts),
                    key=lambda p: len(p.parts), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()

    files = [f for f in out.rglob("*") if f.is_file() and ".git" not in f.relative_to(out).parts]
    size = sum(f.stat().st_size for f in files)
    if github:
        print(f"{len(files)} files, {size / 1e6:.1f} MB in {out} ({removed} unused files left out)")
        return
    zpath = out.with_suffix(".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(files):
            z.write(f, f.relative_to(out).as_posix())
    print(f"{len(files)} files, {size / 1e6:.1f} MB in {out} ({removed} unused files left out)")
    print(f"zip: {zpath} ({zpath.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
