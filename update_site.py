#!/usr/bin/env python3
"""
Tidy Nook - keeps the HOME PAGE list and sitemap.xml in sync with the article files.

It NEVER touches the home page design. It only rewrites the part of index.html
between  <!--ARTICLES-START-->  and  <!--ARTICLES-END-->  (same markup as before),
and it updates sitemap.xml.

What it does when you run it (GitHub runs it for you automatically, see update-site.yml):
  * a NEW article-<category>-<name>.html  -> a new row is added to its category on the home page
  * existing rows keep their short description; their title follows the article's <h1>
  * sitemap.xml gets the new URL, and each article's <lastmod> follows its dateModified
Category = 2nd word of the file name: kitchen, closet, bathroom, travel (a new word creates a new section).

Run manually (optional):   python3 update_site.py
Keep old row titles:       python3 update_site.py --keep-titles
"""
import re, glob, os, sys, datetime, html

BASE = "https://tidynook.github.io/"
LABELS = {"kitchen": "KITCHEN", "closet": "CLOSET &amp; SMALL SPACE",
          "bathroom": "BATHROOM", "travel": "TRAVEL"}
KEEP_TITLES = "--keep-titles" in sys.argv
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def lastmod(s):
    m = re.search(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})"', s)
    if m: return m.group(1)
    m = re.search(r'Updated (\w+) (\d{4})', s)
    if m:
        try: return datetime.datetime.strptime(m.group(1)+" "+m.group(2), "%B %Y").strftime("%Y-%m-01")
        except ValueError: pass
    return datetime.date.today().isoformat()

# ---------- read articles ----------
arts = {}
for f in sorted(glob.glob("article-*.html")):
    s = open(f, encoding="utf-8").read()
    h1 = re.search(r"<h1>(.*?)</h1>", s)
    d = re.search(r'name="description" content="(.*?)"', s)
    if not (h1 and d):
        print("SKIPPED (no <h1> or meta description):", f); continue
    slug = f[:-5]
    arts[slug] = dict(cat=slug.split("-")[1], title=h1.group(1), desc=d.group(1), mod=lastmod(s))

# ---------- home page ----------
if os.path.exists("index.html"):
    idx = open("index.html", encoding="utf-8").read()
    a, b = "<!--ARTICLES-START-->", "<!--ARTICLES-END-->"
    if a in idx and b in idx:
        head, rest = idx.split(a, 1)
        block, tail = rest.split(b, 1)
        row_re = re.compile(r'<div class="post-row">\s*<span class="cat">(.*?)</span>\s*'
                            r'<h2><a href="(.*?)">(.*?)</a></h2>\s*<p>(.*?)</p>\s*</div>', re.S)
        lists = []                      # [(id, [rows])]  keeps your order
        for m in re.finditer(r'<div class="post-list" id="([^"]+)">(.*?)(?=\n</div>)', block, re.S):
            rows = [dict(label=r[0], slug=r[1], title=r[2], blurb=r[3]) for r in row_re.findall(m.group(2))]
            lists.append([m.group(1), rows])
        ids = {l[0]: l[1] for l in lists}
        listed = {r["slug"] for l in lists for r in l[1]}
        added = []
        for slug, a_ in arts.items():
            if slug in listed: continue
            if a_["cat"] not in ids:
                ids[a_["cat"]] = []; lists.append([a_["cat"], ids[a_["cat"]]])
            ids[a_["cat"]].append(dict(label=LABELS.get(a_["cat"], a_["cat"].upper()),
                                       slug=slug, title=a_["title"], blurb=a_["desc"]))
            added.append(slug)
        if not KEEP_TITLES:
            for l in lists:
                for r in l[1]:
                    if r["slug"] in arts: r["title"] = arts[r["slug"]]["title"]
        out = []
        for lid, rows in lists:
            if not rows: continue
            body = "".join('  <div class="post-row">\n    <span class="cat">%s</span>\n    <h2><a href="%s">%s</a></h2>\n    <p>%s</p>\n  </div>\n'
                           % (r["label"], r["slug"], r["title"], r["blurb"]) for r in rows)
            out.append('<div class="post-list" id="%s">\n%s</div>\n' % (lid, body))
        new_block = "\n" + "\n".join(out)
        open("index.html", "w", encoding="utf-8").write(head + a + new_block + b + tail)
        print("index.html: %d rows, new articles added: %s" % (sum(len(l[1]) for l in lists), added or "none"))
    else:
        print("index.html: markers <!--ARTICLES-START--> / <!--ARTICLES-END--> not found - home page left untouched")

# ---------- sitemap ----------
if os.path.exists("sitemap.xml") and arts:
    sm = open("sitemap.xml", encoding="utf-8").read()
    for slug, a_ in arts.items():
        loc = BASE + slug
        pat = re.compile(r"(<url><loc>%s</loc><lastmod>)[^<]*(</lastmod></url>)" % re.escape(loc))
        if pat.search(sm):
            sm = pat.sub(lambda m: m.group(1) + a_["mod"] + m.group(2), sm)
        else:
            sm = sm.replace("</urlset>", "  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>" % (loc, a_["mod"]))
    newest = max(a_["mod"] for a_ in arts.values())
    sm = re.sub(r"(<url><loc>%s</loc><lastmod>)[^<]*(</lastmod></url>)" % re.escape(BASE),
                lambda m: m.group(1) + newest + m.group(2), sm, count=1)
    open("sitemap.xml", "w", encoding="utf-8").write(sm)
    print("sitemap.xml updated (%d article URLs)" % len(arts))
