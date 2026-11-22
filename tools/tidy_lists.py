#!/usr/bin/env python3
"""Tidy text that was pasted into WordPress from the partners' old Wix sites.

1. Numbered lists (<ol>) whose items each wrap a <p>: the theme then shows "01." on its own line
   with a gap after every item. Unwrap the <p> so number and text share a line (as on the IPH page).
   Bulleted lists (<ul>) are left alone.
2. Empty Wix spacer paragraphs (<p><span class="wixGuard">&#8203;</span></p>) that show as
   extra white lines: removed.

Rerunnable: python3 tools/tidy_lists.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPACER = re.compile(r'[ \t]*<p[^>]*>\s*<span class="wixGuard">​</span>\s*</p>\n?')
TOKEN = re.compile(r'<(/?)(ol|ul)\b[^>]*>|<li>\s*<p( class="[^"]*")?>(.*?)</p>', re.S)

def unwrap(s):
    out, pos, stack = [], 0, []
    for m in TOKEN.finditer(s):
        if m.group(2):  # list open/close
            if m.group(1):
                if stack: stack.pop()
            else:
                stack.append(m.group(2))
            continue
        if stack and stack[-1] == "ol":
            out.append(s[pos:m.start()])
            out.append(f'<li{m.group(3) or ""}>{m.group(4)}')
            pos = m.end()
    out.append(s[pos:])
    return "".join(out)

changed = []
for page in sorted((ROOT / "project").glob("*/index.html")):
    s = page.read_text(encoding="utf-8")
    t = unwrap(SPACER.sub("", s))
    if t != s:
        page.write_text(t, encoding="utf-8"); changed.append(page.parent.name)
print("pages changed:", len(changed), changed)
