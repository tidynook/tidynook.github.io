#!/usr/bin/env python3
"""
Tidy Nook - rebuild index.html, sitemap.xml (and robots.txt / 404.html if missing)
from every article-*.html file in this folder.

How to use for each NEW article:
  1. Put the new article-<category>-<name>.html file in this folder.
  2. Run:  python3 update_site.py
  3. Upload/commit the changed files (the new article, index.html, sitemap.xml) to GitHub.

Category = the 2nd word of the file name (article-KITCHEN-spice-rack.html -> Kitchen).
Add a new category label below in CATEGORIES if you start a new one.
"""
import re, glob, html, json, os, datetime
import xml.etree.ElementTree as ET

BASE = "https://tidynook.github.io/"
STATIC_PAGES = ["about", "affiliate-disclosure", "privacy-policy"]
CATEGORIES = [("kitchen", "Kitchen"), ("bathroom", "Bathroom"),
              ("closet", "Closet &amp; Small Space"), ("travel", "Travel")]
HOME_TITLE = "Tidy Nook: Small-Space Organizing Buying Guides"
HOME_DESC = ("Tidy Nook buying guides for kitchen, bathroom, closet and travel storage. "
             "Each guide compares products and shows what to measure and check before buying.")
GA_ID = "G-NQCXQH03M7"

esc = lambda x: html.escape(x, quote=False)
here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)

def lastmod(s):
    m = re.search(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})"', s)
    if m: return m.group(1)
    m = re.search(r'Updated (\w+) (\d{4})', s)
    if m:
        try:
            return datetime.datetime.strptime(m.group(1) + " " + m.group(2), "%B %Y").strftime("%Y-%m-01")
        except ValueError:
            pass
    return datetime.date.today().isoformat()

arts = []
for f in sorted(glob.glob("article-*.html")):
    s = open(f, encoding="utf-8").read()
    slug = f[:-5]
    h1 = re.search(r"<h1>(.*?)</h1>", s)
    d = re.search(r'name="description" content="(.*?)"', s)
    if not (h1 and d):
        print("SKIPPED (no h1 or meta description):", f); continue
    arts.append(dict(slug=slug, cat=slug.split("-")[1], title=html.unescape(h1.group(1)),
                     desc=html.unescape(d.group(1)), mod=lastmod(s)))
    if len(arts[-1]["desc"]) != 153:
        print("NOTE: meta description is %d chars (not 153): %s" % (len(arts[-1]["desc"]), f))

known = {k for k, _ in CATEGORIES}
cats = CATEGORIES + [(c, c.capitalize()) for c in sorted({a["cat"] for a in arts} - known)]
sections = ""
for key, label in cats:
    items = "".join('<li><a href="%s%s">%s</a><br><span class="d">%s</span></li>\n'
                    % (BASE, a["slug"], esc(a["title"]), esc(a["desc"])) for a in arts if a["cat"] == key)
    if items:
        sections += '<h2>%s</h2>\n<ul class="list">\n%s</ul>\n' % (label, items)

ld = json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "Tidy Nook", "url": BASE}, indent=1)
index = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<style>
:root{--ink:#1f2a2e;--muted:#5b6a70;--line:#dde3e5;--bg:#fbfcfc;--accent:#1f6f78;--note:#f1f6f6}
*{box-sizing:border-box}body{margin:0;font-family:Georgia,'Times New Roman',serif;color:var(--ink);background:var(--bg);line-height:1.65}
header,footer{max-width:720px;margin:0 auto;padding:18px 20px;font-family:system-ui,Arial,sans-serif;font-size:14px}
header{display:flex;gap:18px;align-items:center;border-bottom:1px solid var(--line)}header b{margin-right:auto;font-size:17px}
a{color:var(--accent)}main{max-width:720px;margin:0 auto;padding:8px 20px 40px}
h1{font-size:2rem;line-height:1.2;margin:.6em 0 .2em}h2{font-size:1.4rem;margin:1.8em 0 .4em}
.meta{font-family:system-ui,Arial,sans-serif;font-size:14px;color:var(--muted)}
.disc{background:var(--note);border-left:4px solid var(--accent);padding:12px 14px;font-size:15px;margin:18px 0;font-family:system-ui,Arial,sans-serif}
.list{list-style:none;padding:0;margin:0}.list li{padding:10px 0;border-bottom:1px solid var(--line)}.list a{font-weight:600}
.d{font-family:system-ui,Arial,sans-serif;font-size:14px;color:var(--muted)}
footer{border-top:1px solid var(--line);color:var(--muted)}
</style><!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '%s');
</script>
<script type="application/ld+json">
%s
</script>
</head><body>
<header><b>TidyNook</b><a href="%s">Home</a><a href="%sabout">About</a><a href="%saffiliate-disclosure">Disclosure</a><a href="%sprivacy-policy">Privacy</a></header>
<main>
<h1>Tidy Nook: Small-Space Organizing Guides</h1>
<p class="meta">Buying guides for kitchen, bathroom, closet and travel storage</p>
<p class="disc">As an Amazon Associate, Tidy Nook earns from qualifying purchases. This means we may earn a small commission if you buy through our links, at no extra cost to you.</p>
<p>Each guide compares products using the features listed on their Amazon pages, and shows what to measure and check before you order.</p>
%s</main>
<footer>© 2026 Tidy Nook · <a href="%sabout">About</a> · <a href="%saffiliate-disclosure">Affiliate Disclosure</a> · <a href="%sprivacy-policy">Privacy Policy</a></footer>
</body></html>
''' % (esc(HOME_TITLE), HOME_DESC, BASE, GA_ID, GA_ID, ld, BASE, BASE, BASE, BASE, sections, BASE, BASE, BASE)
open("index.html", "w", encoding="utf-8").write(index)

newest = max(a["mod"] for a in arts)
urls = [(BASE, newest)] + [(BASE + p, newest) for p in STATIC_PAGES] + [(BASE + a["slug"], a["mod"]) for a in arts]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
     "".join("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n  </url>\n" % u for u in urls) + "</urlset>\n"
ET.fromstring(sm.encode())
open("sitemap.xml", "w", encoding="utf-8").write(sm)

if not os.path.exists("robots.txt"):
    open("robots.txt", "w").write("User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % BASE)
if not os.path.exists("404.html"):
    open("404.html", "w", encoding="utf-8").write('''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Page Not Found - Tidy Nook</title>
<meta name="robots" content="noindex">
<style>body{margin:0;font-family:Georgia,'Times New Roman',serif;color:#1f2a2e;background:#fbfcfc;line-height:1.65}main{max-width:720px;margin:0 auto;padding:60px 20px}a{color:#1f6f78}</style>
</head><body>
<main>
<h1>Page not found</h1>
<p>The page you are looking for does not exist or has moved. Go back to the <a href="%s">Tidy Nook home page</a> to browse all guides.</p>
</main>
</body></html>
''' % BASE)

print("Done: %d articles listed in index.html, %d URLs in sitemap.xml" % (len(arts), len(urls)))
