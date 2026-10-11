#!/usr/bin/env python3
"""Record a release in site.json: version, checksums, sizes and download links.

    python release.py 0.4.11 ^
        --client C:\\BackupMate\\dist\\BackupMate.msi ^
        --server C:\\BackupMate\\dist\\BackupMateServer.msi ^
        --base-url https://backupmate-downloads.buzzneuron.com/0.4.11

Then `python build.py --strict` and commit.

The installers themselves are NOT kept in this repository or served by the
website host: each is over the 25 MB per-file limit of Cloudflare Pages, and a
git repository is the wrong place for binaries. Upload them to wherever
--base-url points first.

ORDER MATTERS. Publishing this site updates version.json, and every installed
server reads that within a day and sends its administrator to the download
page. Upload the installers, check the links work, and only then publish.

The checksums are computed here from the files you name, so what the download
page prints is a statement about exactly the files you uploaded -- provided they
are the same files. Upload first, then run this against the same copies.
"""
import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def describe(path, base_url, name):
    data = Path(path).read_bytes()
    return {
        "url": f"{base_url.rstrip('/')}/{name}",
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_mb": f"{len(data) / 1_048_576:.1f}",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("--client", required=True, help="path to BackupMate.msi")
    ap.add_argument("--server", required=True, help="path to BackupMateServer.msi")
    ap.add_argument("--base-url", required=True, help="https folder the two installers are uploaded to")
    ap.add_argument("--signed", action="store_true", help="the installers carry a code-signing signature")
    args = ap.parse_args()

    if not re.fullmatch(r"\d{1,5}(\.\d{1,5}){1,3}", args.version):
        sys.exit(f"{args.version!r} is not a version number (expected something like 0.4.11)")
    if not args.base_url.startswith("https://"):
        sys.exit("--base-url must be https")

    path = ROOT / "site.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["release"] = {
        "_comment": "Written by release.py. Do not edit by hand.",
        "version": args.version,
        "date": datetime.date.today().isoformat(),
        "signed": args.signed,
        # Named with the version, so a download says what it is and an old link
        # can never silently start serving a different file.
        "client": describe(args.client, args.base_url, f"BackupMate-{args.version}.msi"),
        "server": describe(args.server, args.base_url, f"BackupMateServer-{args.version}.msi"),
    }
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"recorded {args.version}. Upload the installers as:")
    for part in ("client", "server"):
        print(f"  {cfg['release'][part]['url']}")
    print("then: python build.py --strict")


if __name__ == "__main__":
    main()
