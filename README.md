# motivationforexcellence.org — static copy

A plain-HTML copy of the WordPress site motivationforexcellence.org (Hostinger),
made so the site can run on GitHub Pages without WordPress.

- Preview (hidden from search engines): https://vivekragavan.github.io/motivationforexcellence/
- `tools/mirror.py <folder>` re-copies the live site (pages from the sitemap plus internal links).
- Removed at the owner's request: shop, cart, checkout, my-account, products, campaigns, donations, and the theme demo content (15 demo projects, duplicate Bridges of Sports, events, profiles, news posts, categories/tags). `tools/clean_demo.py` replaces the demo sidebar and footer widgets on the gallery pages with the real footer.

This is separate from `vivekragavan/motivation-for-excellence` (an Astro rewrite).
