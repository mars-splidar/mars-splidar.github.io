#!/usr/bin/env python3
"""Fetch a page, resolve every same-origin reference it makes, report statuses.

Stage 1.5 check W13 — zero 404s on the live `/` and `/demos/`. Written to be
run against PRODUCTION, not just localhost: GitHub Pages serves from a
case-sensitive filesystem and a local one may not be, so an `Assets/` vs
`assets/` slip only shows up here.

    python check_links.py https://mars-splidar.github.io/ / /demos/

Deliberately ignores `data-src` / `data-poster`: those are the stage 1.5 media
gate's deferred URLs, which by design point at files that do not exist yet and
are never requested by the browser.
"""
import html, re, sys, urllib.error, urllib.parse, urllib.request

TAG = re.compile(r"<(\w+)((?:\s+[-\w:]+(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+))?)*)\s*/?>")
ATTR = re.compile(r"([-\w:]+)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)")
URL_META = {"og:image", "twitter:image", "citation_pdf_url", "og:url"}


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
        if tag == "source" and a.get("src"):
            yield a["src"]
        if tag in ("img", "source") and a.get("srcset"):
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
    pages = sys.argv[2:] or ["/"]
    bad = 0
    for page in pages:
        page_url = urllib.parse.urljoin(base, page.lstrip("/"))
        req = urllib.request.Request(
            page_url, headers={"User-Agent": "mars-linkcheck"})
        with urllib.request.urlopen(req, timeout=60) as r:
            status, body = r.status, r.read().decode("utf-8", "replace")
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

        # The hero buttons, the lightbox and the closing links are built at
        # runtime from js/site.config.js, so their URLs never appear in the
        # HTML. They are also the ones most exposed to a case-sensitivity
        # slip, so pull them out of the config and check them too.
        if page.rstrip("/") in ("", "/"):
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
                if pat in body:
                    bad += 1
                    print(f"  ** SERVED HTML CONTAINS {pat!r}")

    print(f"\n{'FAIL' if bad else 'PASS'} — {bad} broken reference(s)")
    return 1 if bad else 0


sys.exit(main())
