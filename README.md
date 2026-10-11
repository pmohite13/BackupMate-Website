# BackupMate website

The public site for BackupMate: `https://backupmate.buzzneuron.com`.

It is static HTML. Pages are written in `src/`, built by `build.py` into `public/`,
and `public/` is committed, so the host only serves files. There is nothing to
install beyond the Python already on the machine.

## Layout

| Path | What it is |
| --- | --- |
| `site.json` | **Every fact the site states**: prices, support address, refund period, legal name. Edit here, never in a page. |
| `src/layout.html` | The header and footer every page shares |
| `src/pages/` | One file per page: a few `key: value` lines, `---`, then HTML |
| `src/assets/` | The stylesheet and icon. No scripts, no fonts, nothing loaded from elsewhere |
| `build.py` | `src/` + `site.json` → `public/` |
| `release.py` | Records a release: version, checksums, download links |
| `preview.py` | Serves `public/` at `http://localhost:8080` the way the real host will |
| `public/` | The built site. **Generated: do not edit by hand** |

## Everyday use

```
python build.py        # build, warning about anything missing
python preview.py      # look at it
python build.py --strict   # before publishing: refuses to build with gaps
```

`--strict` deletes `public/` when it fails, deliberately, so that a draft with
"[legal name to be confirmed]" on its Terms page cannot be deployed by mistake.

## Before the site goes live

`site.json` has values that only the owner can supply. Until they are filled in,
`build.py --strict` fails and the pages show an obvious gap.

- `legal_name`, `legal_address`, `governing_city`, `grievance_officer`: empty.
- `support_hours`, `support_response`: suggestions marked `CONFIRM`. Remove the
  word once agreed; they are promises to customers.
- No release recorded, so the download page offers nothing yet.

The legal pages (`src/pages/legal/`) are drafts written to be clear and fair.
**They have not been reviewed by a lawyer.** Have that done before taking money.

When Paddle is added for sales outside India, its terms require the site to say
that Paddle is the merchant of record for those sales; add that to the terms of
sale and the refund policy at that point.

## Hosting (Cloudflare Pages)

1. In Cloudflare: Workers & Pages → Create → Pages → Connect to Git → this
   repository.
2. Build command: *(leave empty)*. Build output directory: `public`.
3. Production branch: `main`.
4. Custom domains → add `backupmate.buzzneuron.com`.

Cloudflare Pages serves `pricing.html` at `/pricing`, which is how every link on
the site is written, and serves `404.html` for anything missing.

**The installers do not go in this repository.** Each is larger than Cloudflare
Pages' 25 MB per-file limit. Put them in a Cloudflare R2 bucket (free at this
size, no download charges) with a custom domain such as
`downloads.buzzneuron.com`, in a folder per version.

## Publishing a release

The order matters. Every installed BackupMate server reads
`https://backupmate.buzzneuron.com/version.json` once a day and, when the
version there is newer than its own, sends its administrator to `/download`.
**That address is compiled into every installed copy and must keep working.**

1. Build the two MSIs in the product repository.
2. Upload them to the downloads bucket as
   `<version>/BackupMate-<version>.msi` and
   `<version>/BackupMateServer-<version>.msi`.
3. Record the release, against the same files you uploaded:

   ```
   python release.py 0.4.11 --client C:\BackupMate\dist\BackupMate.msi --server C:\BackupMate\dist\BackupMateServer.msi --base-url https://downloads.buzzneuron.com/0.4.11
   ```

   Add `--signed` once the installers carry a code-signing signature; the
   download page then drops its SmartScreen warning.
4. `python build.py --strict`, then `python preview.py` and **click both download
   links** to prove they work.
5. Commit and merge to `main`. The site, the checksums and `version.json` go live
   together.

To withdraw a release, record the previous one again and publish; servers stop
announcing the withdrawn version within a day.

## Changing a price

Edit `plans` in `site.json`, build, commit. The home page, the pricing page and
anything else that quotes it change together.
