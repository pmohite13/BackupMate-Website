#!/usr/bin/env python3
"""Build the BackupMate website: src/ + site.json -> public/.

Why a script at all, for a site this small: sixteen pages share one header, one
footer and a handful of facts (prices, the support address, the refund period).
Kept by hand, the facts drift -- the pricing page says 14 days and the refund
policy says 30 -- and on a site whose legal pages are read by payment providers
before they approve an account, that is not a cosmetic problem.

Why this script and not a site generator: it needs nothing but the Python that
is already installed. There is no node_modules, no lock file, and nothing to
update. The output in public/ is committed, so the host serves files and runs
no build of its own.

    python build.py            build; warn about facts that are missing
    python build.py --strict   refuse to build while any fact is missing or
                               unconfirmed. Run this before publishing.

A page is a file under src/pages/. It starts with a few "key: value" lines, then
a line of three dashes, then HTML. {{name}} is replaced from site.json (and from
the page's own keys); {{#plans}}...{{/plans}} repeats for each plan.
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "src", ROOT / "public"

# Facts only the owner knows. An empty one is shown on the page as an obvious
# gap rather than left out, so that a draft cannot be mistaken for finished.
REQUIRED = ["legal_name", "legal_address", "governing_city", "support_email", "support_response"]


def load_config():
    cfg = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    problems = []
    for key in REQUIRED:
        value = str(cfg.get(key, "")).strip()
        if not value:
            problems.append(f"{key} is empty")
            cfg[key] = f"[{key.replace('_', ' ')} to be confirmed]"
        elif value.startswith("CONFIRM"):
            problems.append(f"{key} is a suggestion that has not been confirmed: {value[7:].strip()}")
            cfg[key] = value[7:].strip()
    return cfg, problems


def flatten(cfg):
    """site.json as flat {{names}}: release.client.url -> release_client_url."""
    out = {}

    def walk(prefix, value):
        if isinstance(value, dict):
            for k, v in value.items():
                if not k.startswith("_"):
                    walk(f"{prefix}{k}_", v)
        elif not isinstance(value, list):
            out[prefix[:-1]] = "yes" if value is True else "" if value is False else str(value)

    walk("", cfg)
    return out


def render(text, values, cfg, where):
    # {{#plans}} ... {{/plans}}
    def repeat(match):
        return "".join(render(match.group(1), {**values, **plan}, cfg, where) for plan in cfg["plans"])
    text = re.sub(r"\{\{#plans\}\}(.*?)\{\{/plans\}\}", repeat, text, flags=re.S)

    # {{?name}} ... {{/name}} keeps its contents when name is set;
    # {{^name}} ... {{/name}} when it is not.
    def conditional(match):
        present = bool(values.get(match.group(2), ""))
        return match.group(3) if present == (match.group(1) == "?") else ""
    for _ in range(3):  # a few passes, so conditionals may nest
        text = re.sub(r"\{\{([?^])(\w+)\}\}(.*?)\{\{/\2\}\}", conditional, text, flags=re.S)

    def value(match):
        name = match.group(1)
        if name not in values:
            sys.exit(f"{where}: {{{{{name}}}}} is not defined in site.json or the page")
        return values[name]
    return re.sub(r"\{\{(\w+)\}\}", value, text)


def read_page(path):
    head, _, body = path.read_text(encoding="utf-8").partition("\n---\n")
    meta = dict(line.split(":", 1) for line in head.splitlines() if ":" in line)
    return {k.strip(): v.strip() for k, v in meta.items()}, body


def main():
    strict = "--strict" in sys.argv
    cfg, problems = load_config()
    notes = []
    base = flatten(cfg)
    base["year"] = cfg["release"].get("date", "")[:4] or "2026"
    layout = (SRC / "layout.html").read_text(encoding="utf-8")

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC / "assets", OUT / "assets")

    pages = sorted((SRC / "pages").rglob("*.html"))
    for path in pages:
        rel = path.relative_to(SRC / "pages")
        meta, body = read_page(path)
        for need in ("title", "description"):
            if need not in meta:
                sys.exit(f"{rel}: missing '{need}:' line")
        url = "/" + rel.with_suffix("").as_posix()
        url = "/" if url == "/index" else url[:-6] + "/" if url.endswith("/index") else url
        values = {**base, **meta, "path": url,
                  "title_html": html.escape(meta["title"]),
                  "description_html": html.escape(meta["description"], quote=True)}
        # Which top-level section this page belongs to, for the highlighted link.
        section = url.strip("/").split("/")[0] or "home"
        for name in ("home", "features", "pricing", "download", "docs", "security", "contact"):
            values[f"on_{name}"] = ' aria-current="page"' if section == name else ""
        content = render(body, values, cfg, rel)
        page = render(layout, {**values, "content": content}, cfg, rel)
        target = OUT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8", newline="\n")

    # What installed servers read once a day to learn of a newer version. It
    # must hold exactly a version number -- see docs/25 in the product repo.
    version = cfg["release"]["version"]
    if version:
        if not re.fullmatch(r"\d{1,5}(\.\d{1,5}){1,3}", version):
            sys.exit(f"release version {version!r} is not a version number")
        (OUT / "version.json").write_text(json.dumps({"version": version}) + "\n", encoding="utf-8", newline="\n")
    else:
        # Not a reason to refuse: the site can go live before the installers do
        # (a payment provider reviews the pages, not the downloads), and the
        # download page says plainly that they are on their way.
        notes.append("no release recorded: the download page offers nothing and version.json is not "
                     "published. Run release.py when the installers are uploaded.")

    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {cfg['site_url']}/sitemap.xml\n",
                                    encoding="utf-8", newline="\n")
    urls = []
    for path in pages:
        rel = path.relative_to(SRC / "pages").with_suffix("").as_posix()
        if rel == "404":
            continue
        rel = "" if rel == "index" else rel[:-5] if rel.endswith("/index") else rel
        urls.append(f"  <url><loc>{cfg['site_url']}/{rel}</loc></url>")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8", newline="\n")

    print(f"built {len(pages)} pages into {OUT}")
    for n in notes:
        print(f"  note: {n}")
    for p in problems:
        print(f"  {'ERROR' if strict else 'warning'}: {p}")
    if strict and problems:
        shutil.rmtree(OUT)
        sys.exit("not published: fix the above in site.json (public/ was removed so it cannot be deployed by mistake)")


if __name__ == "__main__":
    main()
