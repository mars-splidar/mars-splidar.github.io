#!/usr/bin/env python3
"""Fetch a page, resolve every same-origin reference it makes, report statuses.

Stage 1.5 check W13 — zero 404s on the live `/` and `/demos/`. Written to be
run against PRODUCTION, not just localhost: GitHub Pages serves from a
case-sensitive filesystem and a local one may not be, so an `Assets/` vs
`assets/` slip only shows up here.

    python check_links.py https://mars-splidar.github.io/ / /demos/

`data-src` / `data-poster` — CHANGED IN STAGE 07. Those are the media gate's
deferred URLs. They used to be skipped wholesale, because before stage 05 they
pointed at files that did not exist yet. That blind spot is exactly where
stage 06 section 9's silent failure lives: a basename declared in
`mediaAvailable` whose file 404s renders as a blank white frame, and no
page load reveals it, because a cold load requests nothing from
assets/media/. So now every deferred URL whose basename IS declared in
`mediaAvailable` is resolved against the PAGE that carries it (that matters
from /details/, where they read `../assets/media/...`) and HEAD-checked like
any other reference. Undeclared ones are still skipped, and listed.

With no page arguments it checks both public pages, `/` and `/details/`
(stage 07). /demos/ is still checkable by naming it.
"""
import html, re, sys, urllib.error, urllib.parse, urllib.request

TAG = re.compile(r"<(\w+)((?:\s+[-\w:]+(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+))?)*)\s*/?>")
ATTR = re.compile(r"([-\w:]+)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)")
URL_META = {"og:image", "twitter:image", "citation_pdf_url", "og:url"}

# Files `/` depends on that no HTML attribute names, HEAD-checked BY PATH
# (stage 09). The teaser's sources are attributes too, but they are the main
# page's LCP and its one autoplay, so they are named here as well; and
# demo_count.svg ships INLINED in index.html, so nothing on the page
# references the committed file that tools/build_demo_count.py writes.
BY_PATH_MAIN = [
    "assets/media/anim_hero_cubes.jpg",
    "assets/media/anim_hero_cubes.webm",
    "assets/media/anim_hero_cubes.mp4",
    "assets/media/anim_hero_cubes_960.jpg",       # stage 09b phone variant
    "assets/media/anim_hero_cubes_960.webm",
    "assets/media/anim_hero_cubes_960.mp4",
    "assets/img/demo_count.svg",
]


def attrs(blob):
    out = {}
    for k, v in ATTR.findall(blob):
        out[k.lower()] = html.unescape(v.strip("\"'"))
    return out


def refs_in(body):
    """Yield every URL the browser would actually request or navigate to."""
    for m in TAG.finditer(body):
        tag, a = m.group(1).lower(), attrs(m.group(2))
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key in URL_META and a.get("content"):
                yield a["content"]
            continue
        if tag == "link" and a.get("href"):
            yield a["href"]
        if tag in ("script", "img", "video", "audio", "iframe", "embed") \
                and a.get("src"):
            yield a["src"]
        if tag in ("source", "track") and a.get("src"):
            yield a["src"]
        if tag in ("img", "source") and a.get("srcset"):
            # v2.1-A: a data: URI candidate carries its own comma
            # ("data:image/gif;base64,..."), so it is taken whole and skipped
            # (nothing to fetch) before the list is split on commas.
            if a["srcset"].strip().startswith("data:"):
                continue
            for part in a["srcset"].split(","):
                if part.strip():
                    yield part.strip().split()[0]
        if tag in ("img", "video") and a.get("poster"):
            yield a["poster"]
        if tag == "a" and a.get("href"):
            yield a["href"]


def head(url):
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(
            url, method=method, headers={"User-Agent": "mars-linkcheck"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.headers.get("Content-Length", "?")
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405):
                continue
            return e.code, "-"
        except Exception as e:
            return f"ERR {e}", "-"
    return "ERR", "-"


def main():
    base = sys.argv[1].rstrip("/") + "/"
    pages = sys.argv[2:] or ["/", "/details/"]
    bad = 0
    try:
        creq = urllib.request.Request(urllib.parse.urljoin(base, "js/site.config.js"),
                                      headers={"User-Agent": "mars-linkcheck"})
        with urllib.request.urlopen(creq, timeout=60) as r:
            cfg_src = r.read().decode("utf-8", "replace")
        m = re.search(r"mediaAvailable:\s*\[(.*?)\]", cfg_src, re.S)
        available = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()
    except Exception as e:
        print(f"  ** could not read mediaAvailable from site.config.js: {e}")
        available, bad = set(), bad + 1
    for page in pages:
        page_url = urllib.parse.urljoin(base, page.lstrip("/"))
        req = urllib.request.Request(
            page_url, headers={"User-Agent": "mars-linkcheck"})
        with urllib.request.urlopen(req, timeout=60) as r:
            status, body = r.status, r.read().decode("utf-8", "replace")
        # Markup comments are not requested by anything. Stage 07 parks the
        # exact <video> stage 09 will add to the teaser inside a comment, and
        # without this its not-yet-existing sources read as three 404s.
        # The production pattern check below still reads `raw`, comments
        # included, exactly as it did before stage 07.
        raw = body
        body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
        print(f"\n=== {page_url}  [{status}] ===")

        seen, internal, external = set(), [], []
        for u in refs_in(body):
            u = u.strip()
            if not u or u.startswith(("#", "data:", "mailto:", "javascript:")):
                continue
            full = urllib.parse.urljoin(page_url, u)
            if full in seen:
                continue
            seen.add(full)
            (internal if full.startswith(base) else external).append(full)

        for full in sorted(internal):
            code, size = head(full)
            rel = full[len(base) - 1:]
            if code != 200:
                bad += 1
                print(f"  ** {code:<5} {rel}")
            else:
                print(f"  {code:<7} {rel}  ({size} B)")
        for full in sorted(external):
            print(f"  (ext)   {full}")

        # Deferred media URLs, by path (stage 07 — see the docstring).
        deferred = sorted(set(html.unescape(v) for v in re.findall(
            r'\bdata-(?:src|poster)(?:-[a-z]+)?\s*=\s*["\']([^"\']+)["\']',
            body)))   # data-src-refl / data-src-depth: Demo 3 (stage 09)
        if deferred:
            print("  -- deferred media (data-src / data-poster), by path --")
        for u in deferred:
            stem = u.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            full = urllib.parse.urljoin(page_url, u)
            if "assets/media/" in u and stem not in available:
                print(f"  (undeclared, skipped) {u}")
                continue
            code, size = head(full)
            rel = full[len(base) - 1:] if full.startswith(base) else full
            if code != 200:
                bad += 1
                print(f"  ** {code:<5} {rel}   <- declared in mediaAvailable")
            else:
                print(f"  {code:<7} {rel}  ({size} B)")

        # The hero buttons, the lightbox and the closing links are built at
        # runtime from js/site.config.js, so their URLs never appear in the
        # HTML. They are also the ones most exposed to a case-sensitivity
        # slip, so pull them out of the config and check them too.
        # Resolving them against the SITE BASE (not the page) is correct since
        # stage 07: site.config.js itself resolves them against the site root
        # at runtime, so /details/ renders the same absolute URLs as `/`.
        if page.rstrip("/") in ("", "/"):
            print("  -- by path (stage 09) --")
            for u in BY_PATH_MAIN:
                code, size = head(urllib.parse.urljoin(base, u))
                if code != 200:
                    bad += 1
                    print(f"  ** {code:<5} {u}")
                else:
                    print(f"  {code:<7} {u}  ({size} B)")
            cfg_url = urllib.parse.urljoin(page_url, "js/site.config.js")
            try:
                creq = urllib.request.Request(
                    cfg_url, headers={"User-Agent": "mars-linkcheck"})
                with urllib.request.urlopen(creq, timeout=60) as r:
                    cfg = r.read().decode("utf-8", "replace")
            except Exception as e:
                cfg = ""
                print(f"  ** could not read site.config.js: {e}")
                bad += 1
            print("  -- URLs injected from js/site.config.js --")
            for u in sorted(set(re.findall(
                    r'"((?:assets|demos)/[^"]+)"', cfg))):
                full = urllib.parse.urljoin(base, u)
                code, size = head(full)
                if code != 200:
                    bad += 1
                    print(f"  ** {code:<5} {u}")
                else:
                    print(f"  {code:<7} {u}  ({size} B)")

        ids = set(re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', body))
        for a in sorted(set(re.findall(r'href\s*=\s*["\']#([^"\']+)["\']',
                                       body))):
            if a not in ids:
                bad += 1
                print(f"  ** ORPHAN ANCHOR  #{a}")

        if page_url.startswith("http") and "mars-splidar" in page_url:
            for pat in ("mars-todo", "under construction"):
                if pat in raw:
                    bad += 1
                    print(f"  ** SERVED HTML CONTAINS {pat!r}")

    print(f"\n{'FAIL' if bad else 'PASS'} — {bad} broken reference(s)")
    return 1 if bad else 0


sys.exit(main())
